#!/usr/bin/env python3
"""ONLY local OCR engines. No pip, no download, no network, no install."""
from __future__ import annotations
from pathlib import Path
from statistics import mean, median
import json, math, os, re, subprocess, sys, time, unicodedata

ROOT = Path(__file__).resolve().parents[1]
CASES = Path(os.environ.get("GTOCR_BENCH_CASES", str(ROOT / "benchmarks" / "cases")))
MODELS = ROOT / "models" / "latin"
OUT = Path(os.environ.get("GTOCR_BENCH_OUT", str(ROOT / "benchmarks")))
LABELS = json.loads((CASES / "truth.json").read_text(encoding="utf-8"))
IMAGES = sorted(CASES.glob("*.png"))

def normalize(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC",s).casefold().split())

def levenshtein(a: str, b: str) -> int:
    if len(a)<len(b): a,b=b,a
    last=list(range(len(b)+1))
    for i, ca in enumerate(a,1):
        row=[i]
        for j, cb in enumerate(b,1):
            row.append(min(row[-1]+1,last[j]+1,last[j-1]+(ca!=cb)))
        last=row
    return last[-1]

def parse_result(name, pass_number, texts, ms):
    return {"name":name, "pass":pass_number,
            "texts":[str(t) for t in (texts or [])], "ms":round(float(ms),3)}

def benchmark_game(hybrid=False, v6=False, padding=0):
    executable = ROOT/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
    model_dir=ROOT/"models"/("latin-v6-local" if v6 else "latin-v6-hybrid") if (hybrid or v6) else MODELS
    command=["dotnet",str(executable),"suite",str(CASES),str(model_dir),"2",str(padding)]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=180,check=True)
    records=[]
    for line in proc.stdout.splitlines():
        if line.startswith("BENCHRESULT\t"):
            records.append(json.loads(line.split("\t",1)[1]))
    if len(records)!=len(IMAGES)*2:
        raise ValueError(f"Expected {len(IMAGES)*2} results, got {len(records)}:\n{proc.stdout[:1000]}")
    return records

def benchmark_rapid(matched: bool):
    # Force EXPLICIT local model paths: no implicit downloader is reachable.
    import rapidocr
    from rapidocr import RapidOCR
    pkg=Path(rapidocr.__file__).resolve().parent
    cfg={"Global.use_cls":False, "Global.log_level":"error"}
    if matched:
        cfg.update({"Det.model_path":str(MODELS/"detector.onnx"),
            "Rec.model_path":str(MODELS/"recognizer.onnx"),
            "Rec.rec_keys_path":str(MODELS/"charset.txt")})
    else:
        cfg.update({"Det.model_path":str(pkg/"models/PP-OCRv6_det_small.onnx"),
            "Rec.model_path":str(pkg/"models/PP-OCRv6_rec_small.onnx")})
    for name,key in [(cfg["Det.model_path"],"det"),(cfg["Rec.model_path"],"rec")]:
        if not Path(name).is_file():
            raise FileNotFoundError(f"LOCAL {key} unavailable; skipping with NO download: {name}")
    model=RapidOCR(params=cfg)
    model(str(IMAGES[0])) # warmup
    result=[]
    for run in range(2):
        for image in IMAGES:
            start=time.perf_counter()
            prediction=model(str(image),use_cls=False)
            elapsed=(time.perf_counter()-start)*1000
            result.append(parse_result(image.name,run,prediction.txts,elapsed))
    return result

def benchmark_tesseract():
    # CLI start-up is included. All traineddata languages are already installed.
    command=["tesseract","-l","eng+turk","--psm","11"]
    subprocess.run(["tesseract",str(IMAGES[0]),"stdout","-l","eng+turk","--psm","11"],
        capture_output=True,check=True,timeout=20)
    result=[]
    for run in range(2):
        for image in IMAGES:
            start=time.perf_counter()
            proc=subprocess.run(["tesseract",str(image),"stdout","-l","eng+turk","--psm","11"],
                capture_output=True,text=True,check=True,timeout=20)
            elapsed=(time.perf_counter()-start)*1000
            lines=[line.strip() for line in proc.stdout.splitlines() if line.strip()]
            result.append(parse_result(image.name,run,lines,elapsed))
    return result

