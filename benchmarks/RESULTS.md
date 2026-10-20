# Yerel OCR Karşılaştırması (ek indirme yapılmadan)

## Test kapsamı
- Fedora Linux, **mevcut yüklü motorlar ve mevcut yerel modeller**; internetten indirme/kurulum yapılmadı.
- **11 sentetik oyun-arayüzü görseli, 33 gerçek metin satırı**. Gerçek oyun görüntüsü değildir.
- Tüm motorlarda CPU, aynı görüntüler. İlk model ısınması hariç, her görüntü için 2 koşum.
- GameTranslatorOCR ve RapidOCR matched aynı PP-OCRv5 detector + Latin recognizer ağırlıklarını kullanır; postprocess farklı.
- RapidOCR default zaten kurulu PP-OCRv6 det/rec kullanır; model versiyonu farklıdır.
- Tesseract komut satırı başlatma maliyeti ölçüme dahil, diğerlerinde model bir kere yüklenmiştir. Hız eşit yöntemle ölçülmüş sayılamaz.
- Puan = **%70 karakter doğruluğu + %20 tamamen doğru satır oranı + %10 en hızlı motora göre hız puanı**.
- Büyük/küçük harf farkı göz ardı edilir; Türkçe harfler ve noktalama değerlendirmeye dahildir.
- Az sayıda sentetik örnekten genellenebilir OCR yüzdesi veya üstünlük çıkarılamaz.

## Skor tablosu

