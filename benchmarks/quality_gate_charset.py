#!/usr/bin/env python3
"""Opt-in Turkish+English charset safety gate. Local models only; no downloads."""
from pathlib import Path
from collections import Counter
from statistics import mean
import json,os,subprocess,sys,unicodedata
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models/latin-v6-hybrid"
SUITES=("cases","holdout_cases","independent_stress")
def norm(s):
    return " ".join(unicodedata.normalize("NFKC",s).replace("İ","i").casefold().split())
def run(folder,restricted):
    cmd=["dotnet",str(CLI),"suite",str(folder),str(MODEL),"2","6","--enhanced","--fast"]
    if restricted:cmd.append("--tr-charset")
    env=os.environ.copy()
    env["GTOCR_INTRAOP_THREADS"]="6"
    result=subprocess.run(cmd,env=env,check=True,text=True,
                          capture_output=True,timeout=60)
    rows=[json.loads(x.split("\t",1)[1]) for x in result.stdout.splitlines()
          if x.startswith("BENCHRESULT\t")]
    return {(x["name"],x["pass"]):x for x in rows}
def accuracy(row,ref):
    goal=Counter(map(norm,ref))
    got=Counter(map(norm,row["texts"]))
    count=sum(min(n,got[text]) for text,n in goal.items())
    return count,len(ref),len(row["texts"])
repaired=0;regressed=[]
total_old=total_new=total_ref=0
for dirname in SUITES:
    folder=ROOT/"benchmarks"/dirname
    truth=json.loads((folder/"truth.json").read_text(encoding="utf8"))
    old=run(folder,False)
    new=run(folder,True)
    assert len(old)==len(new)==len(truth)*2
    before=after=needed=0
    for key,existing in old.items():
        name,turn=key
        previous,required,old_total=accuracy(existing,truth[name])
        updated,_,new_total=accuracy(new[key],truth[name])
        before+=previous;after+=updated;needed+=required
        was_correct=previous==required and old_total==required
        now_correct=updated==required and new_total==required
        if was_correct and not now_correct:
            regressed.append((name,turn,existing["texts"],new[key]["texts"]))
        if not was_correct and now_correct:repaired+=1
    total_old+=before;total_new+=after;total_ref+=needed
    old_ms=mean(x["ms"] for x in old.values())
    new_ms=mean(x["ms"] for x in new.values())
    print(f"{dirname}: {before}/{needed} -> {after}/{needed}; "+
          f"{old_ms:.1f}ms -> {new_ms:.1f}ms; regressions={len(regressed)}",flush=True)
print(f"ALL_CASES: {total_old}/{total_ref} -> {total_new}/{total_ref}; "+
      f"repaired_records={repaired}, regressed_records={len(regressed)}",flush=True)
for r in regressed:print("REGRESSION",r,flush=True)
if regressed or total_new<total_old:sys.exit(1)
print("TR_CHARSET_GATE=PASS")
