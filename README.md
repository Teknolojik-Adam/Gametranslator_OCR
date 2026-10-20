# GameTranslatorOCR

**GameTranslatorOCR**, oyun ekranları, altyazılar ve görüntülerdeki metinleri algılamak ve okumak için geliştirilen, CPU üzerinde çalışabilen bağımsız bir **C# / .NET 8 OCR motorudur**.

Proje; ONNX tabanlı metin algılama ve tanıma, görüntü ön işleme, metin satırı takibi ve kare değişimi analizi içerir. Windows ve Linux için komut satırı aracı ve yeniden kullanılabilir .NET kütüphaneleri sağlar.



## Durum

- **Platformlar:** Linux x64 ve Windows x64 için derleme/dağıtım yapılandırması.
- **Çalışma ortamı:** .NET 8; dağıtımlar framework-dependent olduğundan uygun .NET 8 runtime gereklidir.
- **Çıkarım:** ONNX Runtime 1.29.0 ile CPU.
- **Görüntü işleme:** SkiaSharp 3.119.1.
- **Önerilen model:** PP-OCRv5 Mobile detector + PP-OCRv6 small recognizer hibriti (`models/latin-v6-hybrid`).
- **Doğrulama:** Linux üzerinde geliştirme ve testler yapılmıştır.

## Özellikler

- ONNX modelleriyle metin bölgesi algılama ve karakter tanıma.
- OCR satırları, koordinatlar ve güven skorları.
- PNG/JPEG görüntülerini ve ham BGRA/RGBA karelerini işleme.
- `SmartOcrSession` ile aynı karelerde gereksiz OCR çağrılarını atlama, değişen bölgeleri yeniden okuma.
- `FrameChangeAnalyzer` ile renk/parlaklık değişimlerini izleme ve `LineTracker` ile metin satırlarını takip etme.
- Oyun altyazıları için bölge kırpma, padding, isteğe bağlı perspektif ve gelişmiş ön işleme seçenekleri.
- Türkçe ve İngilizce metinler için isteğe bağlı karakter aday filtresi (`--tr-charset`).
- Hızlı CPU profili (`--fast`), benchmark ve model bütünlük kontrolü.
- GPU gerektirmeyen kullanım; sonuçlar işlemciye, görüntüye ve modele bağlıdır.

## Proje yapısı

```
GameTranslatorOCR/
├── src/
│   ├── GameTranslatorOCR.Core/       # OCR motoru, ONNX çıkarımı, görüntü işleme
│   ├── GameTranslatorOCR.Tracking/   # Kare değişimi, satır takibi, SmartOcrSession
│   └── GameTranslatorOCR.Cli/        # CLI komutları ve ölçüm araçları
├── tests/GameTranslatorOCR.Tests/   # Test projesi
├── models/                           # Yerel model paketleri
├── samples/                          # Yerel örnekler (görseller Git depoya dahil değil)
├── benchmarks/                       # Test betikleri/raporlar (görseller Git depoya dahil değil)
├── docs/                             # Teknik geliştirme raporları
├── licenses/                         # Üçüncü taraf lisansları
├── THIRD_PARTY.md                    # Model ve bağımlılık atıfları
├── LICENSE                           # GameTranslatorOCR kod lisansı
└── GameTranslatorOCR.sln
```

OCR motorunun ana uygulaması: `src/GameTranslatorOCR.Core/Engines/OnnxGameOcrEngine.cs`.

## Gereksinimler

- .NET 8 SDK (kaynak koddan derlemek için).
- Uygun .NET 8 runtime (hazır framework-dependent CLI paketleri için).
- Desteklenen işletim sistemi ve mimari (mevcut dağıtım hedefleri: `linux-x64`, `win-x64`).
- OCR model paketi (`detector.onnx`, `recognizer.onnx`, `charset.txt`, `manifest.json`).


## Derleme

Proje kökünde:

```bash
dotnet restore GameTranslatorOCR.sln
dotnet build GameTranslatorOCR.sln -c Release
```

## Kullanım

**Test görselleri GitHub deposuna eklenmez.** Aşağıdaki `ornek-goruntu.png` dosyasını kendi ekran görüntünüzle, `ornek-gorseller/` klasörünü ise kendi PNG test koleksiyonunuzla değiştirin. Dosyaları proje köküne koyabilir veya tam dosya yolu kullanabilirsiniz. Görsel gerektiren testler, örnek görüntüler olmadan çalışmaz.

Önce model paketini doğrulayın:

```bash
dotnet run --project src/GameTranslatorOCR.Cli -c Release -- validate models/latin-v6-hybrid
```

Örnek görüntüde OCR çalıştırın:

```bash
dotnet run --project src/GameTranslatorOCR.Cli -c Release -- ocr ornek-goruntu.png models/latin-v6-hybrid tr balanced
```

