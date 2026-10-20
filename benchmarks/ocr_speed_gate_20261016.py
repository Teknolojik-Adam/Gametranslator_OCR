#!/usr/bin/env python3
"""OCR hotpath A/B regression. No model downloads or external APIs."""
import json, os, subprocess, sys, statistics, math, pathlib
ROOT=pathlib.Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR")
STORE=ROOT/"benchmarks"/"hotpath_20261016"
SETS=("cases", "holdout_cases", "independent_stress")
CLI=ROOT/"src"/"GameTranslatorOCR.Cli"/"bin"/"Release"/"net8.0"/"GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models"/"latin-v6-hybrid"
def main():
    label=sys.argv[1]
    if label not in ("baseline","candidate"):raise ValueError("baseline/candidate required")
    STORE.mkdir(parents=True, exist_ok=True)
    env=os.environ.copy();env["GTOCR_INTRAOP_THREADS"]="6"
    result=[]
    for name in SETS:
        cmd=["dotnet",str(CLI),"suite",str(ROOT/"benchmarks"/name),str(MODEL),"2","6",
             "--enhanced","--fast","--tr-charset"]
        done=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=55,check=True)
        rows=[json.loads(ln.split("\t",1)[1]) for ln in done.stdout.splitlines()
              if ln.startswith("BENCHRESULT\t")]
        expected=len(list((ROOT/"benchmarks"/name).glob("*.png")))*2
        if len(rows)!=expected: raise RuntimeError(f"{name}: {len(rows)} rows expected {expected}")
        result.extend([dict(x, suite=name) for x in rows])
        times=[x["ms"] for x in rows]
        print(f"{label} {name}: {len(rows)} images-passes; mean_ms={statistics.mean(times):.2f}; median_ms={statistics.median(times):.2f}",flush=True)
    (STORE/(label+".json")).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf8")
    if label=="candidate":
        reference=json.loads((STORE/"baseline.json").read_text(encoding="utf8"))
        ra={(x["suite"],x["name"],x["pass"]):x for x in reference}
        ca={(x["suite"],x["name"],x["pass"]):x for x in result}
        if set(ra)!=set(ca):raise RuntimeError("missing/extra cases")
        differences=[]
        for key in ra:
            a,b=ra[key],ca[key]
            for field in ("texts","bounds","words","angled","confidences"):
                if a[field]!=b[field]:
                    differences.append((key,field,a[field],b[field]))
        old=[x["ms"] for x in reference];new=[x["ms"] for x in result]
        print(f"Total {len(result)} images-passes: old={statistics.mean(old):.2f}ms new={statistics.mean(new):.2f}ms")
        print(f"TEXT_AND_GEOMETRY_DIFFERENCES={len(differences)}")
        for d in differences[:10]: print("DIFFERENCE",repr(d)[:500])
        if differences:sys.exit(1)
        print("OCR_HOTPATH_GATE=PASS")
if __name__=="__main__":main()
