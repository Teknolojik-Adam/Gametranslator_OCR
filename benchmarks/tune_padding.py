#!/usr/bin/env python3
"""Tune native recognition crop padding; no network, no new OCR models."""
import json, subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import compare_local
root=Path(__file__).resolve().parents[1]
dll=root/"src/GameTranslatorOCR.Cli/bin/Release/net8.0/GameTranslatorOCR.Cli.dll"
cases=root/"benchmarks/cases"
modeldirs={"v5":root/"models/latin","hybrid":root/"models/latin-v6-hybrid"}
all_results={}
for label, model_dir in modeldirs.items():
    for padding in (0,2,4,6,8):
        args=["dotnet",str(dll),"suite",str(cases),str(model_dir),"1",str(padding)]
        start=time.perf_counter()
        res=subprocess.run(args,capture_output=True,text=True,timeout=70,check=True)
        rows=[json.loads(x.split("\t",1)[1]) for x in res.stdout.splitlines() if x.startswith("BENCHRESULT\t")]
        if len(rows)!=len(compare_local.IMAGES): raise RuntimeError("result mismatch"+res.stdout)
        metrics=compare_local.metrics(rows)
        key=f"{label}_padding_{padding}"
        all_results[key]={"metrics":metrics,"rows":rows}
        print(f'{key:24s} accuracy={metrics["char_accuracy"]:5.2f}% exact={metrics["exact_lines"]:2d}/33 mean={metrics["mean_ms"]:6.1f}ms wall={time.perf_counter()-start:.1f}s',flush=True)
outfile=root/"benchmarks/padding_tuning.json"
outfile.write_text(json.dumps(all_results,indent=2,ensure_ascii=False),encoding="utf-8")
print("Saved",outfile)
