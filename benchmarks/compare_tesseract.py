#!/usr/bin/env python3
"""Existing local Tesseract 5.5.3 vs GameTranslatorOCR; zero downloads."""
from __future__ import annotations
import ctypes, ctypes.util, json, math, os, re, resource, subprocess, sys, time, unicodedata
from collections import Counter
from pathlib import Path
from statistics import mean,median
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"benchmarks"/"tesseract_v55"
OUT.mkdir(exist_ok=True)
DLL=ROOT/"src"/"GameTranslatorOCR.Cli"/"bin"/"Release"/"net8.0"/"GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models"/"latin-v6-hybrid"
SETS={"development":ROOT/"benchmarks"/"cases","holdout":ROOT/"benchmarks"/"holdout_cases"}

def norm(x):
    return " ".join(unicodedata.normalize("NFKC",str(x)).replace("İ","i").casefold().split())

def edit(a,b):
    old=list(range(len(b)+1))
    for i,c in enumerate(a,1):
        row=[i]
        for j,d in enumerate(b,1):
            row.append(min(row[-1]+1,old[j]+1,old[j-1]+(c!=d)))
        old=row
    return old[-1]

def metrics(rows,truth):
    byname={}
    for item in rows:byname.setdefault(item["name"],[]).append(item)
    errors=chars=exact=gtcount=predcount=0
    times=[];cases=[]
    for name,ref in truth.items():
        records=byname.get(name)
        if not records:raise RuntimeError("missing image "+name)
        guessed=records[0]["texts"]
        gt=Counter(map(norm,ref));found=Counter(map(norm,guessed))
        matched=sum(min(n,found[x]) for x,n in gt.items())
        a=norm(" ".join(ref));b=norm(" ".join(guessed))
        distance=edit(a,b)
        errors+=distance;chars+=len(a)
        exact+=matched;gtcount+=len(ref);predcount+=len(guessed)
        times.extend(x["ms"] for x in records)
        cases.append({"name":name,"reference":ref,"predicted":guessed,
                      "matched_lines":matched,"total_lines":len(ref),"edit_distance":distance})
    precision=exact/predcount if predcount else 0
    recall=exact/gtcount if gtcount else 0
    times.sort()
    return {"char_accuracy_pct":round(100*max(0,1-errors/max(1,chars)),2),
            "char_error_pct":round(100*errors/max(1,chars),2),
            "exact_lines":exact,"reference_lines":gtcount,"predicted_lines":predcount,
            "line_precision_pct":round(100*precision,2),
            "line_recall_pct":round(100*recall,2),
            "line_f1_pct":round(200*precision*recall/(precision+recall),2) if precision+recall else 0,
            "mean_ms":round(mean(times),2),
            "median_ms":round(median(times),2),
            "p95_ms":round(times[math.ceil(.95*len(times))-1],2),
            "min_ms":round(times[0],2),"max_ms":round(times[-1],2),
            "per_image":cases}

class TesseractSession:
    def __init__(self,psm):
        lib=ctypes.util.find_library("tesseract")
        if not lib:raise RuntimeError("Installed libtesseract absent")
        self.t=ctypes.CDLL(lib)
        self.t.TessBaseAPICreate.restype=ctypes.c_void_p
        self.t.TessBaseAPIInit3.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p]
        self.t.TessBaseAPIInit3.restype=ctypes.c_int
        self.t.TessBaseAPISetPageSegMode.argtypes=[ctypes.c_void_p,ctypes.c_int]
        self.t.TessBaseAPISetImage.argtypes=[
            ctypes.c_void_p,ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int]
        self.t.TessBaseAPIGetUTF8Text.argtypes=[ctypes.c_void_p]
        self.t.TessBaseAPIGetUTF8Text.restype=ctypes.c_void_p
        self.t.TessDeleteText.argtypes=[ctypes.c_void_p]
        self.t.TessBaseAPIDelete.argtypes=[ctypes.c_void_p]
        self.api=self.t.TessBaseAPICreate()
        if not self.api:raise MemoryError("Tesseract alloc failure")
        if self.t.TessBaseAPIInit3(self.api,None,b"eng+turk"):
            self.t.TessBaseAPIDelete(self.api)
            self.api=None
            raise RuntimeError("Preinstalled English/Turkish Tesseract data could not load")
        self.t.TessBaseAPISetPageSegMode(self.api,psm)

    def __call__(self,rgb):
        width,height,bytestr=rgb
        pixels=(ctypes.c_ubyte*len(bytestr)).from_buffer_copy(bytestr)
        start=time.perf_counter()
        self.t.TessBaseAPISetImage(self.api,pixels,width,height,3,width*3)
        ptr=self.t.TessBaseAPIGetUTF8Text(self.api)
        elapsed=(time.perf_counter()-start)*1000
        if not ptr:raise RuntimeError("No Tesseract UTF8 text")
        try:txt=ctypes.string_at(ptr).decode("utf8","replace")
        finally:self.t.TessDeleteText(ptr)
        return [s.strip() for s in txt.splitlines() if s.strip()],elapsed

    def close(self):
        if self.api:
            self.t.TessBaseAPIDelete(self.api)
            self.api=None

