# Yerel OCR Karşılaştırması (ek indirme yapılmadan)

## Test kapsamı
- Fedora Linux, **mevcut yüklü motorlar ve mevcut yerel modeller**; internetten indirme/kurulum yapılmadı.
- **10 sentetik oyun-arayüzü görseli, 30 gerçek metin satırı**. Gerçek oyun görüntüsü değildir.
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
| 1 | GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#) | %97.92 | 29/30 | 198.6 ms | 225.8 ms | **97.2/100** |
| 2 | Tesseract 5.5.3 (eng+turk, PSM 11) | %95.83 | 24/30 | 191.6 ms | 205.5 ms | **92.7/100** |
| 3 | GameTranslatorOCR (v5 modeller + 6px crop, C#) | %94.44 | 19/30 | 184.3 ms | 208.6 ms | **88.8/100** |
| 4 | RapidOCR (hazır PP-OCRv6 modelleri) | %90.05 | 29/30 | 358.1 ms | 576.5 ms | **87.5/100** |
| 5 | RapidOCR (aynı PP-OCRv5 Latin modelleri) | %96.99 | 13/30 | 390.1 ms | 448.4 ms | **81.3/100** |

## Görsel bazında hatalar

| Görsel | GameTranslatorOCR (game_hybrid_tuned) | Tesseract 5.5.3 (tesseract) | GameTranslatorOCR (game_tuned) | RapidOCR (rapid_default) | RapidOCR (rapid_matched) |
|---|---:|---:|---:|---:|---:|
| H00_unseen.png | %100 | %88 | %95 | %100 | %95 |
| H01_unseen.png | %83 | %100 | %78 | %22 | %97 |
| H02_unseen.png | %100 | %98 | %98 | %100 | %98 |
| H03_unseen.png | %100 | %100 | %100 | %100 | %100 |
| H04_unseen.png | %100 | %100 | %96 | %100 | %96 |
| H05_unseen.png | %98 | %100 | %98 | %98 | %98 |
| H06_unseen.png | %96 | %100 | %91 | %70 | %96 |
| H07_unseen.png | %100 | %84 | %95 | %100 | %95 |
| H08_unseen.png | %100 | %100 | %94 | %100 | %98 |
| H09_unseen.png | %100 | %88 | %98 | %100 | %98 |

## Okunan metinler (her motorun ilk koşumu)

### H00_unseen.png
- Doğrusu: ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Find the hidden key', 'Gorusuruz', 'Hızlı seyahat']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Find the hidden key', 'Görüşürüz', 'Hizli seyahat']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Find', 'the', 'hidden', 'key', 'Görüşürüz', 'Hizli', 'seyahat']
### H01_unseen.png
- Doğrusu: ['Işığa doğru', 'Kapı kilitli', 'Run quickly']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['□', 'Işığa doğru', '□', '□', 'Kapı kilitli', 'Run quickly']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Işığa doğru', 'Kapı kilitli', 'Run quickly']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['□', 'Işiğa doğru', '□', '□', 'Kapi kilitli', 'Run quickly']
- RapidOCR (hazır PP-OCRv6 modelleri): ['□', '□', '□', 'Işığa doğru', '□', '□', '□', '□', '□', 'Kapı kilitli', '□', '□', '□', '□', 'Run quickly', '□', '□']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Işığa doğru', 'Kapi kilitli', 'Run quickly']
### H02_unseen.png
- Doğrusu: ['Şifre yanlış', 'Enemy spotted', 'Target acquired']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Şifre yanlış', 'Enemy spotted', 'Target acquired']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Şifre yanlış', 'Enemy spotted', 'Target acguired']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Şifre yanliş', 'Enemy spotted', 'Target acquired']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Şifre yanlış', 'Enemy spotted', 'Target acquired']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Şifre yanliş', 'Enemy spotted', 'Target acquired']
### H03_unseen.png
- Doğrusu: ['Büyük ödül', 'Seviye yükseldi', 'Continue']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Büyük ödül', 'Seviye yükseldi', 'Continue']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Büyük ödül', 'Seviye yükseldi', 'Continue']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Büyük ödül', 'Seviye yükseldi', 'Continue']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Büyük ödül', 'Seviye yükseldi', 'Continue']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Büyük', 'ödül', 'Seviye', 'yükseldi', 'Continue']
### H04_unseen.png
- Doğrusu: ['Kılıç hasar gördü', 'Health restored', 'Görev iptal edildi']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Kılıç hasar gördü', 'Health restored', 'Görev iptal edildi']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Kılıç hasar gördü', 'Health restored', 'Görev iptal edildi']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Kiliç hasar gördü', 'Health restored', 'Görev iptal edildi']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Kılıç hasar gördü', 'Health restored', 'Görev iptal edildi']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Kiliç', 'hasar gördü', 'Health restored', 'Görev', 'iptal edildi']
### H05_unseen.png
- Doğrusu: ['Inventory full', 'Çözüm bulundu', 'İkinci bölüm']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Inventory full', 'Çözüm bulundu', 'ikinci bölüm']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Inventory full', 'Çözüm bulundu', 'İkinci bölüm']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Inventory full', 'Çözüm bulundu', 'ikinci bölüm']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Inventory full', 'Çözüm bulundu', 'ikinci bölüm']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Inventory full', 'Çözüm bulundu', 'ikinci bölüm']
### H06_unseen.png
- Doğrusu: ['Press SPACE', 'Hedefe yaklaşıyoruz', 'Karanlık çöktü']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Press SPACE', 'Hedefe yaklaşıyoruz', 'Karanlık çöktü', '□']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Press SPACE', 'Hedefe yaklaşıyoruz', 'Karanlık çöktü']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Press SPACE', 'Hedefe yaklaşiyoruz', 'Karanlik çöktü', '□']
- RapidOCR (hazır PP-OCRv6 modelleri): ['□', '□', 'Press SPACE', '□', '□', '□', 'Hedefe yaklaşıyoruz', '□', 'Karanlık çöktü', '□']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Press', 'SPACE', 'Hedefe', 'yaklaşiyoruz', 'Karanlik', 'çöktü']
### H07_unseen.png
- Doğrusu: ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Cikisa ilerle', 'Find the map', 'Kopruye geri don']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Çikişa ilerle', 'Find the map', 'Köprüye geri dön']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Çikişa', 'ilerle', 'Find', 'the', 'map', 'Köprüye', 'geri', 'dön']
### H08_unseen.png
- Doğrusu: ['Üçüncü kapı', 'Gizli bölge keşfedildi', 'Mission complete']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Üçüncü kapı', 'Gizli bölge keşfedildi', 'Mission complete']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Üçüncü kapı', 'Gizli bölge keşfedildi', 'Mission complete']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['ςünc kapı', 'Gizli bölge keşfedildi', 'Mission complete']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Üçüncü kapı', 'Gizli bölge keşfedildi', 'Mission complete']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Üςüncü kapı', 'Gizli bölge keşfedildi', 'Mission complete']
### H09_unseen.png
- Doğrusu: ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']
- GameTranslatorOCR (v5 det + yerel v6 rec + 6px, C#): ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']
- Tesseract 5.5.3 (eng+turk, PSM 11): ['Ogrenci girisi', 'Yolculuk basliyor', 'Use magic']
- GameTranslatorOCR (v5 modeller + 6px crop, C#): ['Öğrenci girişi', 'Yolculuk başliyor', 'Use magic']
- RapidOCR (hazır PP-OCRv6 modelleri): ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']
- RapidOCR (aynı PP-OCRv5 Latin modelleri): ['Öğrenci girişi', 'Yolculuk başliyor', 'Use magic']

## Kısıtlar
- Tesseract'ın PSM 11 modu tek seçilmiş ayardır, farklı PSM ile sonuçları değişebilir.
- Bu skor overlay, frame tracking, GPU desteği, dil çeşitliliği, paket boyutu veya lisansı puanlamıyor.
- Rakip motorları indirmemek için EasyOCR/PaddleOCR kurulmadı, dolayısıyla ölçüm skoru yok.
- Skor bir **yerel sentetik test** skorudur; GameTranslatorOCR'a otomatik liderlik anlamına gelmez.
