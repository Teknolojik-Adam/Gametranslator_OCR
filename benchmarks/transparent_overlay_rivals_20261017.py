from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageFilter
import numpy as np,io,json,base64,subprocess,time,statistics,unicodedata,tempfile,random
from collections import Counter
from rapidocr import RapidOCR
import rapidocr
ROOT=Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR")
OUT=ROOT/"benchmarks/transparent_overlay_20261017"
OUT.mkdir(parents=True,exist_ok=True)
font="/usr/share/fonts/google-noto/NotoSans-Regular.ttf"
bold="/usr/share/fonts/google-noto/NotoSans-Bold.ttf"
mono="/usr/share/fonts/google-noto/NotoSansMono-Regular.ttf"
spec=[
("dark_panel85","dark",216,["Görev tamamlandı","Sığınağa geri dön","Press E to continue"],(250,250,246),29,"regular"),
("dark_panel50","dark",128,["Görev tamamlandı","Sığınağa geri dön","Press E to continue"],(250,250,246),29,"regular"),
("dark_panel20","dark",51,["Görev tamamlandı","Sığınağa geri dön","Press E to continue"],(250,250,246),29,"regular"),
("no_panel_white","dark",0,["Yeni yetenek açıldı","Kapıya doğru ilerle","Victory is near"],(255,255,255),28,"bold"),
("bright_panel85","bright",216,["Ekran çözünürlüğü","Çevrimdışı mod","İlk Kurulum Başlıyor"],(14,22,34),27,"regular"),
("bright_panel50","bright",128,["Ekran çözünürlüğü","Çevrimdışı mod","İlk Kurulum Başlıyor"],(14,22,34),27,"regular"),
("bright_panel20","bright",51,["Ekran çözünürlüğü","Çevrimdışı mod","İlk Kurulum Başlıyor"],(14,22,34),27,"regular"),
("no_panel_dark","bright",0,["HP 432 OCR Araştırması","GameTranslator Linux","Merhaba dünya!"],(12,20,28),27,"regular"),
("glass_blur70","blur",178,["Kılıç dayanıklılığı 70","Zırh kapasitesi 45","Yeni görev alındı"],(255,255,255),28,"regular"),
("glass_blur35","blur",89,["Kılıç dayanıklılığı 70","Zırh kapasitesi 45","Yeni görev alındı"],(255,255,255),28,"regular"),
("color_blue60","blue",153,["Görev güncellendi","Bölüm başarıyla bitti","Return to the shelter"],(248,251,255),27,"regular"),
("color_blue25","blue",64,["Görev güncellendi","Bölüm başarıyla bitti","Return to the shelter"],(248,251,255),27,"regular"),
("small_tabs_dark","dark",100,["GameTranslator Linux","HP 432 OCR Araştırması","Bizim OCR — RapidOCR"],(255,255,255),20,"regular"),
("small_tabs_bright","bright",120,["İlk Kurulum Başlıyor","Çevrimdışı mod","Sığınağa geri dön"],(25,28,35),20,"regular"),
("subtitle_shadow","dark",0,["Sığınağa geri dön","Görev tamamlandı","Çevrimdışı mod"],(255,255,255),27,"shadow"),
("subtitle_outline","dark",0,["Sığınağa geri dön","Görev tamamlandı","Çevrimdışı mod"],(255,255,255),27,"outline"),
]
truth={}
for index,(name,style,alpha,lines,color,fs,kind) in enumerate(spec):
 w,h=960,540
 rng=np.random.default_rng(101+index%4)
 a=np.zeros((h,w,3),dtype=np.uint8)
 yy,xx=np.mgrid[0:h,0:w]
 if style in ("dark","blur","blue"):
  a[:,:,0]=(30+35*np.sin(xx/53)+16*np.cos(yy/43)+rng.integers(-15,15,size=(h,w))).clip(0,255).astype("uint8")
  a[:,:,1]=(60+34*np.sin(xx/90)+22*np.cos(yy/29)+rng.integers(-17,18,size=(h,w))).clip(0,255).astype("uint8")
  a[:,:,2]=(85+45*np.sin(xx/67)+35*np.cos(yy/35)+rng.integers(-19,20,size=(h,w))).clip(0,255).astype("uint8")
 else:
  a[:,:,0]=(178+44*np.sin(xx/71)+rng.integers(-15,15,size=(h,w))).clip(0,255).astype("uint8")
  a[:,:,1]=(193+35*np.cos(yy/39)+rng.integers(-13,14,size=(h,w))).clip(0,255).astype("uint8")
  a[:,:,2]=(207+26*np.sin(xx/65)+rng.integers(-15,15,size=(h,w))).clip(0,255).astype("uint8")
 im=Image.fromarray(a,"RGB").convert("RGBA")
 bg=ImageDraw.Draw(im,"RGBA")
 for j in range(15):
  rx=(j*67+37)%w; ry=(j*41+70)%h
  bg.rounded_rectangle((rx,ry,rx+35+(j%5)*26,ry+10+(j%4)*22),radius=8,fill=(175,130,80,60) if style!="bright" else (42,75,125,55))
 if style=="blur":
  cropped=im.crop((65,120,895,430)).filter(ImageFilter.GaussianBlur(8))
  im.paste(cropped,(65,120))
 lay=Image.new("RGBA",im.size,(0,0,0,0))
 draw=ImageDraw.Draw(lay,"RGBA")
 if alpha:
  panel=(12,20,33,alpha) if style in ("dark","blur") else (230,236,247,alpha) if style=="bright" else (17,53,114,alpha)
  draw.rounded_rectangle((65,115,895,430),radius=15,fill=panel)
 f=ImageFont.truetype(bold if kind=="bold" else font,fs)
 for idx,line in enumerate(lines):
  y=145+idx*82
  kw={"font":f,"fill":color+(255,)}
  if kind=="shadow":
   draw.text((99,y+2),line,font=f,fill=(0,0,0,190))
  if kind=="outline":kw["stroke_width"]=2;kw["stroke_fill"]=(0,0,0,255)
  draw.text((96,y),line,**kw)
 im=Image.alpha_composite(im,lay).convert("RGB")
 fname=name+".png"
 im.save(OUT/fname)
 truth[fname]=lines