def tesseract_warm(folder,psm):
    images=sorted(folder.glob("*.png"))
    rgb=[]
    for file in images:
        with Image.open(file) as img:
            converted=img.convert("RGB")
            rgb.append((file.name,(converted.width,converted.height,converted.tobytes())))
    session=TesseractSession(psm)
    rows=[]
    try:
        session(rgb[0][1])
        for passnum in range(2):
            for name,r in rgb:
                texts,ms=session(r)
                rows.append({"name":name,"pass":passnum,"texts":texts,"ms":ms})
    finally:session.close()
    return rows,round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1)

def tesseract_cli(folder):
    images=sorted(folder.glob("*.png"))
    subprocess.run(["tesseract",str(images[0]),"stdout","-l","eng+turk","--psm","11"],
                   check=True,capture_output=True,timeout=15)
    rows=[]
    for passnum in range(2):
        for file in images:
            start=time.perf_counter()
            p=subprocess.run(["tesseract",str(file),"stdout","-l","eng+turk","--psm","11"],
                check=True,capture_output=True,text=True,timeout=15)
            ms=(time.perf_counter()-start)*1000
            rows.append({"name":file.name,"pass":passnum,
                         "texts":[x.strip() for x in p.stdout.splitlines() if x.strip()],
                         "ms":ms})
    return rows

def game(folder,enhanced):
    cmd=["/usr/bin/time","-f","PEAK_RSS_KB=%M","dotnet",str(DLL),
         "suite",str(folder),str(MODEL),"2","6"]
    if enhanced:cmd.append("--enhanced")
    proc=subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=80)
    records=[]
    for line in proc.stdout.splitlines():
        if line.startswith("BENCHRESULT\t"):
            x=json.loads(line.split("\t",1)[1])
            records.append({"name":x["name"],"pass":x["pass"],
                            "texts":x["texts"],"ms":x["ms"]})
    target=2*len(list(folder.glob("*.png")))
    if len(records)!=target:raise RuntimeError(f"Expected {target} rows, got {len(records)}")
    m=re.search(r"PEAK_RSS_KB=(\d+)",proc.stderr)
    peak=round(int(m.group(1))/1024,1) if m else None
    return records,peak

def run(kind,dataset):
    folder=SETS[dataset]
    truth=json.loads((folder/"truth.json").read_text(encoding="utf8"))
    if kind=="game_default":records,peak=game(folder,False)
    elif kind=="game_enhanced":records,peak=game(folder,True)
    elif kind in ("tess_psm11","tess_psm6","tess_psm3"):
        records,peak=tesseract_warm(folder,int(kind.split("psm")[1]))
    elif kind=="tess_cli11":records=tesseract_cli(folder);peak=None
    else:raise ValueError(kind)
    stat=metrics(records,truth)
    result={"kind":kind,"dataset":dataset,"metrics":stat,
            "peak_process_rss_mib":peak,"records":records}
    (OUT/(dataset+"__"+kind+".json")).write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf8")
    print(f'{dataset:11s} {kind:15s} chars={stat["char_accuracy_pct"]:6.2f}% '+
        f'lines={stat["exact_lines"]:2d}/{stat["reference_lines"]} '+
        f'F1={stat["line_f1_pct"]:6.2f}% mean={stat["mean_ms"]:7.2f} ms '+
        f'p95={stat["p95_ms"]:7.2f} RSS={peak} MiB',flush=True)

