using System.Diagnostics;
using GameTranslatorOCR.Core.Abstractions;
using GameTranslatorOCR.Core.Imaging;
using GameTranslatorOCR.Core.Models;
using SkiaSharp;

namespace GameTranslatorOCR.Tracking;

/// <summary>OCR çalıştırılıp çalıştırılmadığını ve karenin satır durumunu döndürür.</summary>
public sealed record FrameOcrResult(
    IReadOnlyList<TrackedLine> Lines,
    bool OcrExecuted,
    bool FullScan,
    IReadOnlyList<OcrBox> ScannedRegions,
    TimeSpan Elapsed);

/// <summary>
/// Oyun kareleri için artımlı OCR oturumu.
/// İlk kare tam OCR, değişmeyen kare OCR'sız, bölgesel değişen kare sadece
/// güncellenen alanların crop OCR'sıdır. Her N karede tam senkronizasyon yapılır.
/// </summary>
public sealed class SmartOcrSession : IDisposable
{
    private readonly IOcrEngine _engine;
    private readonly FrameChangeAnalyzer _analyzer;
    private readonly LineTracker _tracker;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private bool _disposed;

    public SmartOcrSession(IOcrEngine engine, FrameChangeAnalyzer? analyzer = null,
        LineTracker? tracker = null)
    {
        _engine = engine ?? throw new ArgumentNullException(nameof(engine));
        _analyzer = analyzer ?? new FrameChangeAnalyzer();
        _tracker = tracker ?? new LineTracker();
    }

