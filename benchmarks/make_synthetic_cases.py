#!/usr/bin/env python3
"""Local-only synthetic game text benchmark. Does not download models or packages."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json, random, shutil, sys

out = Path(sys.argv[1])
baseline = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
random.seed(1402)
font_bold = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
font_regular = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
if not Path(font_bold).exists():
    font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

cases = {}
shutil.copy2(baseline, out / "00_baseline.png")
cases["00_baseline.png"] = ["GAME TRANSLATOR OCR", "Merhaba dünya!", "Quest completed"]

specs = [
    ("01_dark_dialogue", 960, 540, ["Open the ancient gate", "Görev tamamlandı", "Press E to continue"], 31, "dark", "white", "none"),
    ("02_small_hud", 1280, 720, ["LEVEL 27", "Health 100%", "Kalan süre 02:45"], 24, "hud", "white", "none"),
    ("03_outline_shadow", 960, 540, ["Düşman yaklaşıyor!", "Run to the bridge", "Bölüm başarıyla bitti"], 34, "dark", "gold", "outline"),
    ("04_bright_menu", 960, 540, ["Settings", "Yeni oyun", "Çıkış"], 43, "bright", "black", "none"),
    ("05_blurred_subtitles", 960, 540, ["Can you hear me?", "Kapıyı açmalıyız", "Follow the signal"], 31, "dark", "white", "blur"),
    ("06_low_contrast", 960, 540, ["The mission begins", "Yeni görev alındı", "Return to base"], 33, "low", "low", "none"),
    ("07_busy_background", 960, 540, ["Main quest", "İnceleme tamamlandı", "Return to the village"], 31, "busy", "white", "none"),
    ("08_tilted_screen", 960, 540, ["Victory is ours", "Yeni bölge keşfedildi", "Saving progress"], 32, "dark", "white", "tilt"),
    ("09_wide_720p", 1280, 720, ["The final chapter", "Karakter seviyesi 18", "Continue playing"], 26, "dark", "white", "none"),
    ("10_colored_ui", 960, 540, ["New achievement", "Başarı kilidi açıldı", "Collect your reward"], 31, "hud", "colors", "outline"),
]
for name, width, height, texts, font_size, theme, fgkind, effect in specs:
    if theme == "bright":
        base = Image.new("RGB", (width,height), (232,236,241))
    elif theme == "low":
        base = Image.new("RGB", (width,height), (57,65,69))
    else:
        base = Image.new("RGB", (width,height), (20,28,43))
    d = ImageDraw.Draw(base)
    if theme == "hud":
        for i in range(22):
            x = random.randrange(width)
            y = random.randrange(height)
            d.rectangle((x,y,x+random.randrange(4,50),y+random.randrange(2,8)), fill=(27,45,59))
        d.rectangle((15,15,width-15,height-15), outline=(40,74,88), width=2)
    if theme == "busy":
        for i in range(75):
            x = random.randrange(width)
            y = random.randrange(height)
            r = random.randrange(12,70)
            d.ellipse((x,y,x+r,y+r), outline=random.choice([(43,77,93),(74,44,85),(38,65,52)]), width=2)
    if theme == "bright":
        for y in range(height):
            d.line((0,y,width,y), fill=(232-y//25, 236-y//27, 241-y//28), width=1)

    f = ImageFont.truetype(font_bold if theme != "low" else font_regular, font_size)
    if height == 720:
        yvals = [100,316,548]
    else:
        yvals = [104,258,405]
    for i,(text,y) in enumerate(zip(texts,yvals)):
        x = 65 if (i != 1 or theme != "hud") else 165
        bbox = d.textbbox((x,y),text,font=f,stroke_width=0)
        if theme == "busy":
            d.rounded_rectangle((x-15,y-12,min(width-10,bbox[2]+28),bbox[3]+12),fill=(14,17,26),radius=9)
        if theme == "dark" and name=="01_dark_dialogue":
            d.rectangle((x-9,y-6,min(width-10,bbox[2]+10),bbox[3]+7),fill=(32,40,55))
        colors = ["#fcf8e8","#eddd95","#baf4ff"]
        if fgkind == "white":
            col = (243,243,246)
        elif fgkind == "gold":
            col = (252,221,124)
        elif fgkind == "black":
            col = (31,38,49)
        elif fgkind == "low":
            col = (99,105,110)
        else:
            col = colors[i]
        outline = (0,0,0) if theme != "bright" else (244,244,244)
        d.text((x,y),text,font=f,fill=col,stroke_width=2 if effect=="outline" else 0,
               stroke_fill=outline)
    if effect=="blur":
        base = base.filter(ImageFilter.GaussianBlur(1.15))
    if effect=="tilt":
        base = base.rotate(3,Image.Resampling.BILINEAR,expand=False,fillcolor=(20,28,43))
    target = out / (name+".png")
    base.save(target)
    cases[target.name] = texts

(out/"truth.json").write_text(json.dumps(cases,indent=2,ensure_ascii=False),encoding="utf-8")
print("images",len(cases),"labels",sum(map(len,cases.values())), "destination",out)
