from pathlib import Path
from PIL import Image,ImageEnhance,ImageOps,ImageFilter
r=Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR")
src=r/"benchmarks/independent_stress/S10_low_contrast.png"
dst=r/"benchmarks/quality_retry/contrast_probe"
dst.mkdir(parents=True,exist_ok=True)
im=Image.open(src).convert("RGB")
for f in (1.0,1.2,1.4,1.7,2.0,2.5,3.0):
    ImageEnhance.Contrast(im).enhance(f).save(dst/f"contrast_{f:.1f}.png")
for f in (.7,.85,1.15,1.3):
    ImageEnhance.Brightness(im).enhance(f).save(dst/f"brightness_{f:.2f}.png")
ImageOps.autocontrast(im,cutoff=1).save(dst/"autocontrast.png")
print("wrote",len(list(dst.glob("*.png"))),"variants")
