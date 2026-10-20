#!/usr/bin/env python3
"""Synthetic rotated UI line; Pillow is already installed, no downloads."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
target=Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR/benchmarks/rotated_12deg.png")
base=Image.new("RGB",(960,540),(20,28,43))
font="/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
if not Path(font).exists():font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f=ImageFont.truetype(font,48)
layer=Image.new("RGBA",(720,120),(0,0,0,0))
pen=ImageDraw.Draw(layer)
pen.text((25,15),"Görev tamamlandı!",font=f,fill=(255,255,255,255),stroke_width=2,stroke_fill=(0,0,0,255))
rotated=layer.rotate(-12,resample=Image.Resampling.BICUBIC,expand=True)
base.paste(rotated,(74,180),rotated)
base.save(target)
print(target,target.stat().st_size)