(OUT/"truth.json").write_text(json.dumps(truth,ensure_ascii=False,indent=2))
print("CREATED",len(spec),"IMAGES",flush=True)
entries=[]
for name,*_ in spec:
 f=OUT/(name+".png");image=Image.open(f).convert("RGB")
 modified=ImageEnhance.Contrast(image.filter(ImageFilter.UnsharpMask(radius=1,percent=150,threshold=2))).enhance(1.4)
 b=io.BytesIO();modified.save(b,format="PNG")
 entries.append((f.name,f.read_bytes(),b.getvalue()))
WD=ROOT/"GameTranslator.Linux/release_ownocr_quality960/OwnOCR"
results={}
for variant in ("raw","improved"):
 payload="\n".join(json.dumps({"Id":i+1,"Image":base64.b64encode(row[1 if variant=="raw" else 2]).decode(),"Language":"tr","TurkishEnglishOnly":True}) for i,row in enumerate(entries))+"\n"
 p=subprocess.run(["dotnet",str(WD/"OwnOcr.Worker.dll")],input=payload,text=True,capture_output=True,cwd=WD,timeout=45)
 if p.returncode:raise RuntimeError(p.stderr[-700:])
 outputs=[json.loads(x) for x in p.stdout.splitlines() if x.strip()]
 results["ours_"+variant]=[{"texts":[v["Text"] for v in item["Lines"]],"ms":item["Milliseconds"]} for item in outputs]
 print("OURS",variant,"DONE",flush=True)
