using GameTranslatorOCR.Core.Models;

namespace GameTranslatorOCR.Tracking;

/// <summary>Çıplak ekran görüntüsü byte sırası: her piksel 4 kanal.</summary>
public enum FramePixelLayout { Bgra32, Rgba32 }

public sealed record FrameChangeResult(
    bool FullScanRequired,
    IReadOnlyList<OcrBox> ChangedRegions,
    int ChangedTiles)
{
    public bool IsUnchanged => !FullScanRequired && ChangedRegions.Count == 0;
}

/// <summary>
/// Oyun karelerinde görüntü değişen bölgeleri izler. Dili/OCR modelini bilmez.
/// Renkli Y-Co-Cg imzası kare başına 12x12 karo ve karoda 4x4 örneklemle çıkarılır.
/// Son işlenen referans kare korunur: çok yavaş değişimler de zamanla birikir.
/// İlk kare, çözünürlük değişimi, çok büyük ekran değişimi ve periyodik senkronizasyon
/// tam OCR ister. Bölgesel OCR'ın kendisini yapmaz.
/// </summary>
public sealed class FrameChangeAnalyzer
{
    private const int SamplesPerAxis = 4;
    private const int SamplesPerTile = SamplesPerAxis * SamplesPerAxis;
    private const int SignatureChannels = 3; // parlaklık + kırmızı/yeşil + mavi/yeşil farkları
    private byte[]? _reference;
    private FramePixelLayout _referenceLayout;
    private int _width;
    private int _height;
    private int _framesSinceFullScan;

    public int TileSize { get; }
    public int FullScanInterval { get; }
    public double FullScanChangeRatio { get; }

    public FrameChangeAnalyzer(int tileSize = 12, int fullScanInterval = 120,
        double fullScanChangeRatio = 0.30)
    {
        if (tileSize < 8 || tileSize > 64)
            throw new ArgumentOutOfRangeException(nameof(tileSize));
        if (fullScanInterval < 1)
            throw new ArgumentOutOfRangeException(nameof(fullScanInterval));
        if (fullScanChangeRatio <= 0 || fullScanChangeRatio > 1)
            throw new ArgumentOutOfRangeException(nameof(fullScanChangeRatio));
        TileSize = tileSize;
        FullScanInterval = fullScanInterval;
        FullScanChangeRatio = fullScanChangeRatio;
    }

