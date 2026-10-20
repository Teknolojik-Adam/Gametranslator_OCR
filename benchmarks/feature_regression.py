#!/usr/bin/env python3
"""Compare opt-in GameTranslatorOCR v6-inspired features; no downloads."""
from pathlib import Path
import json,sys,subprocess
from statistics import mean
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v6_headtohead import measure
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"benchmarks/v6_features"
OUT.mkdir(exist_ok=True)
LABEL=sys.argv[1] if len(sys.argv)>1 else "holdout"
CASES=ROOT/"benchmarks"/("cases" if LABEL=="development" else "holdout_cases")
TRUTH=json.loads((CASES/"truth.json").read_text())
CLI=ROOT/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
MODEL=ROOT/"models/latin-v6-hybrid"
profiles={
 "baseline":[],
 "smart_filter_batch4":["--filter","--batch=4"],
 "all_optional":["--filter","--batch=4","--perspective","--adaptive","--adaptive-padding","--words"]
}
result={}
for name,flags in profiles.items():
    cmd=["dotnet",str(CLI),"suite",str(CASES),str(MODEL),"2","6"]+flags
    process=subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=55)
    rows=[json.loads(line.split("\t",1)[1])
        for line in process.stdout.splitlines() if line.startswith("BENCHRESULT\t")]
    if len(rows)!=len(TRUTH)*2:raise RuntimeError("Bad record count "+name)
    metrics=measure(TRUTH,rows)
    words=sum(r.get("words",0) for r in rows)
    angles=sum(r.get("angled",0) for r in rows)
    result[name]={"metrics":metrics,"word_count":words,"angled_boxes":angles,"records":rows}
    print(f'{LABEL} {name}: exact {metrics["exact"]}/{metrics["truth_lines"]}, '+
          f'boxes {metrics["predicted_lines"]}, fake □ {metrics["phantom_boxes"]}, '+
          f'F1 {metrics["line_f1"]}%, mean {metrics["mean_ms"]}ms, '+
          f'words {words}, angles {angles}',flush=True)
(OUT/(LABEL+".json")).write_text(json.dumps(result,indent=2,ensure_ascii=False))
