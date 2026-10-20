from pathlib import Path
from PIL import Image,ImageEnhance,ImageFilter
from collections import Counter
import json,base64,subprocess,statistics,io,unicodedata
root=Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR")
suite_names=["cases","holdout_cases","independent_stress"]
data=[]
def norm(x):return unicodedata.normalize("NFKC",str(x)).replace("İ","i").casefold()
for suite in suite_names:
 folder=root/"benchmarks"/suite
 truth=json.loads((folder/"truth.json").read_text())
 for file in sorted(folder.glob("*.png")):
  img=Image.open(file).convert("RGB")
  for variant in ["base","unsharp_contrast"]:
   modified=img if variant=="base" else ImageEnhance.Contrast(img.filter(ImageFilter.UnsharpMask(radius=1.0,percent=150,threshold=2))).enhance(1.4)
   buffer=io.BytesIO();modified.save(buffer,format="PNG")
   data.append((suite,file.name,variant,truth[file.name],buffer.getvalue()))
wd=root/"GameTranslator.Linux/release_ownocr_quality960/OwnOCR"
inp="\n".join(json.dumps({"Id":i+1,"Image":base64.b64encode(row[4]).decode(),"Language":"tr","TurkishEnglishOnly":True}) for i,row in enumerate(data))+"\n"
p=subprocess.run(["dotnet",str(wd/"OwnOcr.Worker.dll")],cwd=wd,input=inp,text=True,capture_output=True,timeout=60)
if p.returncode:raise RuntimeError(p.stderr[-500:])
lines=[json.loads(s) for s in p.stdout.splitlines() if s.strip()]
for suite in suite_names:
 for variant in ["base","unsharp_contrast"]:
  matched=total=extra=0;ms=[];fails=[]
  for (part,name,v,truth,_),result in zip(data,lines):
   if part!=suite or v!=variant:continue
   actual=[x["Text"] for x in result["Lines"]]
   expected=Counter(map(norm,truth));pred=Counter(map(norm,actual))
   h=sum(min(c,pred[s]) for s,c in expected.items())
   matched+=h;total+=len(truth);extra+=len(actual)-h;ms.append(result["Milliseconds"])
   if h!=len(truth) or len(actual)!=h:fails.append((name,truth,actual))
  print(suite,variant,"CORRECT",matched,"/",total,"EXTRA",extra,"MEAN_MS",round(statistics.mean(ms),1),"FAILURES",repr(fails),flush=True)
