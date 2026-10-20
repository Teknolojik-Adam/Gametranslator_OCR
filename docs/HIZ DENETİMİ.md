# GameTranslatorOCR — Hızlandırma Sonrası Doğruluk ve Performans Denetimi

**Tarih:** 16 Ekim 2026  
**Sistem:** Fedora Linux CPU, .NET 8, ONNX Runtime, PP-OCRv5 detector + PP-OCRv6 recognizer  
**Karşılaştırma:** `--enhanced` + 960 piksel (normal) ↔ `--enhanced --fast` + 864 piksel (hızlı)  
**Yeni model/yazılım indirmesi:** Yok  
**Kod değişikliği:** Bu turda üretim OCR kodu değiştirilmedi; test altyapısı ve rapor eklendi.

## 1. Ana sonuç

Yeni hızlandırma **toplam satır doğruluğunu düşürmedi**, ancak **bireysel harf ve noktalama hatalarının yeri değişti**. Bu yüzden “her koşulda doğruluğu koruyor” demek doğru olmaz; `--fast` varsayılan yapılmadı ve isteğe bağlı kaldı.

- Hem v5 hem hibrit ONNX model paketiyle otomatik test: **59/59 PASS**.
- İlk 21 sentetik görüntüde toplam 63 referans satırı: her profil 2 turda **126/126 tam doğru satır**.
- İlk kez bu denetimde üretilen **14 yeni bağımsız stres görüntüsü**, 42 satır: iki turda **78/84 tam doğru satır** her iki profilde de.
- Toplam 35 sentetik görüntü, 105 benzersiz satır, 2 tur: her iki profil **204/210** tam doğru satır = **%97,14 tam satır oranı**.
- Yeni stres setinde her iki profil için sıralı metin karakter doğruluğu **%99,50** (NFKC normalizasyonu + büyük/küçük harf duyarsız Levenshtein). Türkçe harf farkları korunmuştur.

## 2. Gerçek yeniden ölçüm

| Set | Normal 960: satır | Hızlı 864: satır | Normal karakter | Hızlı karakter | Normal ortalama | Hızlı ortalama | Normal tepe RSS | Hızlı tepe RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| İlk set — 11 görüntü, 2 tur | 66/66 | 66/66 | %100,00 | %100,00 | 191,5 ms | **155,8 ms** | 457,0 MiB | **370,3 MiB** |
| İkinci set — 10 görüntü, 2 tur | 60/60 | 60/60 | %100,00 | %100,00 | 182,3 ms | **146,3 ms** | 412,5 MiB | **360,6 MiB** |
| Yeni stres — 14 görüntü, 2 tur | 78/84 | 78/84 | %99,50 | %99,50 | 197,8 ms | **164,5 ms** | 462,0 MiB | **409,8 MiB** |

Görüntü sayısına göre ağırlıklandırılmış ortalama süre: normal yaklaşık **191,4 ms**, hızlı yaklaşık **156,6 ms**; hız kazancı yaklaşık **%18,2**. Tekrar sayısı sınırlıdır; bu tahminin istatistiksel güven aralığı hesaplanmadı.

## 3. Görüntü bazında kalite farkları — kritik bulgu

Yeni stres setinde 3 farklı görüntüde, profil başına tek satır hatası bulundu (iki turda tekrarlandı). Ancak bu 3 görüntünün tamamı aynı değildi.

**Normal 960'da hatalı, hızlı 864'te doğru olanlar:**
- `S03_bright_settings.png`: “Ekran çözünürlüğü” → normal “Ekran çözünürlügü”, hızlı doğru.
- `S08_slightly_rotated.png`: “Üçüncü bölüm başladı” → normal “Üçünců bölüm başladı”, hızlı doğru.

**Normal 960'da doğru, hızlı 864'te hatalı olanlar — regresyon:**
- `S06_color_hud.png`: “Zırh kapasitesi 45” → hızlı “Zırh kapašitesi 45”.
- `S09_small_resolution.png`: “Çevrimdışı mod” → hızlı “Çevrimdıșı mod”.

