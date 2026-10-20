#!/usr/bin/env python3
"""New independent OCR stress set. Deterministic, all local, no downloads.
This set is not used to tune detector dimensions.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, sys, random

dest=Path(sys.argv[1])
dest.mkdir(parents=True,exist_ok=True)
rng=random.Random(202610161415)
bold="/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
regular="/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
if not Path(bold).is_file():
    bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

cases=[
 ("dialogue_turkish",960,540,36,"dialogue",0,0,
  ["Şehrin kapıları açıldı","Işıklar yeniden yanıyor","Bütün görevler tamamlandı"]),
 ("english_subtitles",960,540,34,"dark",0,0,
  ["Return to the shelter","Follow the glowing trail","The journey continues"]),
 ("tiny_inventory",1280,720,22,"hud",0,0,
  ["Gümüş anahtar bulundu","Kılıç dayanıklılığı 70","Press F to inspect"]),
 ("bright_settings",1024,576,37,"bright",0,0,
  ["Görüntü ayarları","Ekran çözünürlüğü","Değişiklikleri kaydet"]),
 ("orange_quest",960,540,32,"gold",0,0,
  ["Yeni hedef belirlendi","Düşmanı etkisiz hale getir","Görev güncellendi"]),
 ("contrasty_dark",1152,648,29,"dark",0,0,
  ["İlk bölüm başlıyor","Şimdi gizlenmeliyiz","Stay near the river"]),
 ("color_hud",1366,768,25,"hud",0,0,
  ["Can seviyesi 100","Zırh kapasitesi 45","Yeni yetenek açıldı"]),
 ("soft_subtitle",960,540,33,"dialogue",0,0.7,
  ["Köprüden karşıya geç","İleride bir çıkış var","Don't look behind"]),
 ("slightly_rotated",960,540,37,"dark",2.0,0,
  ["Kapıya doğru ilerle","Üçüncü bölüm başladı","Victory is near"]),
 ("small_resolution",800,450,23,"dark",0,0,
  ["Çevrimdışı mod","Bir sonraki kayıt","Hikâyeye devam et"]),
 ("low_contrast",960,540,32,"low",0,0,
  ["Sığınağa geri dön","Haritayı kontrol et","Gösterge açık"]),
 ("wide_menu",1280,720,38,"bright",0,0,
  ["Kayıtlı oyunlar","Başarılar listesi","Ana menüye dön"]),
 ("outlined_subtitles",960,540,34,"outline",0,0,
  ["Şüpheli bir ses var","Hızlı koşmalıyız","Hedefe ulaştık"]),
 ("thin_font_ui",1280,720,29,"hud",0,0,
  ["Ödülleri topla","Köyün etrafını dolaş","Choose your weapon"])
]
truth={}
for i,(label,width,height,size,style,angle,blur,lines) in enumerate(cases):
    if style=="bright":bg=(239,242,248);fg=(21,34,51)
    elif style=="low":bg=(69,75,83);fg=(137,145,154)
    else:bg=(19,26,39);fg=(248,247,244)
    canvas=Image.new("RGB",(width,height),bg)
    dr=ImageDraw.Draw(canvas)
    if style=="hud":
        for j in range(32):
            x=rng.randrange(width);y=rng.randrange(height)
            col=(36,58,68)
            dr.rectangle((x,y,x+rng.randrange(6,75),y+rng.randrange(2,13)),
                         outline=col,width=1)
    if style=="dialogue":
        for j in range(3):
            y=[100,245,385][j] if height<=576 else [130,320,515][j]
            dr.rounded_rectangle((42,y-12,width-38,y+size+20),
                 fill=(29,37,52),radius=8)
    if style=="bright":
        for y in range(0,height,4):
            dr.line((0,y,width,y),fill=(236,239,245))
    font=ImageFont.truetype(regular if style in ("hud","low") else bold,size)
    yvals=([75,200,326] if height<=450 else
           [115,250,390] if height<=576 else
           [135,330,535])
    if angle:
        layer=Image.new("RGBA",(width,height),(0,0,0,0))
        draw=ImageDraw.Draw(layer)
    else:
        draw=dr
    for j,(line,y) in enumerate(zip(lines,yvals)):
        x=64
        color=fg
        if style=="gold":color=(245,223,128)
        if style=="hud" and j==1:color=(177,240,248)
        if style=="outline":
            draw.text((x,y),line,font=font,fill=fg,
                      stroke_width=2,stroke_fill=(0,0,0))
        else:
            draw.text((x,y),line,font=font,fill=color)
    if angle:
        layer=layer.rotate(angle,resample=Image.Resampling.BICUBIC,
                           expand=False,fillcolor=(0,0,0,0))
        canvas.paste(layer,(0,0),layer)
    if blur:
        canvas=canvas.filter(ImageFilter.GaussianBlur(blur))
    name=f"S{i:02d}_{label}.png"
    canvas.save(dest/name)
    truth[name]=lines
(dest/"truth.json").write_text(json.dumps(truth,ensure_ascii=False,indent=2),
                               encoding="utf8")
print(f"Created {len(truth)} independent stress cases, {sum(map(len,truth.values()))} lines at {dest}",flush=True)
