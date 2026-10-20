#!/usr/bin/env python3
"""Local only: tune ONNX detector input resolution while checking OCR output."""
import json, os, subprocess, sys, unicodedata, math
from collections import Counter
from pathlib import Path
from statistics import mean
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models/latin-v6-hybrid"
OUTPUT=ROOT/"benchmarks"/"performance_tuning"
OUTPUT.mkdir(exist_ok=True)

def norm(x):
    return " ".join(unicodedata.normalize("NFKC",str(x)).replace("İ","i").casefold().split())

def check(rows,truth):
    byname={}
    for x in rows:
        if x["pass"]==0:byname[x["name"]]=x["texts"]
    matched=produced=expected=0
    errors=[]
    for name,ref in truth.items():
        guess=byname[name]
        exp=Counter(map(norm,ref))
        rec=Counter(map(norm,guess))
        m=sum(min(count,rec[line]) for line,count in exp.items())
        matched+=m;produced+=len(guess);expected+=len(ref)
        if m!=len(ref) or len(guess)!=len(ref):
            errors.append({"name":name,"truth":ref,"guess":guess})
    return matched,expected,produced,errors

def run(side,dataset):
    folder=ROOT/"benchmarks"/("cases" if dataset=="development" else "holdout_cases")
    truth=json.loads((folder/"truth.json").read_text(encoding="utf8"))
    cmd=["dotnet",str(CLI),"suite",str(folder),str(MODEL),
         "2","6","--enhanced",f"--det-side={side}"]
    env=os.environ.copy()
    env["GTOCR_INTRAOP_THREADS"]="6"
    r=subprocess.run(cmd,env=env,capture_output=True,text=True,
        check=True,timeout=65)
    rows=[json.loads(line.split("\t",1)[1])
          for line in r.stdout.splitlines() if line.startswith("BENCHRESULT\t")]
    if len(rows)!=len(truth)*2:
        raise RuntimeError("Bad result count "+str(len(rows))+": "+r.stderr[-500:])
    matched,expected,produced,errors=check(rows,truth)
    keys=["DecodeMs","PreprocessMs","DetectionMs","PostprocessMs","CropMs","RecognitionMs","TotalMs"]
    means={key:round(mean(x["stages"][key] for x in rows),1) for key in keys}
    out={"side":side,"set":dataset,"exact":matched,"truth":expected,
         "predicted":produced,"mean":means,"errors":errors}
    (OUTPUT/(f"{side}_{dataset}.json")).write_text(
        json.dumps(out,indent=2,ensure_ascii=False),encoding="utf8")
    print(f'{side} {dataset:11s} {matched:2d}/{expected} '+
          f'outputs {produced} ms {means["TotalMs"]:6.1f} '+
          f'det {means["DetectionMs"]:5.1f} rec {means["RecognitionMs"]:5.1f} '+
          f'errors: {[(x["name"],x["guess"]) for x in errors]}',
          flush=True)

for arg in sys.argv[1:]:
    side=int(arg)
    for dataset in ["development","holdout"]:
        run(side,dataset)