**Her iki profilde hatalı:**
- `S10_low_contrast.png`: “Sığınağa geri dön” → “Siğinağa geri dön”.

Bu nedenle **toplam 78/84 eşit olması tek tek her satırın korunduğu anlamına gelmiyor**.

**Ek eğik görüntü (~12°):** `benchmarks/rotated_12deg.png`
- Normal: “Gorey tamamlandi!” (Türkçe karakterlerde hata var, ünlem işareti korunmuş).
- Hızlı: “Gorey tamamlandi” (Türkçe karakter hatalarının yanında sondaki ünlem de kayıp).
- Tahmin edilen açı her ikisinde yaklaşık 11,8°.

Bu örnekler, hızlı ayarın **otomatik olarak varsayılan yapılmaması** gerektiğine kanıttır.

## 4. Aynı yeni görüntülerde kurulu rakipler

14 yeni görüntü / 42 satır (birinci turdaki tam satır sayısı):

| OCR | Tam doğru satır | Metin karakter doğruluğu |
|---|---:|---:|
| GameTranslatorOCR normal | 39/42 | %99,50 |
| GameTranslatorOCR hızlı | 39/42 | %99,50 |
| RapidOCR (PP-OCRv6) | **40/42** | %97,16 |
| Tesseract 5.5.3 (eng+turk, PSM11) | 34/42 | %97,78 |

RapidOCR'ın bazı satırları tam doğru okurken fazladan metin tespit etmesi birleşik metin karakter skorunu düşürebilir. Bu satır ve karakter ölçütleri farklı davranışları ölçer. Tesseract karşılaştırmasındaki CLI işlem açılış maliyeti, OCR çalışma zamanı hızlarıyla birebir eşdeğer değildir; burada öncelik doğruluktur. **Bu yeni stres testinde RapidOCR v6 tam doğru satır sayısında bizden bir satır daha iyi**.

## 5. Kabul kararı

1. **PASS:** Hızlı ayar aynı sentetik korpusta normal ayarın toplam tam satır ve karakter doğruluğunu düşürmedi.
2. **PASS:** Hızlı ayar bu makinede yaklaşık %17–20 daha düşük tam ekran OCR gecikmesi ve daha az peak RSS üretti.
3. **LIMITATION:** Yeni sette hızlı profil iki benzersiz satırda, normal profilin yapmadığı Türkçe harf hataları üretiyor; dolayısıyla bireysel doğruluk korunmuyor.
4. **LIMITATION:** Eğik yazı örneğinde hızlı profil noktalama kaybediyor.
5. **DECISION:** `--fast` isteğe bağlı kalmalı; varsayılan Balanced 960 px korunmalı. Gelecekte adaptif ikinci tarama ya da daha sağlam yön/perspektif algoritmalarıyla bu farklar azaltılabilir; otomatik telafi henüz eklenmedi.

## 6. Nasıl yeniden çalıştırılır?

Proje kökünde:

```bash
dotnet build GameTranslatorOCR.sln -c Release
python3 benchmarks/fast_profile_gate.py
python3 benchmarks/compare_fast_regression.py
```

Yeni bağımsız stres görselleri ve referansları:
- `benchmarks/make_independent_stress.py`
- `benchmarks/independent_stress/`

Altı ayrı koşumun satır satır ham sonuçları ve RAM/latency:
- `benchmarks/regression_20261016/REPORT.md`
- `benchmarks/regression_20261016/{development,holdout,independent_stress}_{normal,fast}.json`


## 7. Kapsam sınırlaması

Bunlar yalnızca sentetik oyun arayüzleridir; gerçek oyun UI'ları, hareketli sahneler, 4K, ekran yakalama alt sistemi, Windows CPU, GPU ve uzun süreli çalışma testi bu denetime dahil edilmedi. Küçük fontlar, kontrast ve perspektif yüzünden gerçek oyunlarda performans farklı olabilir.
