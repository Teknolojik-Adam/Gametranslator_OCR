using GameTranslatorOCR.Core.Engines;
using GameTranslatorOCR.Core.ModelPacks;
using GameTranslatorOCR.Core.Models;
using System.Text.Json;
using SkiaSharp;
using GameTranslatorOCR.Tracking;

if (args.Length == 0 || args[0] is "--help" or "-h" or "help")
{
    Console.WriteLine("GameTranslatorOCR CLI — RapidOCR v6 improvements");
    Console.WriteLine("  status                         Altyapıyı göster");
    Console.WriteLine("  validate <modelFolder>         Model paketini doğrula");
    Console.WriteLine("  ocr <image> <modelFolder> [tr|en] [speed|balanced|quality]");
    Console.WriteLine("  bench <image> <modelFolder> [iterations=5] [speed|balanced|quality]");
    Console.WriteLine("  suite <imageFolder> <modelFolder> [passes=2] [paddingPixels=6] [flags]");
    Console.WriteLine("  Flags: --enhanced --fast --tr-charset --det-side=864 --filter --adaptive --perspective --words --batch=4 --adaptive-padding");
    Console.WriteLine("  CPU threads: GTOCR_INTRAOP_THREADS=6 (auto max 6; 1-24 supported)");
    Console.WriteLine("  bench-raw <image> <modelFolder> [iterations=5] [speed|balanced|quality]");
    Console.WriteLine("  bench-smart <image> <modelFolder> [repeats=60] [--fast] [--enhanced]");
    return 0;
}

