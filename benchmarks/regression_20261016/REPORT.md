# OCR Optimization Regression Audit — 16 October 2026

Both modes use the same GameTranslatorOCR enhanced hybrid model, with 6 CPU threads.
Normal detector long side = 960 px. Fast detector long side = 864 px.
Original 21 images were used during optimization; **independent_stress** (14 new images) was created only afterward.
Each image is evaluated in two passes, exact text and all extraneous detections count against the score.
Character accuracy = 1 - Levenshtein distance of normalized concatenated texts / reference characters.
Case folded and Unicode NFKC normalized; accents like ş/s or ı/i remain distinct.

| Dataset | Profile | Exact lines | Character accuracy | F1 | Mean | p95 | Peak RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| development | normal | 66/66 | 100.0% | 100.0% | 191.5ms | 222.2ms | 457.0 MiB |
| development | fast | 66/66 | 100.0% | 100.0% | 155.8ms | 178.5ms | 370.3 MiB |
| holdout | normal | 60/60 | 100.0% | 100.0% | 182.3ms | 201.9ms | 412.5 MiB |
| holdout | fast | 60/60 | 100.0% | 100.0% | 146.3ms | 167.1ms | 360.6 MiB |
| independent_stress | normal | 78/84 | 99.5% | 92.86% | 197.8ms | 234.9ms | 462.0 MiB |
| independent_stress | fast | 78/84 | 99.5% | 92.86% | 164.5ms | 201.2ms | 409.8 MiB |

## Differences and failures
- **development:** exact lines Δ 0, char accuracy Δ 0.0pp, mean latency 18.6% faster
- **holdout:** exact lines Δ 0, char accuracy Δ 0.0pp, mean latency 19.7% faster
- **independent_stress:** exact lines Δ 0, char accuracy Δ 0.0pp, mean latency 16.8% faster
  - normal S03_bright_settings.png pass=0: 2/3, truth=['Görüntü ayarları', 'Ekran çözünürlüğü', 'Değişiklikleri kaydet'], got=['Görüntü ayarları', 'Ekran çözünürlügü', 'Değişiklikleri kaydet']
  - normal S03_bright_settings.png pass=1: 2/3, truth=['Görüntü ayarları', 'Ekran çözünürlüğü', 'Değişiklikleri kaydet'], got=['Görüntü ayarları', 'Ekran çözünürlügü', 'Değişiklikleri kaydet']
  - normal S08_slightly_rotated.png pass=0: 2/3, truth=['Kapıya doğru ilerle', 'Üçüncü bölüm başladı', 'Victory is near'], got=['Kapıya doğru ilerle', 'Üçünců bölüm başladı', 'Victory is near']
  - normal S08_slightly_rotated.png pass=1: 2/3, truth=['Kapıya doğru ilerle', 'Üçüncü bölüm başladı', 'Victory is near'], got=['Kapıya doğru ilerle', 'Üçünců bölüm başladı', 'Victory is near']
  - normal S10_low_contrast.png pass=0: 2/3, truth=['Sığınağa geri dön', 'Haritayı kontrol et', 'Gösterge açık'], got=['Siğinağa geri dön', 'Haritayı kontrol et', 'Gösterge açık']
  - normal S10_low_contrast.png pass=1: 2/3, truth=['Sığınağa geri dön', 'Haritayı kontrol et', 'Gösterge açık'], got=['Siğinağa geri dön', 'Haritayı kontrol et', 'Gösterge açık']
  - fast S06_color_hud.png pass=0: 2/3, truth=['Can seviyesi 100', 'Zırh kapasitesi 45', 'Yeni yetenek açıldı'], got=['Can seviyesi 100', 'Zırh kapašitesi 45', 'Yeni yetenek açıldı']
  - fast S06_color_hud.png pass=1: 2/3, truth=['Can seviyesi 100', 'Zırh kapasitesi 45', 'Yeni yetenek açıldı'], got=['Can seviyesi 100', 'Zırh kapašitesi 45', 'Yeni yetenek açıldı']
  - fast S09_small_resolution.png pass=0: 2/3, truth=['Çevrimdışı mod', 'Bir sonraki kayıt', 'Hikâyeye devam et'], got=['Çevrimdıșı mod', 'Bir sonraki kayıt', 'Hikâyeye devam et']
  - fast S09_small_resolution.png pass=1: 2/3, truth=['Çevrimdışı mod', 'Bir sonraki kayıt', 'Hikâyeye devam et'], got=['Çevrimdıșı mod', 'Bir sonraki kayıt', 'Hikâyeye devam et']
  - fast S10_low_contrast.png pass=0: 2/3, truth=['Sığınağa geri dön', 'Haritayı kontrol et', 'Gösterge açık'], got=['Siğinağa geri dön', 'Haritayı kontrol et', 'Gösterge açık']
  - fast S10_low_contrast.png pass=1: 2/3, truth=['Sığınağa geri dön', 'Haritayı kontrol et', 'Gösterge açık'], got=['Siğinağa geri dön', 'Haritayı kontrol et', 'Gösterge açık']

## Limitations
- Both original and newly generated cases are **synthetic** game UI screenshots, not real games.
- The 14 independent cases are a post-hoc stress set and were not used to pick 864px.
- Average speed from two sequential batches can be affected by thermal/frequency variation.
- RSS measures the whole .NET process; model memory alone is not isolated.
- No GPU, Windows execution, native game screenshot collection, or translation overlay tested.
- A clean result on these sets is not a guarantee that quality never degrades in any game.
