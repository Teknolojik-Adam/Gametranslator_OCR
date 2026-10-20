#!/usr/bin/env python3
"""Local Turkish-English CTC candidate evaluation. No download, no install."""
from pathlib import Path
from collections import Counter
from statistics import mean
import json,os,subprocess,sys,unicodedata

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"benchmarks/quality_retry"
OUT.mkdir(exist_ok=True)
CLI=ROOT/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models/latin-v6-hybrid"
DATASETS={"development":"cases","holdout":"holdout_cases",
          "independent_stress":"independent_stress"}
def norm(s):
    return " ".join(unicodedata.normalize("NFKC",str(s)).replace("İ","i").casefold().split())
def ed(a,b):
    old=list(range(len(b)+1))
    for i,letter in enumerate(a,1):
        row=[i]
        for j,other in enumerate(b,1):
            row.append(min(row[-1]+1,old[j]+1,old[j-1]+(letter!=other)))
        old=row
    return old[-1]
def compare(records,truth):
    matches=refsize=predsize=errors=chars=0
    mismatches=[]
    for row in records:
        name=row["name"]
        goal=truth[name]
        seen=row["texts"]
        expected=Counter(map(norm,goal))
        predicted=Counter(map(norm,seen))
        match=sum(min(num,predicted[text]) for text,num in expected.items())
        gt=norm(" ".join(goal))
        actual=norm(" ".join(seen))
        distance=ed(gt,actual)
        matches+=match;refsize+=len(goal);predsize+=len(seen);errors+=distance;chars+=len(gt)
        if match!=len(goal) or len(goal)!=len(seen) or distance:
            mismatches.append({"name":name,"pass":row["pass"],
                               "truth":goal,"observed":seen,
                               "confidences":row.get("confidences"),"edits":distance})
    p=matches/predsize if predsize else 0
    r=matches/refsize if refsize else 0
    return {"lines":f"{matches}/{refsize}","exact":matches,"total":refsize,
            "predicted":predsize,"character_accuracy":round(100*max(0,1-errors/max(1,chars)),3),
            "mean_ms":round(mean(q["ms"] for q in records),2),
            "f1":round(200*p*r/(p+r),2) if p+r else 0,
            "errors":mismatches}
def run(dataset):
    folder=ROOT/"benchmarks"/DATASETS[dataset]
    truth=json.loads((folder/"truth.json").read_text(encoding="utf8"))
    result={}
    for profile,fast,limited in (
        ("normal",False,False),("fast",True,False),
        ("normal_tr",False,True),("fast_tr",True,True)):
        flags=["--enhanced"]
        if fast:flags+=["--fast"]
        if limited:flags+=["--tr-charset"]
        cmd=["dotnet",str(CLI),"suite",str(folder),str(MODEL),"2","6"]+flags
        env=os.environ.copy()
        env["GTOCR_INTRAOP_THREADS"]="6"
        p=subprocess.run(cmd,capture_output=True,text=True,env=env,
                         check=True,timeout=55)
        records=[json.loads(x.split("\t",1)[1]) for x in p.stdout.splitlines()
                 if x.startswith("BENCHRESULT\t")]
        if len(records)!=len(truth)*2:
            raise ValueError("Wrong result count: "+profile)
        stat=compare(records,truth)
        result[profile]={"summary":stat,"records":records}
        print(f"{dataset} {profile:10s} {stat['lines']:8s} "
              f"chars={stat['character_accuracy']:.3f}% F1={stat['f1']}% "
              f"ms={stat['mean_ms']} errors={len(stat['errors'])}",flush=True)
        for e in stat["errors"][:12]:
            if e["pass"]==0:
                print("    "+e["name"]+": "+repr(e["observed"]),flush=True)
    for a,b in [("normal","normal_tr"),("fast","fast_tr")]:
        rowsA={(x["name"],x["pass"]):x for x in result[a]["records"]}
        rowsB={(x["name"],x["pass"]):x for x in result[b]["records"]}
        changed=[(name,pa,rowsA[(name,pa)]["texts"],rowsB[(name,pa)]["texts"])
                 for name,pa in rowsA if rowsA[(name,pa)]["texts"]!=rowsB[(name,pa)]["texts"]]
        print(a+" -> "+b+" CHANGED:",len(changed),flush=True)
        for item in changed:
            if item[1]==0:print("   ",item[0],"ORIGINAL",item[2],"RESTRICTED",item[3],flush=True)
    (OUT/("charset_"+dataset+".json")).write_text(json.dumps(result,indent=2,ensure_ascii=False),
                                             encoding="utf8")
if __name__=="__main__":
    run(sys.argv[1])
