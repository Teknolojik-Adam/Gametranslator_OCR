# GameTranslatorOCR vs Tesseract 5.5.3 — Linux CPU benchmark

16 Ekim 2026; kurulu modeller, sıfır indirme.
11 sentetik görüntü/33 satır (ilk set), 10 bağımsız sentetik görüntü/30 satır (ikinci set). Her görüntü üzerinde test iki kez tekrarlandı.
GameTranslatorOCR: C# ONNX PP-OCRv5 detector + yerel PP-OCRv6 recognizer. Gelişmiş profil: --enhanced.
Tesseract: kurulu eng+turk traineddata, libtesseract yeniden başlatılmadan PSM11/6/3 modlarında ve ayrı CLI denemesi.

| Set | Motor | Karakter doğruluğu | Tam satır | Satır F1 | Ortalama | p95 | Tepe RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| development | game_default | 100.00% | 33/33 | 100.00% | 209.2 ms | 239.9 ms | 397.1 MiB |
| development | game_enhanced | 100.00% | 33/33 | 100.00% | 208.3 ms | 247.0 ms | 440.8 MiB |
| development | tess_psm11 | 98.53% | 29/33 | 87.88% | 62.1 ms | 76.6 ms | 104.1 MiB |
| development | tess_psm6 | 98.53% | 29/33 | 87.88% | 60.5 ms | 74.5 ms | 104.6 MiB |
| development | tess_psm3 | 98.53% | 29/33 | 87.88% | 62.6 ms | 76.6 ms | 105.0 MiB |
| development | tess_cli11 | 98.53% | 29/33 | 87.88% | 195.6 ms | 210.7 ms | -- |
| holdout | game_default | 98.14% | 30/30 | 93.75% | 203.3 ms | 229.3 ms | 388.7 MiB |
| holdout | game_enhanced | 100.00% | 30/30 | 100.00% | 201.9 ms | 224.9 ms | 417.2 MiB |
| holdout | tess_psm11 | 95.82% | 24/30 | 80.00% | 57.3 ms | 71.7 ms | 105.8 MiB |
| holdout | tess_psm6 | 94.66% | 22/30 | 73.33% | 52.6 ms | 67.1 ms | 105.4 MiB |
| holdout | tess_psm3 | 95.82% | 24/30 | 80.00% | 57.3 ms | 71.2 ms | 105.7 MiB |
| holdout | tess_cli11 | 95.82% | 24/30 | 80.00% | 193.4 ms | 210.9 ms | -- |

## Nasıl ölçüldü?
- Karakter doğruluğu: Unicode NFKC + büyük/küçük harf yok sayıldı; Tüm OCR çıktısı satır sırasına göre birleştirildi ve Levenshtein edit mesafesi hesaplandı. Fazladan üretilen metinler ve hatalı karakterler doğruluk hesaplamasına dahil edildi.
- Tam doğru satır: bir OCR sonuç satırı, bir referans satırıyla birebir eşleşti. Satır F1 hesabında fazladan tespit edilen satırlar da dikkate alınır.
- Tesseract API testi: kurulu libtesseract tek kere başlatıldı, Pillow RGB conversion önceden yapıldı; SetImage+GetUTF8Text ölçüme dahil.
- GameTranslatorOCR: model oturumu başlangıcı hariç, RecognizeAsync (PNG decode dahil) süreleri ölçüldü.
- Tesseract CLI: her görüntüde ayrı proses başlar ve traineddata yeniden yüklenir; önceden başlatılmış API testiyle doğrudan karşılaştırılabilir bir hız sonucu değildir.
- Bellek: GameTranslatorOCR .NET prosesi peak RSS; Tesseract için yeniden başlatılmadan çalışan Python+libtesseract işleminin en yüksek bellek kullanımı. Framework/buffer farkı vardır.
- Tüm denemeler CPU'da ve sentetik veridedir. Gerçek oyun ekranında, Windows/GPU'da aynı sonuç garantisi yok.
- Tesseract PSM11 sparse text, PSM6 block, PSM3 auto layout stratejileridir.

