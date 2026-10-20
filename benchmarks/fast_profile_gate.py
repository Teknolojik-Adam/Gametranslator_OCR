#!/usr/bin/env python3
"""Release quality gate: Fast OCR may ship only if every test line survives.
No internet access, installations or model downloads.
"""
from pathlib import Path
from collections import Counter
import json, os, subprocess, sys, unicodedata
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models/latin-v6-hybrid"

def normalize(text):
    return " ".join(unicodedata.normalize("NFKC",text).replace("İ","i").casefold().split())

total_matched=total_expected=total_outputs=0
for label,subdir in [("development","cases"),("holdout","holdout_cases")]:
    folder=ROOT/"benchmarks"/subdir
    truth=json.loads((folder/"truth.json").read_text(encoding="utf8"))
    command=["dotnet",str(CLI),"suite",str(folder),str(MODEL),
             "2","6","--enhanced","--fast"]
    env=os.environ.copy()
    env["GTOCR_INTRAOP_THREADS"]="6"
    p=subprocess.run(command,capture_output=True,text=True,
                     env=env,timeout=60,check=True)
    records=[json.loads(line.split("\t",1)[1]) for line in p.stdout.splitlines()
             if line.startswith("BENCHRESULT\t")]
    if len(records)!=len(truth)*2:
        sys.exit("FAIL: wrong result count: "+label)
    for item in records:
        name=item["name"]
        got=Counter(map(normalize,item["texts"]))
        expected=Counter(map(normalize,truth[name]))
        matched=sum(min(count,got[text]) for text,count in expected.items())
        if matched!=len(truth[name]) or len(item["texts"])!=len(truth[name]):
            print("FAIL:",label,name,"expected",truth[name],"got",item["texts"])
            sys.exit(1)
        total_matched+=matched
        total_expected+=len(truth[name])
        total_outputs+=len(item["texts"])
    ms=sum(item["ms"] for item in records)/len(records)
    print(f"{label}: {len(truth)} images, {sum(map(len,truth.values()))} lines, "+
          f"2 passes PASS, mean {ms:.1f} ms",flush=True)
print(f"FAST_PROFILE_GATE=PASS ({total_matched}/{total_expected} correct, {total_outputs} outputs)")
