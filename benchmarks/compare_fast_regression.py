#!/usr/bin/env python3
"""Regression audit: normal 960 px vs fast 864 px on existing + NEW held-out samples.
No downloads. Keep results and report locally for repeatability.
"""
import json, os, re, subprocess, unicodedata, math, sys
from pathlib import Path
from collections import Counter
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"benchmarks"/"regression_20261016"
OUT.mkdir(exist_ok=True)
CLI=ROOT/"src"/"GameTranslatorOCR.Cli"/"bin"/"Release"/"net8.0"/"GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models"/"latin-v6-hybrid"
SUITES=[("development","cases"),("holdout","holdout_cases"),("independent_stress","independent_stress")]

def normalize(s):
    return " ".join(unicodedata.normalize("NFKC",str(s)).replace("İ","i").casefold().split())

def edit_distance(a,b):
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        row=[i]
        for j,cb in enumerate(b,1):
            row.append(min(row[-1]+1,prev[j]+1,prev[j-1]+(ca!=cb)))
        prev=row
    return prev[-1]

def run(suite,folder,profile):
    cmd=["/usr/bin/time","-f","GTOCR_PEAK_KB=%M",
         "dotnet",str(CLI),"suite",str(folder),str(MODEL),"2","6","--enhanced"]
    if profile=="fast":cmd.append("--fast")
    env=os.environ.copy()
    env["GTOCR_INTRAOP_THREADS"]="6"
    p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=60,env=env)
    rows=[json.loads(s.split("\t",1)[1]) for s in p.stdout.splitlines() if s.startswith("BENCHRESULT\t")]
    truth=json.loads((folder/"truth.json").read_text(encoding="utf8"))
    if len(rows)!=len(truth)*2:
        raise RuntimeError(f"Missing rows: {suite} {profile} {len(rows)}/{len(truth)*2}")
    observed={(r["name"],r["pass"]):r for r in rows}
    exact=refcount=predcount=char_edits=charcount=0
    unmatched=[];outcomes=[];ms=[]
    for name,expected_lines in truth.items():
        for pass_num in (0,1):
            item=observed[(name,pass_num)]
            predictions=item["texts"]
            refs=Counter(map(normalize,expected_lines))
            preds=Counter(map(normalize,predictions))
            match=sum(min(n,preds[text]) for text,n in refs.items())
            exact+=match
            refcount+=len(expected_lines)
            predcount+=len(predictions)
            reference=normalize(" ".join(expected_lines))
            hypothesis=normalize(" ".join(predictions))
            distance=edit_distance(reference,hypothesis)
            char_edits+=distance
            charcount+=len(reference)
            ms.append(item["ms"])
            record=dict(file=name,pass_num=pass_num,
                        matched=match,needed=len(expected_lines),
                        total_detected=len(predictions),edit_distance=distance,
                        truth=expected_lines,predicted=predictions)
            outcomes.append(record)
            if match!=len(expected_lines) or len(predictions)!=len(expected_lines) or distance!=0:
                unmatched.append(record)
    precision=exact/predcount if predcount else 0
    recall=exact/refcount if refcount else 0
    peak_match=re.search(r"GTOCR_PEAK_KB=(\d+)",p.stderr)
    peak=round(int(peak_match.group(1))/1024,1) if peak_match else None
    ms.sort()
    summary={
        "suite":suite,"profile":profile,"images":len(truth),"passes":2,
        "reference_lines":refcount,"exact_lines":exact,
        "detected_lines":predcount,
        "character_count":charcount,"character_edit_distance":char_edits,
        "character_accuracy_pct":round(100*max(0,1-char_edits/max(1,charcount)),2),
        "exact_line_recall_pct":round(100*recall,2),
        "exact_line_precision_pct":round(100*precision,2),
        "exact_line_f1_pct":round(200*precision*recall/(precision+recall),2) if precision+recall else 0,
        "mean_ms":round(mean(ms),1),
        "median_ms":round(median(ms),1),
        "p95_ms":round(ms[math.ceil(.95*len(ms))-1],1),
        "peak_process_rss_mib":peak,
        "failures":unmatched,"details":outcomes
    }
    (OUT/f"{suite}_{profile}.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf8")
    print(f"{suite:19s} {profile:6s} accurate={exact}/{refcount} "
          f"chars={summary['character_accuracy_pct']:6.2f}% "
          f"F1={summary['exact_line_f1_pct']:6.2f}% "
          f"latency={summary['mean_ms']:6.1f}ms peak={peak}MiB "
          f"errors={len(unmatched)}",flush=True)
    return summary

def report(results):
    lines=["# OCR Optimization Regression Audit — 16 October 2026",
           "","Both modes use the same GameTranslatorOCR enhanced hybrid model, with 6 CPU threads.",
           "Normal detector long side = 960 px. Fast detector long side = 864 px.",
           "Original 21 images were used during optimization; **independent_stress** (14 new images) was created only afterward.",
           "Each image is evaluated in two passes, exact text and all extraneous detections count against the score.",
           "Character accuracy = 1 - Levenshtein distance of normalized concatenated texts / reference characters.",
           "Case folded and Unicode NFKC normalized; accents like ş/s or ı/i remain distinct.",
           "",
           "| Dataset | Profile | Exact lines | Character accuracy | F1 | Mean | p95 | Peak RSS |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    for s,_ in SUITES:
        for profile in ["normal","fast"]:
            v=results[(s,profile)]
            lines.append(f'| {s} | {profile} | {v["exact_lines"]}/{v["reference_lines"]} | '
                         f'{v["character_accuracy_pct"]}% | {v["exact_line_f1_pct"]}% | '
                         f'{v["mean_ms"]}ms | {v["p95_ms"]}ms | {v["peak_process_rss_mib"]} MiB |')
    lines+=["","## Differences and failures"]
    for s,_ in SUITES:
        normal=results[(s,"normal")]
        fast=results[(s,"fast")]
        deltas=fast["exact_lines"]-normal["exact_lines"]
        char_delta=round(fast["character_accuracy_pct"]-normal["character_accuracy_pct"],2)
        speed_pct=round(100*(normal["mean_ms"]-fast["mean_ms"])/normal["mean_ms"],1)
        lines.append(f"- **{s}:** exact lines Δ {deltas}, char accuracy Δ {char_delta}pp, mean latency {speed_pct}% faster")
        for profile,res in (("normal",normal),("fast",fast)):
            for f in res["failures"]:
                lines.append(f'  - {profile} {f["file"]} pass={f["pass_num"]}: '
                             f'{f["matched"]}/{f["needed"]}, '
                             f'truth={f["truth"]}, got={f["predicted"]}')
    lines+=["","## Limitations",
            "- Both original and newly generated cases are **synthetic** game UI screenshots, not real games.",
            "- The 14 independent cases are a post-hoc stress set and were not used to pick 864px.",
            "- Average speed from two sequential batches can be affected by thermal/frequency variation.",
            "- RSS measures the whole .NET process; model memory alone is not isolated.",
            "- No GPU, Windows execution, native game screenshot collection, or translation overlay tested.",
            "- A clean result on these sets is not a guarantee that quality never degrades in any game.",
            ""]
    (OUT/"REPORT.md").write_text("\n".join(lines),encoding="utf8")
    print("REPORT",OUT/"REPORT.md",flush=True)

if __name__=="__main__":
    results={}
    for suite,subdir in SUITES:
        folder=ROOT/"benchmarks"/subdir
        for profile in ("normal","fast"):
            results[(suite,profile)]=run(suite,folder,profile)
    report(results)
