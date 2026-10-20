#!/usr/bin/env python3
"""Process peak RSS comparison. No downloads or package installs."""
import json,os,re,subprocess,time
from pathlib import Path
r=Path(__file__).resolve().parents[1]
case=r/"benchmarks/holdout_cases"
out=r/"benchmarks/holdout_results"
dll=r/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
entry=r/"benchmarks/compare_local.py"
env=os.environ.copy()
env["GTOCR_BENCH_CASES"]=str(case)
env["GTOCR_BENCH_OUT"]=str(out)
cmds={
    "GameTranslatorOCR v5 tuned":["dotnet",str(dll),"suite",str(case),str(r/"models/latin"),"2","6"],
    "GameTranslatorOCR hybrid tuned":["dotnet",str(dll),"suite",str(case),str(r/"models/latin-v6-hybrid"),"2","6"],
    "RapidOCR v5 matched":["python3",str(entry),"rapid_matched"]
}
data={}
for name,command in cmds.items():
    result=subprocess.run(["/usr/bin/time","-f","PEAK_KB=%M"]+command,
        capture_output=True,text=True,timeout=55,env=env,check=True)
    match=re.search(r"PEAK_KB=(\d+)",result.stderr)
    if match is None:raise RuntimeError("time peak not found: "+result.stderr)
    value=round(int(match.group(1))/1024,1)
    data[name]={"peak_rss_mb":value,"command":[command[0],command[1] if len(command)>1 else ""]}
    print(f"{name:40s}: {value:7.1f} MiB peak resident memory",flush=True)
(out/"MEMORY.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf8")
