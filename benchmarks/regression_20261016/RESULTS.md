# Yerel OCR Karşılaştırması (ek indirme yapılmadan)

## Test kapsamı
- Fedora Linux, **mevcut yüklü motorlar ve mevcut yerel modeller**; internetten indirme/kurulum yapılmadı.
- **14 sentetik oyun-arayüzü görseli, 42 gerçek metin satırı**. Gerçek oyun görüntüsü değildir.
- Tüm motorlarda CPU, aynı görüntüler. İlk model ısınması hariç, her görüntü için 2 koşum.
- Sadece GameTranslatorOCR v5 original/tuned ile RapidOCR matched aynı PP-OCRv5 detector + Latin recognizer modellerini kullanır; hibrit sürüm v6 tanıyıcı kullanır, dolayısıyla model eşitliği yoktur.
- RapidOCR default zaten kurulu PP-OCRv6 det/rec kullanır; model versiyonu farklıdır.
- Tesseract komut satırı başlatma maliyeti ölçüme dahil, diğerlerinde model bir kere yüklenmiştir. Hız eşit yöntemle ölçülmüş sayılamaz.
- Puan = **%70 karakter doğruluğu + %20 tamamen doğru satır oranı + %10 en hızlı motora göre hız puanı**.
- Büyük/küçük harf farkı göz ardı edilir; Türkçe harfler ve noktalama değerlendirmeye dahildir.
- Az sayıda sentetik örnekten genellenebilir OCR yüzdesi veya üstünlük çıkarılamaz.

## Skor tablosu

| Sıra | Motor | Karakter doğruluğu | Tam satır | Ortalama CPU | p95 | Skor |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Tesseract 5.5.3 (eng+turk, PSM 11) | %97.78 | 34/42 | 206.8 ms | 228.4 ms | **94.6/100** |
| 2 | RapidOCR (hazır PP-OCRv6 modelleri) | %97.16 | 40/42 | 345.8 ms | 467.5 ms | **93.0/100** |

## Görsel bazında hatalar

| Görsel | Tesseract 5.5.3 (tesseract) | RapidOCR (rapid_default) |
|---|---:|---:|
| S00_dialogue_turkish.png | %100 | %100 |
| S01_english_subtitles.png | %100 | %100 |
| S02_tiny_inventory.png | %95 | %94 |
| S03_bright_settings.png | %100 | %100 |
| S04_orange_quest.png | %92 | %100 |
| S05_contrasty_dark.png | %100 | %98 |
| S06_color_hud.png | %93 | %84 |
| S07_soft_subtitle.png | %100 | %98 |
| S08_slightly_rotated.png | %100 | %100 |
| S09_small_resolution.png | %96 | %100 |
| S10_low_contrast.png | %92 | %100 |
| S11_wide_menu.png | %100 | %100 |
| S12_outlined_subtitles.png | %100 | %100 |
| S13_thin_font_ui.png | %100 | %85 |

## Okunan metinler (her motorun ilk koşumu)