| Sıra | Motor | Karakter doğruluğu | Tam satır | Ortalama CPU | p95 | Skor |
|---:|---|---:|---:|---:|---:|---:|
| 1 | GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#) | %99.82 | 32/33 | 210.7 ms | 237.5 ms | **98.2/100** |
| 2 | Tesseract 5.5.3 (eng+turk, PSM 11) | %98.35 | 29/33 | 200.0 ms | 213.0 ms | **95.9/100** |
| 3 | RapidOCR (hazır PP-OCRv6 modelleri) | %99.63 | 31/33 | 328.7 ms | 352.3 ms | **94.3/100** |
| 4 | GameTranslatorOCR (v5 modeller + 6px crop, C#) | %97.07 | 25/33 | 189.2 ms | 211.0 ms | **93.1/100** |
| 5 | GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#) | %96.89 | 26/33 | 239.4 ms | 285.3 ms | **91.5/100** |
| 6 | GameTranslatorOCR (PP-OCRv5 Latin, C#) | %95.60 | 23/33 | 212.0 ms | 242.3 ms | **89.8/100** |
| 7 | GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#) | %96.34 | 24/33 | 245.2 ms | 288.4 ms | **89.7/100** |
| 8 | RapidOCR (aynı PP-OCRv5 Latin modelleri) | %97.25 | 15/33 | 412.8 ms | 460.0 ms | **81.7/100** |

## Görsel bazında hatalar

| Görsel | GameTranslatorOCR (game_hybrid_tuned) | Tesseract 5.5.3 (tesseract) | RapidOCR (rapid_default) | GameTranslatorOCR (game_tuned) | GameTranslatorOCR (game_hybrid) | GameTranslatorOCR (game) | GameTranslatorOCR (game_v6) | RapidOCR (rapid_matched) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 00_baseline.png | %100 | %98 | %100 | %100 | %100 | %100 | %98 | %100 |
| 01_dark_dialogue.png | %100 | %100 | %100 | %98 | %95 | %97 | %98 | %98 |
| 02_small_hud.png | %100 | %100 | %100 | %100 | %100 | %100 | %95 | %100 |
| 03_outline_shadow.png | %100 | %100 | %100 | %97 | %91 | %95 | %90 | %97 |
| 04_bright_menu.png | %100 | %83 | %100 | %88 | %96 | %83 | %100 | %92 |
| 05_blurred_subtitles.png | %100 | %100 | %100 | %92 | %94 | %92 | %96 | %94 |
| 06_low_contrast.png | %100 | %100 | %98 | %96 | %94 | %92 | %96 | %96 |
| 07_busy_background.png | %98 | %96 | %98 | %96 | %96 | %96 | %96 | %96 |
| 08_tilted_screen.png | %100 | %96 | %100 | %100 | %100 | %100 | %100 | %100 |
| 09_wide_720p.png | %100 | %100 | %100 | %100 | %100 | %98 | %98 | %100 |
| 10_colored_ui.png | %100 | %100 | %100 | %96 | %100 | %93 | %95 | %95 |

## Okunan metinler (her motorun ilk koşumu)

### 00_baseline.png
- Doğrusu: ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['GAME TRANSLATOR OCR', 'Merhaba dunya!', 'Quest completed']
- RapidOCR (hazır PP-OCRv6 modelleri): ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['GAME TRANSLATOR OCR', 'Merhaba dunya!', 'Quest completed']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']
### 01_dark_dialogue.png
- Doğrusu: ['Open the ancient gate', 'Görev tamamlandı', 'Press E to continue']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Open the ancient gate', 'Görev tamamlandı', 'Press E to continue']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Open the ancient gate', 'Görev tamamlandı', 'Press E to continue']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Open the ancient gate', 'Görev tamamlandı', 'Press E to continue']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Open the ancient gate', 'Görev tamamlandi', 'Press E to continue']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['Open the ancient gate', 'Gorey tamamlandl', 'Press E to continue']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['Open the ancient gate', 'Gorev tamamlandi', 'Press E to continue']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['Open the ancient gate', 'Görev tamamlandi', 'Press E to continue']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Open', 'the', 'ancient', 'gate', 'Görev', 'tamamlandi', 'Press', 'E to continue']
### 02_small_hud.png
- Doğrusu: ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- RapidOCR (hazır PP-OCRv6 modelleri): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['LEVEL 27', 'Health 100%', '_', 'Kalan süre 02:45']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['LEVEL 27', 'Health 100%', 'Kalan süre 02:45']
### 03_outline_shadow.png
- Doğrusu: ['Düşman yaklaşıyor!', 'Run to the bridge', 'Bölüm başarıyla bitti']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Düşman yaklaşıyor!', 'Run to the bridge', 'Bölüm başarıyla bitti']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Düşman yaklaşıyor!', 'Run to the bridge', 'Bölüm başarıyla bitti']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Düşman yaklaşıyor!', 'Run to the bridge', 'Bölüm başarıyla bitti']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Düşman yaklaşiyor!', 'Run to the bridge', 'Bölüm başariyla bitti']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['Dusman yaklasiyor!', 'Run to the bridge', 'Bölüm başariyla bitti']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['Duşman yaklaşiyor!', 'Run to the bridge', 'Bölüm başariyla bitti']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['Düsman vaklasiyor!', 'Run to the bridge', 'Bölüm basariyla bitti']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Düşman', 'yaklaşiyor!', 'Run to', 'the', 'bridge', 'Bölüm', 'başariyla', 'bitti']
### 04_bright_menu.png
- Doğrusu: ['Settings', 'Yeni oyun', 'Çıkış']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Settings', 'Yeni oyun', 'Çıkış']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Settings', 'Yeni oyun', 'Cikis']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Settings', 'Yeni oyun', 'Çıkış']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Settings', 'Yeni oyun', 'Cikiş']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['Settings', 'Yeni oyun', 'Çikış']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['Settings', 'Yeni oyun', 'CikiS']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['Settings', 'Yeni oyun', 'Çıkış']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Settings', 'Yeni oyun', 'Çikiş']
### 05_blurred_subtitles.png
- Doğrusu: ['Can you hear me?', 'Kapıyı açmalıyız', 'Follow the signal']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Can you hear me?', 'Kapıyı açmalıyız', 'Follow the signal']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Can you hear me?', 'Kapıyı açmalıyız', 'Follow the signal']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Can you hear me?', 'Kapıyı açmalıyız', 'Follow the signal']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Can you hear me?', 'Kapiyi açmaliyiz', 'Follow the signal']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['Can you hear me?', 'Kapiyı açmaliyiz', 'Follow the signal']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['Can you hear me?', 'kapiyi açmaliyiz', 'Follow the signal']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['Can you hear me?', 'Kapiyı acmalıyız', 'Follow the signal']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Can you', 'hear', 'me?', 'Kapiyı', 'açmaliyiz', 'Follow', 'the', 'signal']
### 06_low_contrast.png
- Doğrusu: ['The mission begins', 'Yeni görev alındı', 'Return to base']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['The mission begins', 'Yeni görev alındı', 'Return to base']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['The mission begins', 'Yeni görev alındı', 'Return to base']
- RapidOCR (hazır PP-OCRv6 modelleri): ['The mission begins', 'Yeni görev alindı', 'Return to base']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['The mission begins', 'Yeni görev alindi', 'Return to base']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['The mission begins', 'Yeni gorev alindi', 'Return to base']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['The mission begins', 'Yeni gorev alindi', 'Return tobase']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['The mission begins', 'Yeni görev alindi', 'Return to base']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['The mission begins', 'Yeni görev alindi', 'Return to base']
### 07_busy_background.png
- Doğrusu: ['Main quest', 'İnceleme tamamlandı', 'Return to the village']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Main quest', 'inceleme tamamlandı', 'Return to the village']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Main quest', 'inceleme tamamlandi', 'Return to the village']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Main quest', 'inceleme tamamlandı', 'Return to the village']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Main quest', 'inceleme tamamlandi', 'Return to the village']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['Main quest', 'Inceleme tamamlandi', 'Return to the village']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['Main quest', 'Inceleme tamamlandi', 'Return to the village']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['Main quest', 'Inceleme tamamlandi', 'Return to the village']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Main quest', 'inceleme tamamlandi', 'Return to the village']
### 08_tilted_screen.png
- Doğrusu: ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Victory is ours', 'Yeni bolge kesfedildi', 'Saving progress']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Victory', 'is ours', 'Yeni', 'bölge', 'keşfedildi', 'Saving', 'progress']
### 09_wide_720p.png
- Doğrusu: ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
- RapidOCR (hazır PP-OCRv6 modelleri): ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['The final chapter', 'Karakter sevivesi 18', 'Continue playing']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['The final chapter', 'Karakter sevivesi 18', 'Continue playing']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['The final chapter', 'Karakter seviyesi 18', 'Continue playing']
### 10_colored_ui.png
- Doğrusu: ['New achievement', 'Başarı kilidi açıldı', 'Collect your reward']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['New achievement', 'Başarı kilidi açıldı', 'Collect your reward']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['New achievement', 'Başarı kilidi açıldı', 'Collect your reward']
- RapidOCR (hazır PP-OCRv6 modelleri): ['New achievement', 'Başarı kilidi açıldı', 'Collect your reward']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['New achievement', 'Başari kilidi açıldi', 'Collect your reward']
- GameTranslatorOCR (PP-OCRv5 det + v6 rec, C#): ['New achievement', 'Başarı kilidi açıldı', 'Collect your reward']
- GameTranslatorOCR (PP-OCRv5 Latin, C#): ['New achievement', 'Başari killidi açildi', 'Collect your reward']
- GameTranslatorOCR (yerel PP-OCRv6 det + rec, C#): ['New achievement', 'Basarı kilidi acildı', 'Collect your reward']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['New', 'achievement', 'Başari', 'kilidi', 'açildi', 'Collect', 'your', 'reward']

## Kısıtlar
- Tesseract'ın PSM 11 modu tek seçilmiş ayardır, farklı PSM ile sonuçları değişebilir.
- Bu skor overlay, frame tracking, GPU desteği, dil çeşitliliği, paket boyutu veya lisansı puanlamıyor.
- Rakip motorları indirmemek için EasyOCR/PaddleOCR kurulmadı, dolayısıyla ölçüm skoru yok.
- Skor bir **yerel sentetik test** skorudur; GameTranslatorOCR'a otomatik liderlik anlamına gelmez.
