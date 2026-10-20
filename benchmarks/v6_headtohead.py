#!/usr/bin/env python3
"""Local CPU OCR comparison; NO network, install or model downloads."""
from pathlib import Path
from collections import Counter
from statistics import mean,median
import unicodedata, json, math
root=Path(__file__).resolve().parents[1]
target=root/"benchmarks/v6_headtohead"
target.mkdir(exist_ok=True)
sets=[("original",root/"benchmarks/cases",root/"benchmarks"),("holdout",root/"benchmarks/holdout_cases",root/"benchmarks/holdout_results")]
keys=["game_hybrid_tuned","rapid_default"]
def norm(x):
    return " ".join(unicodedata.normalize("NFKC",str(x)).replace("İ","i").casefold().split())
def lev(a,b):
    old=list(range(len(b)+1))
    for i,c in enumerate(a,1):
        row=[i]
        for j,d in enumerate(b,1):
            row.append(min(row[-1]+1,old[j]+1,old[j-1]+(c!=d)))
        old=row
    return old[-1]
def measure(truth,records):
    m={}
    for item in records:m.setdefault(item["name"],[]).append(item)
    exact=allpred=noise=groundtotal=distclean=distraw=charcount=0
    times=[];samples=[]
    for name,lines in truth.items():
        rows=m[name];texts=rows[0]["texts"]
        expected=Counter(map(norm,lines))
        found=Counter(map(norm,texts))
        ok=sum(min(n,found[line]) for line,n in expected.items())
        junk=sum(norm(t)=="□" for t in texts)
        exact+=ok;allpred+=len(texts);noise+=junk;groundtotal+=len(lines)
        gt=norm(" ".join(lines))
        raw=norm(" ".join(texts))
        clean=norm(" ".join(x for x in texts if norm(x)!="□"))
        charcount+=len(gt)
        distraw+=lev(gt,raw);distclean+=lev(gt,clean)
        times.extend(row["ms"] for row in rows)
        samples.append({"file":name,"correct":ok,"ground":len(lines),"noise":junk,
                        "pred":texts,"truth":lines})
    times.sort()
    p=exact/allpred if allpred else 0
    r=exact/groundtotal if groundtotal else 0
    return {
        "exact":exact,"truth_lines":groundtotal,"predicted_lines":allpred,"phantom_boxes":noise,
        "line_precision":round(100*p,2),"line_recall":round(100*r,2),
        "line_f1":round(200*p*r/(p+r),2) if p+r else 0,
        "joined_raw_accuracy":round(100*max(0,1-distraw/charcount),2),
        "joined_noise_filtered_accuracy":round(100*max(0,1-distclean/charcount),2),
        "mean_ms":round(mean(times),1),"median_ms":round(median(times),1),
        "p95_ms":round(times[math.ceil(len(times)*.95)-1],1),
        "cases":samples}
out={}
for dataset,caseroot,resultsroot in sets:
    truth=json.loads((caseroot/"truth.json").read_text())
    out[dataset]={}
    for key in keys:
        d=json.loads((resultsroot/("results_"+key+".json")).read_text())
        out[dataset][key]=measure(truth,d["records"])
(target/"SUMMARY.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
head=["# GameTranslatorOCR vs RapidOCR PP-OCRv6 (Fedora CPU)","",
"Both used already installed models, no downloads. Tests: 11/33 original images/lines + 10/30 new images/lines, 2 passes each.",
"Hybrid: v5 detector + v6 recognizer + 6px crop. RapidOCR: v6 detector + v6 recognizer.",
"","| Set | Engine | Noise-filtered joined text accuracy | Exact lines | Exact-line precision | Exact-line F1 | Extra square boxes | Mean CPU | p95 |",
"|---|---|---:|---:|---:|---:|---:|---:|---:|"]
for setname,scores in out.items():
    for key,d in scores.items():
        name="GameTranslatorOCR hybrid" if key=="game_hybrid_tuned" else "RapidOCR PP-OCRv6"
        head.append(f'| {setname} | {name} | {d["joined_noise_filtered_accuracy"]}% | {d["exact"]}/{d["truth_lines"]} | {d["line_precision"]}% | {d["line_f1"]}% | {d["phantom_boxes"]} | {d["mean_ms"]} ms | {d["p95_ms"]} ms |')
head.extend(["","Accuracy ignores only standalone square (□) false boxes, which are counted separately as extra detections. Ordering differences can still affect joined-text accuracy.",
"Exact-line precision counts ALL detected text boxes including extraneous boxes.",
"Scores on synthetic images do not establish real game accuracy, and model detectors are not identical.",
"","## Notable mismatches"])
for setname,scores in out.items():
    head.append("### "+setname)
    for key,d in scores.items():
        head.append("#### "+key)
        for case in d["cases"]:
            if case["correct"]<case["ground"] or case["noise"]:
                head.append("- "+case["file"]+": correct "+str(case["correct"])+"/"+str(case["ground"])+
                            ", extra squares "+str(case["noise"])+", detected "+repr(case["pred"]))
(target/"REPORT.md").write_text("\n".join(head)+"\n")
for setname,scores in out.items():
    print(setname)
    for k,d in scores.items():
        print(k,"char(clean)",d["joined_noise_filtered_accuracy"],
            "char(raw)",d["joined_raw_accuracy"],"exact",d["exact"],"/",d["truth_lines"],
            "detections",d["predicted_lines"],"square",d["phantom_boxes"],
            "F1",d["line_f1"],"ms",d["mean_ms"])
