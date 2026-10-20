#!/usr/bin/env python3
"""Second, held-out synthetic game UI set; preinstalled Pillow only, no download."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import random, json, sys, math
dest=Path(sys.argv[1]);dest.mkdir(parents=True,exist_ok=True)
bold="/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
regular="/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
if not Path(bold).exists():
    bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
labels=[
    ["Find the hidden key","Görüşürüz","Hızlı seyahat"],
    ["Işığa doğru","Kapı kilitli","Run quickly"],
    ["Şifre yanlış","Enemy spotted","Target acquired"],
    ["Büyük ödül","Seviye yükseldi","Continue"],
    ["Kılıç hasar gördü","Health restored","Görev iptal edildi"],
    ["Inventory full","Çözüm bulundu","İkinci bölüm"],
    ["Press SPACE","Hedefe yaklaşıyoruz","Karanlık çöktü"],
    ["Çıkışa ilerle","Find the map","Köprüye geri dön"],
    ["Üçüncü kapı","Gizli bölge keşfedildi","Mission complete"],
    ["Öğrenci girişi","Yolculuk başlıyor","Use magic"]
]
rng=random.Random(41445)
truth={}
for i,lines in enumerate(labels):
    width,height=(1280,720) if i in (2,5,8) else (960,540)
    style=i%5
    background = (245,246,250) if style==2 else (29,38,52) if style==0 else (12,20,29)
    if style==4:background=(63,73,80)
    im=Image.new("RGB",(width,height),background)
    dr=ImageDraw.Draw(im)
    if style==1:
        for k in range(35):
            x,y=rng.randrange(width),rng.randrange(height)
            r=rng.randrange(6,30)
            dr.rectangle((x,y,x+r,y+r),outline=(40,63,78),width=1)
    if style==3:
        for k in range(20):
            x,y=rng.randrange(width),rng.randrange(height)
            dr.ellipse((x,y,x+60,y+20),outline=(29,63,62),width=1)
    size=(25 if i in (1,5) else 30 if i in (4,8,9) else 36)
    font=ImageFont.truetype(regular if i in (1,5,9) else bold,size)
    ys=[90,245,405] if height==540 else [130,330,545]
    for idx,(line,y) in enumerate(zip(lines,ys)):
        x=70
        if style==2:
            color=(30,36,49)
        elif style==4:
            color=(160,164,170)
        elif style==3:
            color=(250,220,120) if idx==1 else (245,249,246)
        else:
            color=(245,245,244) if idx!=1 else (187,241,255)
        box=dr.textbbox((x,y),line,font=font)
        if style==0:
            dr.rounded_rectangle((x-12,y-9,box[2]+15,box[3]+8),radius=8,fill=(20,26,39))
        dr.text((x,y),line,font=font,fill=color,
                stroke_width=2 if style==3 else 0,
                stroke_fill=(0,0,0))
    if i==6: im=im.filter(ImageFilter.GaussianBlur(0.65))
    if i==8: im=im.rotate(-2.5,resample=Image.Resampling.BILINEAR,expand=False,fillcolor=background)
    fname=f"H{i:02d}_unseen.png"
    im.save(dest/fname)
    truth[fname]=lines
(dest/"truth.json").write_text(json.dumps(truth,ensure_ascii=False,indent=2),encoding="utf8")
print("holdout",len(truth),"images",sum(len(x) for x in truth.values()),"lines")