try
{
    switch (args[0].ToLowerInvariant())
    {
        case "status":
            Console.WriteLine("Core DLL: .NET 8 / SkiaSharp / ONNX Runtime");
            Console.WriteLine("Tracking: IoU satır eşleştirici + FrameChangeAnalyzer + SmartOcrSession");
            Console.WriteLine("Detector: PP-OCRv5 Mobile DBNet (CPU)");
            Console.WriteLine("Recognizer: PP-OCRv5 Latin (CTC, CPU)");
            Console.WriteLine("GPU: henüz etkin değil");
            return 0;

        case "validate" when args.Length == 2:
            var result = ModelPackValidator.Validate(args[1]);
            if (result.IsValid)
            {
                var errors = ModelPackIntegrity.Verify(args[1]);
                if (errors.Count == 0)
                {
                    Console.WriteLine($"Model paketi ve SHA-256 doğrulandı: {result.Manifest!.PackId}");
                    return 0;
                }
                foreach (var error in errors) Console.Error.WriteLine($"HATA: {error}");
                return 1;
            }
            foreach (var error in result.Errors)
                Console.Error.WriteLine($"HATA: {error}");
            return 1;

        case "ocr" when args.Length >= 3:
            string language = args.Length >= 4 ? args[3] : "tr";
            var profile = args.Length >= 5
                ? Enum.Parse<OcrQualityProfile>(args[4], ignoreCase: true)
                : OcrQualityProfile.Balanced;
            byte[] bytes = await File.ReadAllBytesAsync(args[1]);
            using (var engine = new OnnxGameOcrEngine(args[2]))
            {
                var ocrFlags = ApplyFlags(new OcrOptions(language, profile),args.Skip(5));
                var ocr = await engine.RecognizeAsync(bytes, ocrFlags);
                Console.WriteLine($"OCR: {ocr.Lines.Count} satır, {ocr.Elapsed.TotalMilliseconds:F0} ms");
                foreach (var line in ocr.Lines)
                {
                    Console.WriteLine($"[{line.Confidence:P0}] ({line.Bounds.X},{line.Bounds.Y}," +
                        $"{line.Bounds.Width},{line.Bounds.Height}) {line.Text}");
                    if(line.Quadrilateral.HasValue)
                        Console.WriteLine($"    Eğim: {line.Quadrilateral.Value.SlopeDegrees:F1}°");
                    foreach(var word in line.Words)
                        Console.WriteLine($"    {word.Text}: x={word.Bounds.X} w={word.Bounds.Width}");
                }
            }
            return 0;

        case "bench" when args.Length >= 3:
            int iterations = args.Length >= 4 ? int.Parse(args[3]) : 5;
            if (iterations is < 1 or > 50)
                throw new ArgumentOutOfRangeException(nameof(iterations), "1-50 ölçüm seçin.");
            var benchProfile = args.Length >= 5
                ? Enum.Parse<OcrQualityProfile>(args[4], true)
                : OcrQualityProfile.Balanced;
            byte[] benchImage = await File.ReadAllBytesAsync(args[1]);
            using (var engine = new OnnxGameOcrEngine(args[2]))
            {
                // ONNX session açılışı/ilk JIT ölçüm dışında, aynı model oturumunda.
                var benchOptions = ApplyFlags(new OcrOptions("tr",benchProfile),args.Skip(5));
                var warmup = await engine.RecognizeAsync(benchImage,benchOptions);
                var values = new List<double>();
                for (int i = 0; i < iterations; i++)
                {
                    var recognized = await engine.RecognizeAsync(benchImage,
                        benchOptions);
                    values.Add(recognized.Elapsed.TotalMilliseconds);
                    Console.WriteLine($"Ölçüm {i + 1}: {values[^1]:F1} ms / {recognized.Lines.Count} satır");
                }
                values.Sort();
                int p95Index = Math.Clamp((int)Math.Ceiling(values.Count * 0.95) - 1,
                    0, values.Count - 1);
                Console.WriteLine($"Model: {engine.ModelPackId}; profil: {benchProfile}; kare: {iterations}");
                Console.WriteLine($"Isınma: {warmup.Elapsed.TotalMilliseconds:F1} ms");
                Console.WriteLine($"Ortalama: {values.Average():F1} ms; median: {values[values.Count / 2]:F1} ms;" +
                    $" p95: {values[p95Index]:F1} ms; min/max: {values[0]:F1}/{values[^1]:F1} ms");
                Console.WriteLine("Not: Aynı görüntü tekrarlandığı için gerçek oyun senaryosu yerine mikrobenchmark.");
            }
            return 0;

        case "bench-raw" when args.Length >= 3:
            int rawIterations = args.Length >= 4 ? int.Parse(args[3]) : 5;
            if (rawIterations is < 1 or > 50)
                throw new ArgumentOutOfRangeException(nameof(rawIterations), "1-50 ölçüm seçin.");
            var rawProfile = args.Length >= 5
                ? Enum.Parse<OcrQualityProfile>(args[4], true)
                : OcrQualityProfile.Balanced;
            using (var bitmap = SKBitmap.Decode(args[1])
                ?? throw new InvalidDataException("Görüntü çözümlenemedi."))
            {
                var rawBytes = new byte[checked(bitmap.Width * bitmap.Height * 4)];
                for (int y = 0; y < bitmap.Height; y++)
                for (int x = 0; x < bitmap.Width; x++)
                {
                    SKColor color = bitmap.GetPixel(x, y);
                    int position = (y * bitmap.Width + x) * 4;
                    rawBytes[position] = color.Blue;
                    rawBytes[position + 1] = color.Green;
                    rawBytes[position + 2] = color.Red;
                    rawBytes[position + 3] = 255;
                }

                using var engine = new OnnxGameOcrEngine(args[2]);
                var warmup = await engine.RecognizeBgraAsync(rawBytes,
                    bitmap.Width, bitmap.Height, bitmap.Width * 4,
                    new OcrOptions("tr", rawProfile));
                var values = new List<double>();
                for (int i = 0; i < rawIterations; i++)
                {
                    var recognized = await engine.RecognizeBgraAsync(rawBytes,
                        bitmap.Width, bitmap.Height, bitmap.Width * 4,
                        new OcrOptions("tr", rawProfile));
                    values.Add(recognized.Elapsed.TotalMilliseconds);
                    Console.WriteLine($"Raw {i + 1}: {values[^1]:F1} ms / {recognized.Lines.Count} satır");
                }
                values.Sort();
                int p95Index = Math.Clamp((int)Math.Ceiling(values.Count * .95) - 1,
                    0, values.Count - 1);
                Console.WriteLine($"Model: {engine.ModelPackId}, profil: {rawProfile}, kare: {rawIterations}");
                Console.WriteLine($"Isınma: {warmup.Elapsed.TotalMilliseconds:F1} ms");
                Console.WriteLine($"Ortalama: {values.Average():F1} ms; median: {values[values.Count / 2]:F1} ms;" +
                    $" p95: {values[p95Index]:F1} ms; min/max: {values[0]:F1}/{values[^1]:F1} ms");
                Console.WriteLine("Not: PNG'den BGRA'ya ilk dönüştürme ölçüm dışıdır." +
                    " Bu sadece tek görüntülü CPU mikrobenchmark'ıdır.");
            }
            return 0;

        case "bench-smart" when args.Length >= 3:
        {
            int repeats = args.Length >= 4 ? int.Parse(args[3]) : 60;
            if (repeats is < 1 or > 100)
                throw new ArgumentOutOfRangeException(nameof(repeats),"1-100 tekrar seçin.");
            var options = ApplyFlags(new OcrOptions("tr"), args.Skip(4));

            using var image = SKBitmap.Decode(args[1])
                ?? throw new InvalidDataException("PNG/JPEG görüntü çözümlenemedi.");
            var bgra = new byte[checked(image.Width * image.Height * 4)];
            for (int y = 0; y < image.Height; y++)
            for (int x = 0; x < image.Width; x++)
            {
                var rgb = image.GetPixel(x, y);
                int pos = (y * image.Width + x) * 4;
                bgra[pos] = rgb.Blue;
                bgra[pos + 1] = rgb.Green;
                bgra[pos + 2] = rgb.Red;
                bgra[pos + 3] = 255;
            }

            using var engine = new OnnxGameOcrEngine(args[2]);
            using var smart = new SmartOcrSession(engine,
                new FrameChangeAnalyzer(fullScanInterval:120));
            // ONNX session/JIT setup outside the timed change-detection iterations.
            var initial = await smart.ProcessAsync(ReadOnlyMemory<byte>.Empty,
                bgra, image.Width, image.Height, image.Width * 4, options);
            if (!initial.OcrExecuted)
                throw new InvalidOperationException("İlk karede tam OCR bekleniyordu.");
            var times = new List<double>(repeats);
            int ocrRuns = 0;
            for (int i = 0; i < repeats; i++)
            {
                var frame = await smart.ProcessAsync(ReadOnlyMemory<byte>.Empty,
                    bgra, image.Width, image.Height, image.Width * 4, options);
                times.Add(frame.Elapsed.TotalMilliseconds);
                if (frame.OcrExecuted) ocrRuns++;
            }
            times.Sort();
            int p95i = Math.Clamp((int)Math.Ceiling(times.Count * .95) - 1, 0, times.Count - 1);
            Console.WriteLine($"Smart OCR başlangıç: {initial.Elapsed.TotalMilliseconds:F1} ms, {initial.Lines.Count} satır");
            Console.WriteLine($"Aynı kare tekrar: {repeats}; OCR yeniden çalıştı: {ocrRuns}");
            Console.WriteLine($"Yalnız kontrol/önbellek: ortalama {times.Average():F2} ms, p95 {times[p95i]:F2} ms");
            Console.WriteLine("Not: Hareketli sahne ve periyodik tam tarama maliyeti bu sabit-kare testinde yok.");
            return 0;
        }

        case "suite" when args.Length >= 3:
        {
            var files = Directory.GetFiles(args[1], "*.png")
                .OrderBy(x => x, StringComparer.Ordinal).ToArray();
            if (files.Length == 0) throw new InvalidDataException("PNG görüntüsü yok.");
            int passes = args.Length >= 4 ? int.Parse(args[3]) : 2;
            if (passes is < 1 or > 5) throw new ArgumentOutOfRangeException(nameof(passes));
            int padding = args.Length >= 5 ? int.Parse(args[4]) : 6;
            if (padding is < 0 or > 24) throw new ArgumentOutOfRangeException(nameof(padding));
            var options = ApplyFlags(new OcrOptions("tr", RecognitionPaddingPixels: padding),args.Skip(5));
            using var engine = new OnnxGameOcrEngine(args[2]);
            await engine.RecognizeAsync(await File.ReadAllBytesAsync(files[0]), options);
            for (int pass = 0; pass < passes; pass++)
            {
                foreach (var file in files)
                {
                    var res = await engine.RecognizeAsync(await File.ReadAllBytesAsync(file),
                        options);
                    var record = new
                    {
                        name = Path.GetFileName(file),
                        pass,
                        ms = res.Elapsed.TotalMilliseconds,
                        texts = res.Lines.Select(x => x.Text).ToArray(),
                        confidences = res.Lines.Select(x => x.Confidence).ToArray(),
                        bounds = res.Lines.Select(x => new { x.Bounds.X, x.Bounds.Y, x.Bounds.Width, x.Bounds.Height }).ToArray(),
                        words = res.Lines.Sum(x=>x.Words.Count),
                        angled = res.Lines.Count(x=>x.Quadrilateral.HasValue),
                        stages = engine.LastTimings
                    };
                    Console.WriteLine("BENCHRESULT\t" + JsonSerializer.Serialize(record));
                }
            }
            return 0;
        }

        default:
            Console.Error.WriteLine("Bilinmeyen komut. --help kullanın.");
            return 2;
    }
}
catch (Exception ex)
{
    Console.Error.WriteLine($"OCR HATASI: {ex.GetType().Name}: {ex.Message}");
    return 1;
}