def metrics(records):
    final={}
    all_ms=[]
    expected_chars=0; distance_sum=0; exact_lines=0; expected_lines=0
    for name, ground in LABELS.items():
        subset=[r for r in records if r["name"]==name]
        if not subset: raise ValueError(f"Missing {name}")
        all_ms.extend(r["ms"] for r in subset)
        prediction=subset[0]["texts"]
        # Normalize/casefold to ignore capitalization but retain accents and punctuation.
        truth=normalize(" ".join(ground))
        guess=normalize(" ".join(prediction))
        distance=levenshtein(truth,guess)
        expected_chars+=len(truth)
        distance_sum+=distance
        true_norm=[normalize(x) for x in ground]
        pred_norm=[normalize(x) for x in prediction]
        for line in true_norm:
            if line in pred_norm:
                pred_norm.remove(line)
                exact_lines+=1
        expected_lines+=len(ground)
        final[name]={"truth":ground,"pred":prediction,"cer":round(distance/max(1,len(truth)),4),
                     "mean_ms":round(mean(r["ms"] for r in subset),1)}
    return {"char_accuracy":round(100*max(0,1-distance_sum/max(1,expected_chars)),2),
            "exact_line_recall":round(100*exact_lines/max(1,expected_lines),2),
            "exact_lines":exact_lines,
            "total_lines":expected_lines,
            "mean_ms":round(mean(all_ms),1),
            "median_ms":round(median(all_ms),1),
            "p95_ms":round(sorted(all_ms)[math.ceil(len(all_ms)*.95)-1],1),
            "per_case":final}