### S00_dialogue_turkish.png
- Doğrusu: ['Şehrin kapıları açıldı', 'Işıklar yeniden yanıyor', 'Bütün görevler tamamlandı']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Şehrin kapıları açıldı', 'Işıklar yeniden yanıyor', 'Bütün görevler tamamlandı']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Şehrin kapıları açıldı', 'Işıklar yeniden yanıyor', 'Bütün görevler tamamlandı']
### S01_english_subtitles.png
- Doğrusu: ['Return to the shelter', 'Follow the glowing trail', 'The journey continues']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Return to the shelter', 'Follow the glowing trail', 'The journey continues']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Return to the shelter', 'Follow the glowing trail', 'The journey continues']
### S02_tiny_inventory.png
- Doğrusu: ['Gümüş anahtar bulundu', 'Kılıç dayanıklılığı 70', 'Press F to inspect']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Gumus anahtar bulundu', 'Kılıç dayanıklılığı 70', 'Press F to inspect']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Gümüş anahtar bulundu', '□', 'Kılıç dayanıklılığı 70', 'Press F to inspect', '口']
### S03_bright_settings.png
- Doğrusu: ['Görüntü ayarları', 'Ekran çözünürlüğü', 'Değişiklikleri kaydet']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Görüntü ayarları', 'Ekran çözünürlüğü', 'Değişiklikleri kaydet']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Görüntü ayarları', 'Ekran çözünürlüğü', 'Değişiklikleri kaydet']
### S04_orange_quest.png
- Doğrusu: ['Yeni hedef belirlendi', 'Düşmanı etkisiz hale getir', 'Görev güncellendi']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Yeni hedef belirlendi', 'Dusmani etkisiz hale getir', 'Gorev guncellendi']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Yeni hedef belirlendi', 'Düşmanı etkisiz hale getir', 'Görev güncellendi']
### S05_contrasty_dark.png
- Doğrusu: ['İlk bölüm başlıyor', 'Şimdi gizlenmeliyiz', 'Stay near the river']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['İlk bölüm başlıyor', 'Şimdi gizlenmeliyiz', 'Stay near the river']
- RapidOCR (hazır PP-OCRv6 modelleri): ['ilk bölüm başlıyor', 'Şimdi gizlenmeliyiz', 'Stay near the river']
### S06_color_hud.png
- Doğrusu: ['Can seviyesi 100', 'Zırh kapasitesi 45', 'Yeni yetenek açıldı']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Can seviyesi 100', 'Zirh kapasitesi 45', 'Yeni yetenek acildi']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Can seviyesi 100', '_', '_', 'Zırh kapasitesi 45', 'Yeni yetenek açıldı', '__', '□']
### S07_soft_subtitle.png
- Doğrusu: ['Köprüden karşıya geç', 'İleride bir çıkış var', "Don't look behind"]
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Köprüden karşıya geç', 'İleride bir çıkış var', "Don't look behind"]
- RapidOCR (hazır PP-OCRv6 modelleri): ['Köprüden karşıya geç', 'ileride bir çıkış var', "Don't look behind"]
### S08_slightly_rotated.png
- Doğrusu: ['Kapıya doğru ilerle', 'Üçüncü bölüm başladı', 'Victory is near']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Kapıya doğru ilerle', 'Üçüncü bölüm başladı', 'Victory is near']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Kapıya doğru ilerle', 'Üçüncü bölüm başladı', 'Victory is near']
### S09_small_resolution.png
- Doğrusu: ['Çevrimdışı mod', 'Bir sonraki kayıt', 'Hikâyeye devam et']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Çevrimdışı mod', 'Bir sonraki kayit', 'Hikayeye devam et']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Çevrimdışı mod', 'Bir sonraki kayıt', 'Hikâyeye devam et']
### S10_low_contrast.png
- Doğrusu: ['Sığınağa geri dön', 'Haritayı kontrol et', 'Gösterge açık']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Siginaga geri dön', 'Haritayı kontrol et', 'Gösterge açık']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Sığınağa geri dön', 'Haritayı kontrol et', 'Gösterge açık']
### S11_wide_menu.png
- Doğrusu: ['Kayıtlı oyunlar', 'Başarılar listesi', 'Ana menüye dön']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Kayıtlı oyunlar', 'Başarılar listesi', 'Ana menüye dön']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Kayıtlı oyunlar', 'Başarılar listesi', 'Ana menüye dön']
### S12_outlined_subtitles.png
- Doğrusu: ['Şüpheli bir ses var', 'Hızlı koşmalıyız', 'Hedefe ulaştık']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Şüpheli bir ses var', 'Hızlı koşmalıyız', 'Hedefe ulaştık']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Şüpheli bir ses var', 'Hızlı koşmalıyız', 'Hedefe ulaştık']
### S13_thin_font_ui.png
- Doğrusu: ['Ödülleri topla', 'Köyün etrafını dolaş', 'Choose your weapon']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Ödülleri topla', 'Köyün etrafını dolaş', 'Choose your weapon']
- RapidOCR (hazır PP-OCRv6 modelleri): ['□', 'Ödülleri topla', '□', '□', 'Köyün etrafını dolaş', '□', 'Choose your weapon']

## Kısıtlar
- Tesseract'ın PSM 11 modu tek seçilmiş ayardır, farklı PSM ile sonuçları değişebilir.
- Bu skor overlay, frame tracking, GPU desteği, dil çeşitliliği, paket boyutu veya lisansı puanlamıyor.
- Rakip motorları indirmemek için EasyOCR/PaddleOCR kurulmadı, dolayısıyla ölçüm skoru yok.
- Skor bir **yerel sentetik test** skorudur; GameTranslatorOCR'a otomatik liderlik anlamına gelmez.
