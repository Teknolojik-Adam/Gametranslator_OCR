from pathlib import Path
R=Path("/run/media/adminmehmet/0ba60d1b-7861-4575-a77f-d974006e3982/GameTranslatorOCR")
def edit(rel, changes):
    f=R/rel
    source=f.read_text(encoding="utf8")
    for before,after in changes:
        if source.count(before)!=1:
            raise RuntimeError(f"{rel}: expected one match got {source.count(before)}: {before[:100]!r}")
        source=source.replace(before,after)
    f.write_text(source,encoding="utf8")
    print("OPTIMIZED",rel)
edit("src/GameTranslatorOCR.Core/Imaging/ImageTensorBuilder.cs", [
    ("""        int byteCount=checked(bitmap.RowBytes*height);
        var raw=new byte[byteCount];
        Marshal.Copy(bitmap.GetPixels(),raw,0,byteCount);""",
     """        // SkiaSharp exposes the existing bitmap storage as a Span. Do not
        // allocate a full-size byte[] and Marshal.Copy on every detector or
        // recognition crop. Pixel values and channel order remain unchanged.
        int byteCount=checked(bitmap.RowBytes*height);
        ReadOnlySpan<byte> raw=bitmap.GetPixelSpan();
        if(raw.Length<byteCount)
            throw new InvalidDataException("Skia bitmap piksel tamponu beklenenden kısa.");"""),
])
edit("src/GameTranslatorOCR.Core/Engines/OnnxGameOcrEngine.cs", [
    ("""            IntPtr dest = bitmap.GetPixels();
            if (dest == IntPtr.Zero) throw new OutOfMemoryException("SKBitmap ayrılmış bellek yok.");
            byte[] source = pixels.ToArray();
            for (int y = 0; y < height; y++)
                Marshal.Copy(source, y * stride, IntPtr.Add(dest, y * bitmap.RowBytes), width * 4);""",
     """            // Avoid copying the entire caller-owned BGRA buffer into a
            // temporary array. Copy scanlines directly into Skia's bitmap
            // storage, preserving row stride and every original pixel.
            Span<byte> dest = bitmap.GetPixelSpan();
            if (dest.Length < checked(bitmap.RowBytes * height))
                throw new OutOfMemoryException("SKBitmap ayrılmış bellek yok.");
            ReadOnlySpan<byte> source = pixels.Span;
            int copyWidth = checked(width * 4);
            for (int y = 0; y < height; y++)
                source.Slice(y * stride, copyWidth)
                    .CopyTo(dest.Slice(y * bitmap.RowBytes, copyWidth));""")
])
edit("src/GameTranslatorOCR.Core/Recognition/CtcDecoder.cs", [
    ("""        for(int t=0;t<time;t++)
        {
            float max=float.NegativeInfinity;int chosen=0;""",
     """        // Most ONNX Runtime outputs are contiguous DenseTensor<float>.
        // Read its flat span instead of performing a multidimensional tensor
        // index lookup for every CTC timestep and class. Preserve fallback.
        bool contiguous=probabilities is DenseTensor<float>;
        ReadOnlySpan<float> flat=probabilities is DenseTensor<float> dense
            ?dense.Buffer.Span:default;
        for(int t=0;t<time;t++)
        {
            int stepOffset=(batchIndex*time+t)*classes;
            float max=float.NegativeInfinity;int chosen=0;"""),
    ("""                float score=probabilities[batchIndex,t,cls];""",
     """                float score=contiguous?flat[stepOffset+cls]
                    :probabilities[batchIndex,t,cls];""")
])
print("HOTPATH_EDIT_DONE")
