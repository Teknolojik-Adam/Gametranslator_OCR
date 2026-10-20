using GameTranslatorOCR.Core.Models;

namespace GameTranslatorOCR.Tracking;

public sealed record TrackedLine(
    int Id,
    string Text,
    OcrBox Bounds,
    float Confidence,
    bool Changed);

/// <summary>OCR satırlarının kareler arasında kimliğini koruyan ilk eşleştirici.
/// Bu sürüm IoU tabanlıdır; optik akış ve bant bazlı güncelleme sonraki aşamadır.</summary>
public sealed class LineTracker
{
    private readonly object _gate = new();
    private List<TrackedLine> _previous = [];
    private int _nextId = 1;

    public double MinimumIoU { get; }

    public LineTracker(double minimumIoU = 0.3)
    {
        if (minimumIoU is < 0 or > 1 || double.IsNaN(minimumIoU))
            throw new ArgumentOutOfRangeException(nameof(minimumIoU));
        MinimumIoU = minimumIoU;
    }

    public IReadOnlyList<TrackedLine> Update(IReadOnlyList<OcrLine> lines)
    {
        ArgumentNullException.ThrowIfNull(lines);

        lock (_gate)
        {
            var used = new HashSet<int>();
            var next = new List<TrackedLine>();

            foreach (var line in lines)
            {
                if (line is null || !line.Bounds.IsValid || string.IsNullOrWhiteSpace(line.Text))
                    continue;

                TrackedLine? best = null;
                var bestIoU = MinimumIoU;
                foreach (var old in _previous)
                {
                    if (used.Contains(old.Id)) continue;
                    var overlap = old.Bounds.IntersectionOverUnion(line.Bounds);
                    if (overlap >= bestIoU && (best is null || overlap > bestIoU))
                    {
                        best = old;
                        bestIoU = overlap;
                    }
                }

                int id = best?.Id ?? _nextId++;
                if (best is not null) used.Add(best.Id);
                bool changed = best is null ||
                    !string.Equals(best.Text, line.Text, StringComparison.Ordinal);

                next.Add(new TrackedLine(id, line.Text, line.Bounds, line.Confidence, changed));
            }

            _previous = next;
            return next.ToArray();
        }
    }

    /// <summary>Mevcut satırları değiştirilmedi olarak döndürür.</summary>
    public IReadOnlyList<TrackedLine> Snapshot()
    {
        lock (_gate)
            return _previous.Select(line => line with { Changed = false }).ToArray();
    }

    /// <summary>
    /// Yalnızca verilen ekran bölgeleri yeniden OCR yapıldığında çağrılır.
    /// Bu bölgelerin dışındaki satırlar saklanır; bölgedeki kaybolmuş satırlar silinir.
    /// </summary>
    public IReadOnlyList<TrackedLine> UpdatePartial(
        IReadOnlyList<OcrLine> lines,
        IReadOnlyList<OcrBox> scannedRegions)
    {
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(scannedRegions);
        lock (_gate)
        {
            if (scannedRegions.Count == 0)
                return _previous.Select(line => line with { Changed = false }).ToArray();

            bool IsScanned(OcrBox box) => scannedRegions.Any(region =>
                box.X < region.X + region.Width &&
                box.X + box.Width > region.X &&
                box.Y < region.Y + region.Height &&
                box.Y + box.Height > region.Y);

            var candidates = _previous.Where(line => IsScanned(line.Bounds)).ToArray();
            var result = _previous.Where(line => !IsScanned(line.Bounds))
                .Select(line => line with { Changed = false }).ToList();
            var used = new HashSet<int>();
            foreach (var line in lines)
            {
                if (line is null || !line.Bounds.IsValid || string.IsNullOrWhiteSpace(line.Text))
                    continue;
                TrackedLine? best = null;
                double maxIoU = MinimumIoU;
                foreach (var old in candidates)
                {
                    if (used.Contains(old.Id)) continue;
                    double overlap = old.Bounds.IntersectionOverUnion(line.Bounds);
                    if (overlap >= maxIoU && (best is null || overlap > maxIoU))
                    {
                        best = old;
                        maxIoU = overlap;
                    }
                }

                int id = best?.Id ?? _nextId++;
                if (best is not null) used.Add(best.Id);
                result.Add(new TrackedLine(id, line.Text, line.Bounds, line.Confidence,
                    best is null || best.Text != line.Text));
            }

            _previous = result.OrderBy(x => x.Bounds.Y).ThenBy(x => x.Bounds.X).ToList();
            return _previous.ToArray();
        }
    }

    public void Reset()
    {
        lock (_gate)
        {
            _previous.Clear();
            _nextId = 1;
        }
    }
}