def aggregate():
    entries=[]
    for dataset in SETS:
        for kind in ["game_default","game_enhanced","tess_psm11",
                     "tess_psm6","tess_psm3","tess_cli11"]:
            f=OUT/(dataset+"__"+kind+".json")
            if f.exists():entries.append(json.loads(f.read_text(encoding="utf8")))
    lines=["# GameTranslatorOCR vs Tesseract 5.5.3 — Fedora CPU benchmark",
           "",
           "16 Ekim 2026; kurulu modeller, sıfır indirme.",
           "11 sentetik görüntü/33 satır (ilk set), 10 bağımsız sentetik görüntü/30 satır (ikinci set). Görsel başına 2 koşum.",
           "GameTranslatorOCR: C# ONNX PP-OCRv5 detector + yerel PP-OCRv6 recognizer. Gelişmiş profil: --enhanced.",
           "Tesseract: kurulu eng+turk traineddata, libtesseract sıcak oturumlu PSM11/6/3 ve ayrı CLI denemesi.",
           "",
           "| Set | Motor | Karakter doğruluğu | Tam satır | Satır F1 | Ortalama | p95 | Tepe RSS |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    for e in entries:
        v=e["metrics"]
        rss=("--" if e["peak_process_rss_mib"] is None else str(e["peak_process_rss_mib"])+" MiB")
        lines.append(f'| {e["dataset"]} | {e["kind"]} | {v["char_accuracy_pct"]:.2f}% | '+
            f'{v["exact_lines"]}/{v["reference_lines"]} | {v["line_f1_pct"]:.2f}% | '+
            f'{v["mean_ms"]:.1f} ms | {v["p95_ms"]:.1f} ms | {rss} |')
    lines+=["",
        "## Nasıl ölçüldü?",
        "- Karakter doğruluğu: Unicode NFKC + büyük/küçük harf yok sayıldı; Tüm OCR çıktısı satır sırasına göre birleştirildi ve Levenshtein edit mesafesi hesaplandı. Ek çıktılar/yanlışlar cezalandırıldı.",
        "- Tam doğru satır: bir OCR sonuç satırı, bir referans satırıyla birebir eşleşti. Satır F1 fazladan satırları da cezalandırır.",
        "- Tesseract sıcak API: kurulu libtesseract tek kere başlatıldı, Pillow RGB conversion önceden yapıldı; SetImage+GetUTF8Text ölçüme dahil.",
        "- GameTranslatorOCR: model oturumu başlangıcı hariç, RecognizeAsync (PNG decode dahil) süreleri ölçüldü.",
        "- Tesseract CLI: her görüntüde ayrı proses başlar ve traineddata yeniden yüklenir; sıcak API ile eşdeğer hız sonucu değildir.",
        "- Bellek: GameTranslatorOCR .NET prosesi peak RSS; Tesseract sıcak oturumu Python+libtesseract prosesi peak RSS. Framework/buffer farkı vardır.",
        "- Tüm denemeler CPU'da ve sentetik veridedir. Gerçek oyun ekranında, Windows/GPU'da aynı sonuç garantisi yok.",
        "- Tesseract PSM11 sparse text, PSM6 block, PSM3 auto layout stratejileridir.",
        "","## Başarısız/göze çarpan örnekler"]
    for e in entries:
        m=e["metrics"]
        faults=[x for x in m["per_image"] if x["matched_lines"]<x["total_lines"]]
        lines.append("### "+e["dataset"]+" - "+e["kind"]+f" ({len(faults)} hata içeren görsel)")
        for item in faults:
            lines.append("- "+item["name"]+": gerçek "+repr(item["reference"])+"; okunan "+repr(item["predicted"]))
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    print("\n".join(lines[:28]))

if __name__=="__main__":
    os.environ["HF_HUB_OFFLINE"]="1"
    if sys.argv[1]=="aggregate":aggregate()
    else:run(sys.argv[1],sys.argv[2])