pkg=Path(rapidocr.__file__).resolve().parent
rapid=RapidOCR(params={"Global.use_cls":False,"Global.log_level":"error","Det.model_path":str(pkg/"models/PP-OCRv6_det_small.onnx"),"Rec.model_path":str(pkg/"models/PP-OCRv6_rec_small.onnx")})
rapid(str(OUT/(spec[0][0]+".png")),use_cls=False)
for variant in ("raw","improved"):
 rows=[]
 for n,original,edited in entries:
  arr=np.asarray(Image.open(io.BytesIO(original if variant=="raw" else edited)).convert("RGB"))
  st=time.perf_counter(); pred=rapid(arr,use_cls=False)
  rows.append({"texts":list(pred.txts or []),"ms":(time.perf_counter()-st)*1000})
 results["rapid_"+variant]=rows
 print("RAPID",variant,"DONE",flush=True)
with tempfile.TemporaryDirectory() as tmp:
 for variant in ("raw","improved"):
  rows=[]
  for i,(n,original,edited) in enumerate(entries):
   f=Path(tmp)/(str(i)+".png")
   f.write_bytes(original if variant=="raw" else edited)
   st=time.perf_counter(); p=subprocess.run(["tesseract",str(f),"stdout","-l","eng+turk","--psm","11"],capture_output=True,text=True,timeout=15)
   if p.returncode:raise RuntimeError(p.stderr[-450:])
   rows.append({"texts":[s.strip() for s in p.stdout.splitlines() if s.strip()],"ms":(time.perf_counter()-st)*1000})
  results["tesseract_"+variant]=rows
  print("TESS",variant,"DONE",flush=True)
def norm(s):return " ".join(unicodedata.normalize("NFKC",str(s)).replace("İ","i").casefold().split())
def lev(a,b):
 dp=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  nx=[i]
  for j,cb in enumerate(b,1):nx.append(min(nx[-1]+1,dp[j]+1,dp[j-1]+(ca!=cb)))
  dp=nx
 return dp[-1]
summary={}
for engine,rows in results.items():
 found=needed=excess=errors=chars=0
 bad=[];timings=[]
 for (name,_,_),row in zip(entries,rows):
  reference=truth[name]
  a=Counter(map(norm,reference));b=Counter(map(norm,row["texts"]))
  hit=sum(min(ct,b[text]) for text,ct in a.items())
  found+=hit;needed+=len(reference);excess+=len(row["texts"])-hit
  canonical=norm(" ".join(reference));predicted=norm(" ".join(row["texts"]))
  errors+=lev(canonical,predicted);chars+=len(canonical)
  timings.append(row["ms"])
  if hit!=len(reference) or len(row["texts"])!=hit:bad.append({"case":name,"expected":reference,"actual":row["texts"]})
 summary[engine]={"exact_lines":found,"reference_lines":needed,"extra_or_wrong_lines":excess,"char_accuracy_pct":round(max(0,1-errors/chars)*100,2),"mean_ocr_ms":round(statistics.mean(timings),1),"median_ocr_ms":round(statistics.median(timings),1),"errors":bad}
 print("SCORE",engine,"EXACT",found,"/",needed,"EXTRA",excess,"CHAR",summary[engine]["char_accuracy_pct"],"MEAN_MS",summary[engine]["mean_ocr_ms"],flush=True)
(OUT/"results.json").write_text(json.dumps({"summary":summary,"case_specs":[{"name":n,"alpha":a,"style":s,"lines":l} for n,s,a,l,*_ in spec],"notes":"Synthetic RGB screenshots with text over composited semi-transparent panels. 16 images x 3 lines. All engines same pixels per variant. OCR-only time, excludes Pillow preprocess and capture, Tesseract CLI startup included. No alpha-only raw-image benchmark."},ensure_ascii=False,indent=2))
print("RESULTS",OUT/"results.json",flush=True)