def aggregate():
    definitions={
       "game":"GameTranslatorOCR (PP-OCRv5 Latin, C#)",
       "game_hybrid":"GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#)",
       "game_v6":"GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#)",
       "game_tuned":"GameTranslatorOCR (v5 modeller + 6px crop, C#)",
       "game_hybrid_tuned":"GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#)",
       "rapid_matched":"RapidOCR (aynı PP-OCRv5 Latin modelleri)",
       "rapid_default":"RapidOCR (hazır PP-OCRv6 modelleri)",
       "tesseract":"Tesseract 5.5.3 (eng+turk, PSM 11)"
    }
    results={}
    for kind,title in definitions.items():
        file=OUT/f"results_{kind}.json"
        if not file.exists(): continue
        d=json.loads(file.read_text(encoding="utf-8"))
        results[kind]=dict(title=title,metrics=metrics(d["records"]))
    if not results: raise ValueError("No benchmark results")
    fastest=min(x["metrics"]["mean_ms"] for x in results.values())
    for row in results.values():
        m=row["metrics"]
        speed=min(100,100*fastest/m["mean_ms"])
        m["speed_score"]=round(speed,1)
        m["total_score"]=round(.70*m["char_accuracy"]+.20*m["exact_line_recall"]+.10*speed,1)
    summary=sorted(results.items(),key=lambda x:x[1]["metrics"]["total_score"],reverse=True)
    lines=["# Yerel OCR Karşılaştırması (ek indirme yapılmadan)",
           "",
           "## Test kapsamı",
           "- Fedora Linux, **mevcut yüklü motorlar ve mevcut yerel modeller**; internetten indirme/kurulum yapılmadı.",
           f"- **{len(LABELS)} sentetik oyun-arayüzü görseli, {sum(map(len,LABELS.values()))} gerçek metin satırı**. Gerçek oyun görüntüsü değildir.",
           "- Tüm motorlarda CPU, aynı görüntüler. İlk model ısınması hariç, her görüntü için 2 koşum.",
           "- Sadece GameTranslatorOCR v5 original/tuned ile RapidOCR matched aynı PP-OCRv5 detector + Latin recognizer modellerini kullanır; hibrit sürüm v6 tanıyıcı kullanır, dolayısıyla model eşitliği yoktur.",
           "- RapidOCR default zaten kurulu PP-OCRv6 det/rec kullanır; model versiyonu farklıdır.",
           "- Tesseract komut satırı başlatma maliyeti ölçüme dahil, diğerlerinde model bir kere yüklenmiştir. Hız eşit yöntemle ölçülmüş sayılamaz.",
           "- Puan = **%70 karakter doğruluğu + %20 tamamen doğru satır oranı + %10 en hızlı motora göre hız puanı**.",
           "- Büyük/küçük harf farkı göz ardı edilir; Türkçe harfler ve noktalama değerlendirmeye dahildir.",
           "- Az sayıda sentetik örnekten genellenebilir OCR yüzdesi veya üstünlük çıkarılamaz.",
           "",
           "## Skor tablosu",
           "",
           "| Sıra | Motor | Karakter doğruluğu | Tam satır | Ortalama CPU | p95 | Skor |",
           "|---:|---|---:|---:|---:|---:|---:|"]
    for i,(kind,entry) in enumerate(summary,1):
        m=entry["metrics"]
        lines.append(f'| {i} | {entry["title"]} | %{m["char_accuracy"]:.2f} | {m["exact_lines"]}/{m["total_lines"]} | {m["mean_ms"]:.1f} ms | {m["p95_ms"]:.1f} ms | **{m["total_score"]:.1f}/100** |')
    lines+=["","## Görsel bazında hatalar", ""]
    lines+=["| Görsel | "+ " | ".join(x[1]["title"].split(" (")[0]+ " ("+x[0]+")" for x in summary)+" |",
            "|---|"+"---:|"*len(summary)]
    for name in LABELS:
        row=[name]
        for key,_ in summary:
            case=results[key]["metrics"]["per_case"][name]
            row.append(f'%{100*(1-case["cer"]):.0f}')
        lines.append("| "+" | ".join(row)+" |")
    lines+=["","## Okunan metinler (her motorun ilk koşumu)", ""]
    for name in LABELS:
        lines.append(f'### {name}')
        lines.append(f'- Doğrusu: {LABELS[name]}')
        for kind,entry in summary:
            p=entry["metrics"]["per_case"][name]["pred"]
            lines.append(f'- {entry["title"]}: {p}')
    lines+=["","## Kısıtlar",
            "- Tesseract'ın PSM 11 modu tek seçilmiş ayardır, farklı PSM ile sonuçları değişebilir.",
            "- Bu skor overlay, frame tracking, GPU desteği, dil çeşitliliği, paket boyutu veya lisansı puanlamıyor.",
            "- Rakip motorları indirmemek için EasyOCR/PaddleOCR kurulmadı, dolayısıyla ölçüm skoru yok.",
            "- Skor bir **yerel sentetik test** skorudur; GameTranslatorOCR'a otomatik liderlik anlamına gelmez.",
           ""]
    (OUT/"RESULTS.md").write_text("\n".join(lines),encoding="utf-8")
    (OUT/"SUMMARY.json").write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding="utf-8")
    print("\n".join(lines[:22]))

if __name__=="__main__":
    mode=sys.argv[1]
    # Do not permit accidental model download: all model paths are local.
    os.environ["HF_HUB_OFFLINE"]="1"
    os.environ["TRANSFORMERS_OFFLINE"]="1"
    if mode=="aggregate":
        aggregate()
    else:
        if mode=="game": results=benchmark_game()
        elif mode=="game_hybrid": results=benchmark_game(hybrid=True)
        elif mode=="game_v6": results=benchmark_game(v6=True)
        elif mode=="game_tuned": results=benchmark_game(padding=6)
        elif mode=="game_hybrid_tuned": results=benchmark_game(hybrid=True,padding=6)
        elif mode=="rapid_matched": results=benchmark_rapid(True)
        elif mode=="rapid_default": results=benchmark_rapid(False)
        elif mode=="tesseract": results=benchmark_tesseract()
        else: raise SystemExit("Unknown mode: "+mode)
        file=OUT/f"results_{mode}.json"
        file.write_text(json.dumps({"engine":mode,"records":results},ensure_ascii=False,indent=2),
                        encoding="utf-8")
        print(mode, "records",len(results),"saved",file.name)
        m=metrics(results)
        print(f'accuracy={m["char_accuracy"]}% exact={m["exact_lines"]}/{m["total_lines"]} latency={m["mean_ms"]}ms p95={m["p95_ms"]}ms')