    public FrameChangeResult Analyze(ReadOnlySpan<byte> frame,
        int width, int height, int stride, FramePixelLayout layout = FramePixelLayout.Bgra32)
    {
        if (width <= 0 || height <= 0 || width > 8192 || height > 8192)
            throw new ArgumentOutOfRangeException(nameof(width), "Geçersiz kare boyutu.");
        if (stride < (long)width * 4 || frame.Length < (long)(height - 1) * stride + (long)width * 4)
            throw new ArgumentException("BGRA/RGBA verisi veya stride geçersiz.", nameof(frame));
        int tilesX = (width + TileSize - 1) / TileSize;
        int tilesY = (height + TileSize - 1) / TileSize;
        int totalTiles = tilesX * tilesY;
        var signature = new byte[totalTiles * SamplesPerTile * SignatureChannels];
        int redOffset = layout == FramePixelLayout.Bgra32 ? 2 : 0;
        int blueOffset = layout == FramePixelLayout.Bgra32 ? 0 : 2;

        for (int ty = 0; ty < tilesY; ty++)
        for (int tx = 0; tx < tilesX; tx++)
        for (int sy = 0; sy < SamplesPerAxis; sy++)
        for (int sx = 0; sx < SamplesPerAxis; sx++)
        {
            int x = Math.Min(width - 1, tx * TileSize + (sx * TileSize / 4) + TileSize / 8);
            int y = Math.Min(height - 1, ty * TileSize + (sy * TileSize / 4) + TileSize / 8);
            int index = y * stride + x * 4;
            int r = frame[index + redOffset], g = frame[index + 1], b = frame[index + blueOffset];
            byte luma = (byte)((77 * r + 150 * g + 29 * b) >> 8);
            int signatureIndex = ((ty * tilesX + tx) * SamplesPerTile) + sy * SamplesPerAxis + sx;
            int offset = signatureIndex * SignatureChannels;
            signature[offset] = luma;
            signature[offset + 1] = (byte)((r - g + 255) / 2);
            signature[offset + 2] = (byte)((b - g + 255) / 2);
        }

        bool newSize = _reference is null || _width != width || _height != height ||
            _referenceLayout != layout;
        byte[]? old = _reference;
        _width = width;
        _height = height;
        _referenceLayout = layout;

        if (newSize)
        {
            _reference = signature;
            return FullScan(width, height, totalTiles);
        }

        _framesSinceFullScan++;
        if (_framesSinceFullScan >= FullScanInterval)
        {
            _reference = signature;
            return FullScan(width, height, totalTiles);
        }

        var changed = new bool[totalTiles];
        int changedCount = 0;
        for (int i = 0; i < totalTiles; i++)
        {
            int changedSamples = 0, largestDelta = 0;
            int offset = i * SamplesPerTile * SignatureChannels;
            for (int sample = 0; sample < SamplesPerTile; sample++)
            {
                int index = offset + sample * SignatureChannels;
                int lumaDelta = Math.Abs(signature[index] - old![index]);
                int chromaRedDelta = Math.Abs(signature[index + 1] - old[index + 1]);
                int chromaBlueDelta = Math.Abs(signature[index + 2] - old[index + 2]);
                int delta = Math.Max(lumaDelta, Math.Max(chromaRedDelta, chromaBlueDelta));
                largestDelta = Math.Max(largestDelta, delta);
                if (delta >= 20) changedSamples++;
            }
            if (changedSamples < 2 && largestDelta < 65) continue;
            changed[i] = true;
            changedCount++;
        }

        if ((double)changedCount / totalTiles >= FullScanChangeRatio)
        {
            _reference = signature;
            return FullScan(width, height, changedCount);
        }

        if (changedCount == 0)
            return new FrameChangeResult(false, Array.Empty<OcrBox>(), 0);

        var visited = new bool[totalTiles];
        var queue = new int[totalTiles];
        var regions = new List<OcrBox>();

        for (int start = 0; start < totalTiles; start++)
        {
            if (!changed[start] || visited[start]) continue;
            int head = 0, tail = 0;
            queue[tail++] = start;
            visited[start] = true;
            int minTx = tilesX, maxTx = 0, minTy = tilesY, maxTy = 0;

            while (head < tail)
            {
                int index = queue[head++];
                int tx = index % tilesX, ty = index / tilesX;
                minTx = Math.Min(minTx, tx);
                maxTx = Math.Max(maxTx, tx);
                minTy = Math.Min(minTy, ty);
                maxTy = Math.Max(maxTy, ty);

                for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++)
                {
                    int nx = tx + dx, ny = ty + dy;
                    if (nx < 0 || nx >= tilesX || ny < 0 || ny >= tilesY) continue;
                    int ni = ny * tilesX + nx;
                    if (changed[ni] && !visited[ni])
                    {
                        visited[ni] = true;
                        queue[tail++] = ni;
                    }
                }
            }

            int pad = TileSize;
            int x1 = Math.Max(0, minTx * TileSize - pad);
            int y1 = Math.Max(0, minTy * TileSize - pad);
            int x2 = Math.Min(width, (maxTx + 1) * TileSize + pad);
            int y2 = Math.Min(height, (maxTy + 1) * TileSize + pad);
            regions.Add(new OcrBox(x1, y1, x2 - x1, y2 - y1));
        }

        // Yakındaki parçaları OCR'a tek crop olarak gönder; gereksiz çağrı sayısını azalt.
        bool merged;
        do
        {
            merged = false;
            for (int i = 0; i < regions.Count && !merged; i++)
            for (int j = i + 1; j < regions.Count; j++)
            {
                var a = regions[i];
                var b = regions[j];
                int xGap = Math.Max(0, Math.Max(a.X - (b.X + b.Width), b.X - (a.X + a.Width)));
                int yGap = Math.Max(0, Math.Max(a.Y - (b.Y + b.Height), b.Y - (a.Y + a.Height)));
                if (xGap > TileSize * 2 || yGap > TileSize / 2) continue;

                int x1 = Math.Min(a.X, b.X), y1 = Math.Min(a.Y, b.Y);
                int x2 = Math.Max(a.X + a.Width, b.X + b.Width);
                int y2 = Math.Max(a.Y + a.Height, b.Y + b.Height);
                regions[i] = new OcrBox(x1, y1, x2 - x1, y2 - y1);
                regions.RemoveAt(j);
                merged = true;
                break;
            }
        } while (merged);

        if (regions.Count > 64)
        {
            _reference = signature;
            return FullScan(width, height, changedCount);
        }

        // Yalnız değiştiği kanıtlanan karoların referansını güncelle.
        // Azar azar değişen diğer karoların farkları kaybolmaz.
        for (int i = 0; i < totalTiles; i++)
        {
            if (!changed[i]) continue;
            int offset = i * SamplesPerTile * SignatureChannels;
            Buffer.BlockCopy(signature, offset, _reference!, offset,
                SamplesPerTile * SignatureChannels);
        }
        return new FrameChangeResult(false,
            regions.OrderBy(x => x.Y).ThenBy(x => x.X).ToArray(), changedCount);
    }

    private FrameChangeResult FullScan(int width, int height, int dirty)
    {
        _framesSinceFullScan = 0;
        return new FrameChangeResult(true, [new OcrBox(0, 0, width, height)], dirty);
    }

    public void Reset()
    {
        _reference = null;
        _width = _height = _framesSinceFullScan = 0;
    }
}