static OcrOptions ApplyFlags(OcrOptions initial,IEnumerable<string> flags)
{
    var o=initial;
    foreach(string flag in flags)
    {
        switch(flag)
        {
            case "--enhanced":
                o=o with
                {
                    EnableArtifactFilter=true,
                    AdaptiveDetectionUpscale=true,
                    AdaptiveRecognitionPadding=true,
                    EnablePerspectiveCorrection=true,
                    RecognitionBatchSize=4,
                    ReturnWordBoxes=true
                };
                break;
            case "--fast":
                // Fedora-tuned option. Default Balanced remains 960px
                // until accuracy is verified on real game screenshots.
                o=o with{DetectionMaxSideOverride=864};
                break;
            case "--tr-charset":
                o=o with{RestrictTurkishEnglishCharset=true};
                break;
            case "--filter":
                o=o with{EnableArtifactFilter=true};break;
            case "--adaptive":
                o=o with{AdaptiveDetectionUpscale=true};break;
            case "--adaptive-padding":
                o=o with{AdaptiveRecognitionPadding=true};break;
            case "--perspective":
                o=o with{EnablePerspectiveCorrection=true};break;
            case "--words":
                o=o with{ReturnWordBoxes=true};break;
            default:
                if(flag.StartsWith("--det-side=",StringComparison.Ordinal))
                {
                    if(!int.TryParse(flag["--det-side=".Length..],out int side) ||
                        side is < 320 or > 1920)
                        throw new ArgumentException("detector side must be 320-1920");
                    o=o with{DetectionMaxSideOverride=side};
                }
                else if(flag.StartsWith("--batch=",StringComparison.Ordinal))
                {
                    if(!int.TryParse(flag["--batch=".Length..],out int n)||n<1||n>12)
                        throw new ArgumentException("batch 1-12 olmalı");
                    o=o with{RecognitionBatchSize=n};
                }
                else throw new ArgumentException($"Bilinmeyen OCR seçeneği: {flag}");
                break;
        }
    }
    return o;
}