    /// <summary>
    /// encodedFrame: PNG/JPEG; rawFrame: aynı karenin BGRA/RGBA piksel belleği.
    /// rawFrame belleği OCR tamamlanana kadar çağıran tarafından korunmalıdır.
    /// IRawOcrEngine ve BGRA32 kullanılıyorsa encodedFrame boş olabilir.
    /// Oturum kendisine verilen IOcrEngine'in ömrünü yönetmez.
    /// </summary>
    public async Task<FrameOcrResult> ProcessAsync(
        ReadOnlyMemory<byte> encodedFrame,
        ReadOnlyMemory<byte> rawFrame,
        int width, int height, int stride,
        OcrOptions options,
        FramePixelLayout layout = FramePixelLayout.Bgra32,
        CancellationToken cancellationToken = default)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        var clock = Stopwatch.StartNew();
        try
        {
            cancellationToken.ThrowIfCancellationRequested();
            var changed = _analyzer.Analyze(rawFrame.Span, width, height, stride, layout);
            if (changed.IsUnchanged)
                return new FrameOcrResult(_tracker.Snapshot(), false, false,
                    Array.Empty<OcrBox>(), clock.Elapsed);

            var regions = changed.FullScanRequired
                ? [new OcrBox(0, 0, width, height)]
                : ExpandWithKnownLines(changed.ChangedRegions, _tracker.Snapshot(), width, height);

            // Büyük ekrandaki yaygın değişimler artımlı modun avantajını kaldırır.
            bool fullScan = changed.FullScanRequired || regions.Count > 8 ||
                regions.Sum(r => (long)r.Width * r.Height) > (long)width * height * 0.45;

            bool canUseRaw = layout == FramePixelLayout.Bgra32 && _engine is IRawOcrEngine;
            if (fullScan)
            {
                var result = canUseRaw
                    ? await ((IRawOcrEngine)_engine).RecognizeBgraAsync(rawFrame,
                        width, height, stride, options, cancellationToken).ConfigureAwait(false)
                    : await _engine.RecognizeAsync(encodedFrame, options,
                        cancellationToken).ConfigureAwait(false);
                return new FrameOcrResult(_tracker.Update(result.Lines), true, true,
                    [new OcrBox(0, 0, width, height)], clock.Elapsed);
            }

            var updated = new List<OcrLine>();
            if (canUseRaw)
            {
                var rawEngine = (IRawOcrEngine)_engine;
                // Gerçek zamanlı capture'da PNG kodlama/dekodlama artık gerekmiyor.
                foreach (var region in regions)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    byte[] crop = CropBgra(rawFrame, stride, region);
                    var croppedResult = await rawEngine.RecognizeBgraAsync(crop,
                        region.Width, region.Height, region.Width * 4, options,
                        cancellationToken).ConfigureAwait(false);
                    AppendTranslatedBounds(updated, croppedResult, region);
                }
            }
            else
            {
                // Diğer IOcrEngine uygulamaları ve RGBA32 yakalama için uyumluluk yolu.
                using var decoded = SKBitmap.Decode(encodedFrame.ToArray())
                    ?? throw new InvalidDataException("Kare görüntüsü çözümlenemedi.");
                if (decoded.Width != width || decoded.Height != height)
                    throw new InvalidDataException(
                        "Ham görüntü ve kodlanmış görüntü boyutları uyuşmuyor.");

                foreach (var region in regions)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    using var crop = ImageTensorBuilder.Crop(decoded, region.X, region.Y,
                        region.Width, region.Height);
                    using var image = SKImage.FromBitmap(crop);
                    using var data = image.Encode(SKEncodedImageFormat.Png, 100);
                    var croppedResult = await _engine.RecognizeAsync(data.ToArray(), options,
                        cancellationToken).ConfigureAwait(false);
                    AppendTranslatedBounds(updated, croppedResult, region);
                }
            }

            return new FrameOcrResult(_tracker.UpdatePartial(updated, regions), true, false,
                regions, clock.Elapsed);
        }
        catch
        {
            // İptal/hata durumunda başarısız kareyi doğru işlenmiş varsaymayız.
            _analyzer.Reset();
            throw;
        }
        finally
        {
            _gate.Release();
        }
    }

    private static byte[] CropBgra(ReadOnlyMemory<byte> rawFrame, int stride, OcrBox region)
    {
        int lineBytes = checked(region.Width * 4);
        byte[] result = new byte[checked(lineBytes * region.Height)];
        for (int y = 0; y < region.Height; y++)
        {
            int sourceOffset = checked((region.Y + y) * stride + region.X * 4);
            rawFrame.Span.Slice(sourceOffset, lineBytes)
                .CopyTo(result.AsSpan(y * lineBytes, lineBytes));
        }
        return result;
    }

    private static void AppendTranslatedBounds(
        List<OcrLine> output, OcrResult partialResult, OcrBox region)
    {
        foreach (var line in partialResult.Lines)
        {
            output.Add(line with
            {
                Bounds = new OcrBox(line.Bounds.X + region.X,
                    line.Bounds.Y + region.Y, line.Bounds.Width, line.Bounds.Height)
            });
        }
    }

    private static IReadOnlyList<OcrBox> ExpandWithKnownLines(
        IReadOnlyList<OcrBox> changed,
        IReadOnlyList<TrackedLine> known, int width, int height)
    {
        var expanded = changed.ToList();
        // Kısmi değişiklik, eski satırın ortasına denk geliyorsa crop'un satır
        // tamamını kapsaması için tanınan kutuyu da içine al.
        for (int i = 0; i < expanded.Count; i++)
        {
            var r = expanded[i];
            foreach (var line in known)
            {
                var box = line.Bounds;
                bool touching = r.X < box.X + box.Width && r.X + r.Width > box.X &&
                    r.Y < box.Y + box.Height && r.Y + r.Height > box.Y;
                if (!touching) continue;
                int x1 = Math.Max(0, Math.Min(r.X, box.X - 8));
                int y1 = Math.Max(0, Math.Min(r.Y, box.Y - 8));
                int x2 = Math.Min(width, Math.Max(r.X + r.Width, box.X + box.Width + 8));
                int y2 = Math.Min(height, Math.Max(r.Y + r.Height, box.Y + box.Height + 8));
                r = new OcrBox(x1, y1, x2 - x1, y2 - y1);
            }
            expanded[i] = r;
        }

        // Birleşen crop bölgelerinin iki kez OCR edilmesini önle.
        bool merged;
        do
        {
            merged = false;
            for (int i = 0; i < expanded.Count && !merged; i++)
            for (int j = i + 1; j < expanded.Count; j++)
            {
                var a = expanded[i];
                var b = expanded[j];
                if (a.X > b.X + b.Width || b.X > a.X + a.Width ||
                    a.Y > b.Y + b.Height || b.Y > a.Y + a.Height)
                    continue;
                int x1 = Math.Min(a.X, b.X), y1 = Math.Min(a.Y, b.Y);
                int x2 = Math.Max(a.X + a.Width, b.X + b.Width);
                int y2 = Math.Max(a.Y + a.Height, b.Y + b.Height);
                expanded[i] = new OcrBox(x1, y1, x2 - x1, y2 - y1);
                expanded.RemoveAt(j);
                merged = true;
                break;
            }
        } while (merged);

        // Oyun altyazılarında geniş değişen bir bölge, satırın tamamını
        // içermeyebilir. Bu durumda tam ekran yerine yalnız yatay bandı
        // taramak, dar crop'larda harf tanıma hatalarını azaltır.
        for (int i = 0; i < expanded.Count; i++)
        {
            var region = expanded[i];
            if (region.Width >= width * 0.35)
                expanded[i] = new OcrBox(0, region.Y, width, region.Height);
        }

        // Yatay banda genişletildikten sonra yeniden çakışanları birleştir.
        // (Birden fazla satır aynı banda düşerse çift OCR'ı engeller.)
        merged = true;
        while (merged)
        {
            merged = false;
            for (int i = 0; i < expanded.Count && !merged; i++)
            for (int j = i + 1; j < expanded.Count; j++)
            {
                var a = expanded[i];
                var b = expanded[j];
                if (a.X >= b.X + b.Width || b.X >= a.X + a.Width ||
                    a.Y >= b.Y + b.Height || b.Y >= a.Y + a.Height)
                    continue;
                int x1 = Math.Min(a.X, b.X), y1 = Math.Min(a.Y, b.Y);
                int x2 = Math.Max(a.X + a.Width, b.X + b.Width);
                int y2 = Math.Max(a.Y + a.Height, b.Y + b.Height);
                expanded[i] = new OcrBox(x1, y1, x2 - x1, y2 - y1);
                expanded.RemoveAt(j);
                merged = true;
                break;
            }
        }
        return expanded;
    }

    public void Reset()
    {
        _analyzer.Reset();
        _tracker.Reset();
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _gate.Dispose();
    }
}