Gelişmiş ön işleme, hızlı CPU profili ve Türkçe karakter filtresi:

```bash
dotnet run --project src/GameTranslatorOCR.Cli -c Release -- ocr ornek-goruntu.png models/latin-v6-hybrid tr balanced --enhanced --fast --tr-charset
```

Basit performans ölçümü:

```bash
dotnet run --project src/GameTranslatorOCR.Cli -c Release -- bench ornek-goruntu.png models/latin-v6-hybrid 5 balanced
```

Kare değişimi analiziyle tekrar ölçümü:

```bash
dotnet run --project src/GameTranslatorOCR.Cli -c Release -- bench-smart ornek-goruntu.png models/latin-v6-hybrid 60 --enhanced --fast
```

Görüntü koleksiyonu üzerinden karşılaştırma:

```bash
dotnet run --project src/GameTranslatorOCR.Cli -c Release -- suite ornek-gorseller/ models/latin-v6-hybrid 2 6 --enhanced --fast
```

Ek CLI seçenekleri ve teknik ayrıntılar için `src/GameTranslatorOCR.Cli/Program.cs` ve `docs/` klasörüne bakın.

## Testler

```bash
dotnet run --project tests/GameTranslatorOCR.Tests -c Release -- models/latin-v6-hybrid ornek-goruntu.png
```

Test görselleri yerel geliştirme ortamında korunur; GitHub üzerinden sağlanmaz. Bazı benchmark betikleri belirli yerel görsel yollarını bekleyebilir ve bu dosyalar olmadan çalışmaz.

Geçmiş ölçüm ve regresyon raporları `docs/` ve `benchmarks/` altında bulunur. Örneğin `docs/PHASE9_OCR_HOTPATH_20261016.md`, 35 sentetik görüntü üzerinde yapılan hız ve kalite karşılaştırmalarını açıklar.

**Performans notu:** Belgelerdeki süreler ve doğruluk oranları belirtilen test ortamı/veri setlerine aittir; her oyun, cihaz, çözünürlük veya Windows sistemi için garanti değildir. Gerçek oyun görüntülerinde bağımsız kalite değerlendirmesi ve Windows çalışma zamanı testi sürmektedir.

## Windows ve Linux paketleri

Linux ortamında proje kökünden:

```bash
bash scripts/build-release.sh
```

Betik `dist/linux-x64/` ve `dist/win-x64/` klasörlerine framework-dependent CLI paketleri üretir; mevcut yerel model klasörlerini ve üçüncü taraf bildirimlerini dağıtıma kopyalar.

Linux örneği:

```bash
./dist/linux-x64/GameTranslatorOCR.Cli ocr ornek-goruntu.png dist/linux-x64/models/latin-v6-hybrid tr
```

Windows paketi üretilmiş olması, gerçek Windows ortamında test edildiği anlamına gelmez.

## Kütüphane olarak kullanım

- `GameTranslatorOCR.Core`: OCR algılama ve tanıma bileşenleri.
- `GameTranslatorOCR.Tracking`: `FrameChangeAnalyzer`, `LineTracker` ve `SmartOcrSession`.
- `SmartOcrSession.ProcessAsync(...)`: Görüntü karelerini değerlendirir, gerektiğinde OCR yapar ve önceki kareye göre değişen metinleri takip etmeye yardımcı olur.

API ayrıntıları için ilgili kaynak dosyaları ve teknik raporları inceleyin.

## Lisans — ticari kullanım yasaktır

**GameTranslatorOCR'ın hak sahibi olduğumuz özgün kaynak kodu**, [GameTranslatorOCR Non-Commercial Attribution License v1.0](LICENSE) kapsamında sunulur.

- Ticari olmayan kişisel, eğitim ve araştırma amaçlı kullanım lisans şartlarıyla mümkündür.
- **Ticari kullanım, ticari ürün veya OCR motorunun ya da türevlerinin satışı yasaktır.**
- Motoru kullanan projeler **GameTranslatorOCR** adını görünür biçimde belirtmeli; lisans ve telif bildirimlerini korumalıdır.
- Ayrıntılar ve bağlayıcı şartlar için mutlaka dosyasını okuyun.

Bu özel lisans, proje kaynak kodu görüntülenebilir (source-available) olarak paylaşılır.

## Katkı ve geri bildirim

Hata raporları, yeniden üretilebilir test örnekleri, performans ölçümleri ve geliştirme önerileri değerlidir. Bir sorun bildirirken işletim sistemi, .NET sürümü, kullanılan model paketi, CLI komutu ve mümkünse kişisel veri içermeyen örnek görüntüyü ekleyin.

---

GameTranslatorOCR — bağımsız, CPU odaklı oyun metni OCR motoru.