## Başarısız/göze çarpan örnekler
### development - game_default (0 hata içeren görsel)
### development - game_enhanced (0 hata içeren görsel)
### development - tess_psm11 (4 hata içeren görsel)
- 00_baseline.png: gerçek ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']; okunan ['GAME TRANSLATOR OCR', 'Merhaba dunya!', 'Quest completed']
- 04_bright_menu.png: gerçek ['Settings', 'Yeni oyun', 'Çıkış']; okunan ['Settings', 'Yeni oyun', 'Cikis']
- 07_busy_background.png: gerçek ['Main quest', 'İnceleme tamamlandı', 'Return to the village']; okunan ['Main quest', 'inceleme tamamlandi', 'Return to the village']
- 08_tilted_screen.png: gerçek ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']; okunan ['Victory is ours', 'Yeni bolge kesfedildi', 'Saving progress']
### development - tess_psm6 (4 hata içeren görsel)
- 00_baseline.png: gerçek ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']; okunan ['GAME TRANSLATOR OCR', 'Merhaba dunya!', 'Quest completed']
- 04_bright_menu.png: gerçek ['Settings', 'Yeni oyun', 'Çıkış']; okunan ['Settings', 'Yeni oyun', 'Cikis']
- 07_busy_background.png: gerçek ['Main quest', 'İnceleme tamamlandı', 'Return to the village']; okunan ['Main quest', 'inceleme tamamlandi', 'Return to the village']
- 08_tilted_screen.png: gerçek ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']; okunan ['Victory is ours', 'Yeni bolge kesfedildi', 'Saving progress']
### development - tess_psm3 (4 hata içeren görsel)
- 00_baseline.png: gerçek ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']; okunan ['GAME TRANSLATOR OCR', 'Merhaba dunya!', 'Quest completed']
- 04_bright_menu.png: gerçek ['Settings', 'Yeni oyun', 'Çıkış']; okunan ['Settings', 'Yeni oyun', 'Cikis']
- 07_busy_background.png: gerçek ['Main quest', 'İnceleme tamamlandı', 'Return to the village']; okunan ['Main quest', 'inceleme tamamlandi', 'Return to the village']
- 08_tilted_screen.png: gerçek ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']; okunan ['Victory is ours', 'Yeni bolge kesfedildi', 'Saving progress']
### development - tess_cli11 (4 hata içeren görsel)
- 00_baseline.png: gerçek ['GAME TRANSLATOR OCR', 'Merhaba dünya!', 'Quest completed']; okunan ['GAME TRANSLATOR OCR', 'Merhaba dunya!', 'Quest completed']
- 04_bright_menu.png: gerçek ['Settings', 'Yeni oyun', 'Çıkış']; okunan ['Settings', 'Yeni oyun', 'Cikis']
- 07_busy_background.png: gerçek ['Main quest', 'İnceleme tamamlandı', 'Return to the village']; okunan ['Main quest', 'inceleme tamamlandi', 'Return to the village']
- 08_tilted_screen.png: gerçek ['Victory is ours', 'Yeni bölge keşfedildi', 'Saving progress']; okunan ['Victory is ours', 'Yeni bolge kesfedildi', 'Saving progress']
### holdout - game_default (0 hata içeren görsel)
### holdout - game_enhanced (0 hata içeren görsel)
### holdout - tess_psm11 (4 hata içeren görsel)
- H00_unseen.png: gerçek ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']; okunan ['Find the hidden key', 'Gorusuruz', 'Hızlı seyahat']
- H02_unseen.png: gerçek ['Şifre yanlış', 'Enemy spotted', 'Target acquired']; okunan ['Şifre yanlış', 'Enemy spotted', 'Target acguired']
- H07_unseen.png: gerçek ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']; okunan ['Cikisa ilerle', 'Find the map', 'Kopruye geri don']
- H09_unseen.png: gerçek ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']; okunan ['Ogrenci girisi', 'Yolculuk basliyor', 'Use magic']
### holdout - tess_psm6 (5 hata içeren görsel)
- H00_unseen.png: gerçek ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']; okunan ['Find the hidden key', 'Gorusuruz', 'Hızlı seyahat']
- H02_unseen.png: gerçek ['Şifre yanlış', 'Enemy spotted', 'Target acquired']; okunan ['Şifre yanlış', 'Enemy spotted', 'Target acguired']
- H03_unseen.png: gerçek ['Büyük ödül', 'Seviye yükseldi', 'Continue']; okunan ['Buyuk odul', 'Seviye yukseldi', 'Continue']
- H07_unseen.png: gerçek ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']; okunan ['Cikisa ilerle', 'Find the map', 'Kopruye geri don']
- H09_unseen.png: gerçek ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']; okunan ['Ogrenci girisi', 'Yolculuk basliyor', 'Use magic']
### holdout - tess_psm3 (4 hata içeren görsel)
- H00_unseen.png: gerçek ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']; okunan ['Find the hidden key', 'Gorusuruz', 'Hızlı seyahat']
- H02_unseen.png: gerçek ['Şifre yanlış', 'Enemy spotted', 'Target acquired']; okunan ['Şifre yanlış', 'Enemy spotted', 'Target acguired']
- H07_unseen.png: gerçek ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']; okunan ['Cikisa ilerle', 'Find the map', 'Kopruye geri don']
- H09_unseen.png: gerçek ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']; okunan ['Ogrenci girisi', 'Yolculuk basliyor', 'Use magic']
### holdout - tess_cli11 (4 hata içeren görsel)
- H00_unseen.png: gerçek ['Find the hidden key', 'Görüşürüz', 'Hızlı seyahat']; okunan ['Find the hidden key', 'Gorusuruz', 'Hızlı seyahat']
- H02_unseen.png: gerçek ['Şifre yanlış', 'Enemy spotted', 'Target acquired']; okunan ['Şifre yanlış', 'Enemy spotted', 'Target acguired']
- H07_unseen.png: gerçek ['Çıkışa ilerle', 'Find the map', 'Köprüye geri dön']; okunan ['Cikisa ilerle', 'Find the map', 'Kopruye geri don']
- H09_unseen.png: gerçek ['Öğrenci girişi', 'Yolculuk başlıyor', 'Use magic']; okunan ['Ogrenci girisi', 'Yolculuk basliyor', 'Use magic']
