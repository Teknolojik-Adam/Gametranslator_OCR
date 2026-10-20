from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import json,base64,subprocess,statistics
root=Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR")
p=root/"benchmarks/independent_stress/S10_low_contrast.png"
im=Image.open(p).convert("RGB")
print("source",im.size,flush=True)
ims={"base":im,"contrast1.4":ImageEnhance.Contrast(im).enhance(1.4),"contrast1.8":ImageEnhance.Contrast(im).enhance(1.8),"contrast2.4":ImageEnhance.Contrast(im).enhance(2.4),"sharp1.5":ImageEnhance.Sharpness(im).enhance(1.5),"sharp2.5":ImageEnhance.Sharpness(im).enhance(2.5),"unsharp":im.filter(ImageFilter.UnsharpMask(radius=1.0,percent=150,threshold=2)),"gray":ImageOps.grayscale(im).convert("RGB"),"autocontrast":ImageOps.autocontrast(im,preserve_tone=False),"gamma075":im.point(lambda v:int(255*(v/255)**.75)),"gamma125":im.point(lambda v:int(255*(v/255)**1.25))}
ims["bilinear2x"]=im.resize((im.width*2,im.height*2),Image.Resampling.BILINEAR)
ims["bicubic2x"]=im.resize((im.width*2,im.height*2),Image.Resampling.BICUBIC)
ims["lanczos2x"]=im.resize((im.width*2,im.height*2),Image.Resampling.LANCZOS)
ims["unsharp_contrast"]=ImageEnhance.Contrast(ims["unsharp"]).enhance(1.4)
try:
 import io
 reqs=[]
 for name,im2 in ims.items():
  b=io.BytesIO();im2.save(b,format="PNG")
  reqs.append((name,json.dumps({"Id":len(reqs)+1,"Image":base64.b64encode(b.getvalue()).decode(),"Language":"tr","TurkishEnglishOnly":True})))
 for label in ("release_ownocr_quality960","release_ownocr_quality1280"):
  wd=root/"GameTranslator.Linux"/label/"OwnOCR"
  inp="\n".join(x[1] for x in reqs)+"\n"
  z=subprocess.run(["dotnet",str(wd/"OwnOcr.Worker.dll")],input=inp,text=True,capture_output=True,cwd=wd,timeout=55)
  if z.returncode:raise Exception(z.stderr[-500:])
  res=[json.loads(line) for line in z.stdout.splitlines() if line.strip()]
  for (name,_),v in zip(reqs,res):
   print(label,name,round(v["Milliseconds"],1),repr([x["Text"] for x in v["Lines"]]),flush=True)
except Exception as e:print("ERROR",str(e),flush=True);raise
