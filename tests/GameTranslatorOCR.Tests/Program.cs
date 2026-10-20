using GameTranslatorOCR.Core.Engines;
using GameTranslatorOCR.Core.ModelPacks;
using GameTranslatorOCR.Core.Models;
using GameTranslatorOCR.Tracking;
using SkiaSharp;
using GameTranslatorOCR.Core.Detection;
using GameTranslatorOCR.Core.Imaging;
using GameTranslatorOCR.Core.Recognition;
using Microsoft.ML.OnnxRuntime.Tensors;

int passed = 0;
void Check(bool condition, string name)
{
    if (!condition)
        throw new InvalidOperationException($"TEST FAIL: {name}");
    passed++;
    Console.WriteLine($"PASS: {name}");
}

var tracker = new LineTracker();
var first = tracker.Update([new OcrLine("Hello", new OcrBox(10, 10, 100, 20), 0.95f)]);
Check(first.Count == 1 && first[0].Changed && first[0].Id == 1, "İlk kare yeni satır");
var same = tracker.Update([new OcrLine("Hello", new OcrBox(12, 10, 100, 20), 0.95f)]);
Check(same[0].Id == 1 && !same[0].Changed, "Sabit metin tekrarlanmaz");
var changed = tracker.Update([new OcrLine("World", new OcrBox(12, 10, 100, 20), 0.92f)]);
Check(changed[0].Id == 1 && changed[0].Changed, "Metin değişimi yakalanır");
var extra = tracker.Update([
    new OcrLine("World", new OcrBox(12, 10, 100, 20), 0.92f),
    new OcrLine("New", new OcrBox(12, 50, 100, 20), 0.89f)
]);
Check(extra.Count == 2 && extra[1].Id == 2 && extra[1].Changed, "Yeni satıra yeni kimlik");
Check(tracker.Update([]).Count == 0, "Kaybolan satır silinir");
var again = tracker.Update([new OcrLine("Hello", new OcrBox(10, 10, 100, 20), 0.91f)]);
Check(again[0].Id == 3 && again[0].Changed, "Kaybolan metin yeni olarak tanınır");
tracker.Reset();
Check(tracker.Update([new OcrLine("Start", new OcrBox(0, 0, 20, 20), 1f)])[0].Id == 1, "Reset kimlik sayacını sıfırlar");
Check(new OcrBox(0, 0, 20, 20).IntersectionOverUnion(new OcrBox(10, 0, 20, 20)) is > 0.3 and < 0.34, "Bounding box IoU");
Check(!ModelPackValidator.Validate("/not-existing-gametranslatorocr-pack").IsValid, "Eksik model paketi reddedilir");

// BGRA tam ekran kare analizi: başlangıç, sabit görüntü, yeni satır,
// periyodik yeniden tarama ve boyut değişimi.
static byte[] SolidFrame(int width, int height)
{
    var pixels = new byte[width * height * 4];
    for (int i = 3; i < pixels.Length; i += 4) pixels[i] = 255;
    return pixels;
}
static void WhiteRect(byte[] pixels, int width, int x1, int y1, int x2, int y2)
{
    for (int y = y1; y < y2; y++)
    for (int x = x1; x < x2; x++)
    {
        int i = (y * width + x) * 4;
        pixels[i] = pixels[i + 1] = pixels[i + 2] = pixels[i + 3] = 255;
    }
}

var analyzer = new FrameChangeAnalyzer(tileSize: 12, fullScanInterval: 4);
int fw = 192, fh = 96;
var frame = SolidFrame(fw, fh);
Check(analyzer.Analyze(frame, fw, fh, fw * 4).FullScanRequired, "İlk kare tam OCR");
Check(analyzer.Analyze(frame, fw, fh, fw * 4).IsUnchanged, "Sabit kare OCR atlar");
WhiteRect(frame, fw, 48, 36, 144, 54);
var dirty = analyzer.Analyze(frame, fw, fh, fw * 4);
Check(!dirty.FullScanRequired && dirty.ChangedRegions.Any(b =>
    b.X <= 48 && b.X + b.Width >= 144 && b.Y <= 36 &&
    b.Y + b.Height >= 54), "Yeni satır alanı yakalanır");
Check(analyzer.Analyze(frame, fw, fh, fw * 4).IsUnchanged, "Periyodik süre dolmadan OCR atlanır");
Check(analyzer.Analyze(frame, fw, fh, fw * 4).FullScanRequired, "Periyodik tam OCR");
Check(analyzer.Analyze(frame, fw, fh, fw * 4).IsUnchanged, "Tam tarama sonrası sabit kare");
var bigger = SolidFrame(216, fh);
Check(analyzer.Analyze(bigger, 216, fh, 216 * 4).FullScanRequired,
    "Çözünürlük değişince yeniden tam OCR");
analyzer.Reset();
Check(analyzer.Analyze(frame, fw, fh, fw * 4).FullScanRequired,
    "Reset yeni kareyi tam tarar");

// Yalnız renkten oluşan fark: kırmızı ~77 luma, koyu yeşil ~77 luma.
// Gri skala/yalnız luma analizi bu farkı kaçırabilir.
var chromaTracker = new FrameChangeAnalyzer(fullScanInterval: 60);
var colorFrame = SolidFrame(120, 96);
WhiteRect(colorFrame, 120, 24, 24, 60, 48);
for (int y = 24; y < 48; y++)
for (int x = 24; x < 60; x++)
{
    int i = (y * 120 + x) * 4;
    colorFrame[i] = 0; colorFrame[i + 1] = 0; colorFrame[i + 2] = 255;
}
Check(chromaTracker.Analyze(colorFrame, 120, 96, 120 * 4).FullScanRequired,
    "Renk analizi ilk kare tam tarama");
for (int y = 24; y < 48; y++)
for (int x = 24; x < 60; x++)
{
    int i = (y * 120 + x) * 4;
    colorFrame[i] = 0; colorFrame[i + 1] = 131; colorFrame[i + 2] = 0;
}
var colorChange = chromaTracker.Analyze(colorFrame, 120, 96, 120 * 4);
Check(!colorChange.FullScanRequired && !colorChange.IsUnchanged,
    "Benzer parlaklıkta renk değişimi tespit edilir");
Check(chromaTracker.Analyze(colorFrame, 120, 96, 120 * 4).IsUnchanged,
    "Renk değişimi işlendiğinde tekrar tetiklenmez");

// Önceki kareyle fark hep 5, ama 4 kare sonunda başlangıca göre fark 20.
// Referans tabanlı hesap bunu yakalamalı.
var accumulating = new FrameChangeAnalyzer(fullScanInterval: 80);
var dimFrame = SolidFrame(120, 96);
Check(accumulating.Analyze(dimFrame, 120, 96, 120 * 4).FullScanRequired,
    "Yavaş değişim başlangıç karesi");
bool accumulatedSeen = false;
for (int brightness = 5; brightness <= 35; brightness += 5)
{
    for (int y = 24; y < 48; y++)
    for (int x = 24; x < 60; x++)
    {
        int i = (y * 120 + x) * 4;
        dimFrame[i] = dimFrame[i + 1] = dimFrame[i + 2] = (byte)brightness;
    }
    var result = accumulating.Analyze(dimFrame, 120, 96, 120 * 4);
    accumulatedSeen |= !result.IsUnchanged;
}
Check(accumulatedSeen, "Kademeli parlaklık birikimi yakalanır");
Check(accumulating.Analyze(dimFrame, 120, 96, 120 * 4).IsUnchanged,
    "Sabit hale gelen sahnede OCR atlanır");

var layoutAnalyzer = new FrameChangeAnalyzer(fullScanInterval: 80);
Check(layoutAnalyzer.Analyze(dimFrame, 120, 96, 120 * 4).FullScanRequired,
    "BGRA formatı başlangıç tarama");
Check(layoutAnalyzer.Analyze(dimFrame, 120, 96, 120 * 4, FramePixelLayout.Rgba32).FullScanRequired,
    "Pixel layout değişince referans sıfırlanır");
try
{
    analyzer.Analyze(frame.AsSpan(0, 10), fw, fh, fw * 4);
    Check(false, "Eksik görüntü verisi reddedilir");
}
catch (ArgumentException)
{
    Check(true, "Eksik görüntü verisi reddedilir");
}

if (args.Length == 2)
{
    string modelDirectory = args[0];
    string imagePath = args[1];
    Check(ModelPackValidator.Validate(modelDirectory).IsValid, "Model dosyaları mevcut");
    Check(ModelPackIntegrity.Verify(modelDirectory).Count == 0, "Model SHA-256 doğrulama");
    using var engine = new OnnxGameOcrEngine(modelDirectory);
    var actual = await engine.RecognizeAsync(
        await File.ReadAllBytesAsync(imagePath), new OcrOptions("tr"));
    Check(actual.Lines.Any(x => x.Text == "GAME TRANSLATOR OCR"), "İngilizce başlık OCR");
    Check(actual.Lines.Any(x => x.Text == "Merhaba dünya!"), "Türkçe karakter OCR");
    Check(actual.Lines.Any(x => x.Text == "Quest completed"), "İngilizce metin OCR");
    Check(actual.Lines.All(x => x.Bounds.IsValid && x.Confidence > 0.5f),
        "Koordinatlar ve güven skorları");
    Console.WriteLine($"Model OCR testi: {actual.Lines.Count} satır, {actual.Elapsed.TotalMilliseconds:F0} ms");
    var enhancedOptions = new OcrOptions("tr",
        RecognitionBatchSize: 4,
        EnableArtifactFilter: true,
        ReturnWordBoxes: true);
    var enhanced = await engine.RecognizeAsync(
        await File.ReadAllBytesAsync(imagePath), enhancedOptions);
    Check(enhanced.Lines.Select(x=>x.Text).SequenceEqual(actual.Lines.Select(x=>x.Text)),
        "Batch OCR tekli metinlerle aynı");
    Check(enhanced.Lines.All(x=>x.Words.Count>0) &&
          enhanced.Lines.SelectMany(x=>x.Words).All(x=>x.Bounds.IsValid),
        "Kelime kutuları ve koordinatları üretilir");
    Check(enhanced.Lines.SelectMany(x=>x.Words).Any(x=>x.Text=="dünya!"),
        "Türkçe kelime hizalama");

    var angleMode = await engine.RecognizeAsync(
        await File.ReadAllBytesAsync(imagePath),
        new OcrOptions("tr",EnablePerspectiveCorrection:true));
    Check(angleMode.Lines.Any(x=>x.Text=="Merhaba dünya!"),
        "Perspektif düzeltme normal yazıyı bozmuyor");


    static byte[] ToBgra(SKBitmap bmp)
    {
        var raw = new byte[bmp.Width * bmp.Height * 4];
        for (int y = 0; y < bmp.Height; y++)
        for (int x = 0; x < bmp.Width; x++)
        {
            var c = bmp.GetPixel(x, y);
            int index = (y * bmp.Width + x) * 4;
            raw[index] = c.Blue;
            raw[index + 1] = c.Green;
            raw[index + 2] = c.Red;
            raw[index + 3] = 255;
        }
        return raw;
    }

    using var bmp = SKBitmap.Decode(imagePath);
    using var session = new SmartOcrSession(engine, new FrameChangeAnalyzer(fullScanInterval: 8));
    byte[] sourceBytes = await File.ReadAllBytesAsync(imagePath);
    byte[] sourceBgra = ToBgra(bmp);

    var rawResult = await engine.RecognizeBgraAsync(sourceBgra,
        bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
    Check(rawResult.Lines.Count == actual.Lines.Count &&
        rawResult.Lines.Select(x => x.Text).SequenceEqual(actual.Lines.Select(x => x.Text)),
        "Doğrudan BGRA OCR kodlanmış PNG ile aynı metni okur");
    Check(rawResult.Lines.All(x => x.Bounds.IsValid && x.Confidence > .5f),
        "Doğrudan BGRA koordinat ve güven skorları geçerli");

    // Ekran yakalama kaynaklarında satır başına padding olabiliyor.
    int paddedStride = bmp.Width * 4 + 16;
    var padded = new byte[paddedStride * bmp.Height];
    for (int row = 0; row < bmp.Height; row++)
        Array.Copy(sourceBgra, row * bmp.Width * 4, padded,
            row * paddedStride, bmp.Width * 4);
    var paddedResult = await engine.RecognizeBgraAsync(padded,
        bmp.Width, bmp.Height, paddedStride, new OcrOptions("tr"));
    Check(paddedResult.Lines.Select(x => x.Text)
        .SequenceEqual(rawResult.Lines.Select(x => x.Text)),
        "Padded BGRA stride OCR doğru");

    try
    {
        await engine.RecognizeBgraAsync(sourceBgra.AsMemory(0, 16),
            bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
        Check(false, "Eksik BGRA verisi reddedilir");
    }
    catch (ArgumentException)
    {
        Check(true, "Eksik BGRA verisi reddedilir");
    }

    // SmartOcrSession, IRawOcrEngine ile kodlanmış görüntü olmadan çalışmalı.
    using (var rawOnlySession = new SmartOcrSession(engine))
    {
        var rawOnlyResult = await rawOnlySession.ProcessAsync(ReadOnlyMemory<byte>.Empty,
            sourceBgra, bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
        Check(rawOnlyResult.OcrExecuted && rawOnlyResult.Lines.Count == 3,
            "Smart OCR ham BGRA ile PNG üretmeden ilk kareyi okur");
    }
    var sessionFirst = await session.ProcessAsync(sourceBytes, sourceBgra,
        bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
    Check(sessionFirst.OcrExecuted && sessionFirst.FullScan && sessionFirst.Lines.Count == 3,
        "Smart OCR ilk kare tam tarama");
    var sessionSame = await session.ProcessAsync(sourceBytes, sourceBgra,
        bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
    Check(!sessionSame.OcrExecuted && sessionSame.Lines.Count == 3,
        "Smart OCR aynı kareyi tekrar OCR etmez");

    // Sentetik ekranın yalnızca orta satırını sil, diğer satırları koru.
    using (var canvas = new SKCanvas(bmp))
    using (var paint = new SKPaint { Color = new SKColor(22, 28, 42) })
    {
        canvas.DrawRect(new SKRect(72, 216, 444, 277), paint);
        canvas.Flush();
    }
    using var imageWithRemovedLine = SKImage.FromBitmap(bmp);
    using var data = imageWithRemovedLine.Encode(SKEncodedImageFormat.Png, 100);
    byte[] changedFrame = data.ToArray();
    byte[] changedRaw = ToBgra(bmp);
    var partial = await session.ProcessAsync(changedFrame, changedRaw,
        bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
    Check(partial.OcrExecuted && !partial.FullScan,
        "Smart OCR değişen bölgeyi kısmi tarar");
    Check(!partial.Lines.Any(x => x.Text == "Merhaba dünya!") &&
        partial.Lines.Any(x => x.Text == "GAME TRANSLATOR OCR") &&
        partial.Lines.Any(x => x.Text == "Quest completed"),
        "Smart OCR silinen satırı kaldırır ve diğerlerini korur");
    var sessionChangedSame = await session.ProcessAsync(changedFrame, changedRaw,
        bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
    Check(!sessionChangedSame.OcrExecuted,
        "Smart OCR yeni sabit kareyi de atlar");

    // Bir sonraki karede daha önce silinmiş metnin geri gelmesi kaçırılmamalı.
    var restored = await session.ProcessAsync(sourceBytes, sourceBgra,
        bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"));
    Check(restored.OcrExecuted && !restored.FullScan &&
        restored.Lines.Any(x => x.Text == "Merhaba dünya!"),
        "Boş bölgeye yeniden gelen metin kısmi OCR ile bulunur");
    var oldHeader = sessionFirst.Lines.Single(x => x.Text == "GAME TRANSLATOR OCR");
    var newHeader = restored.Lines.Single(x => x.Text == "GAME TRANSLATOR OCR");
    Check(oldHeader.Id == newHeader.Id && !newHeader.Changed,
        "Değişmeyen komşu satırın kimliği korunur");

    // RGBA32 yakalama, doğrudan BGRA yolunu kullanamaz; PNG fallback korunmalı.
    var rgba = (byte[])sourceBgra.Clone();
    for (int index = 0; index < rgba.Length; index += 4)
        (rgba[index], rgba[index + 2]) = (rgba[index + 2], rgba[index]);
    using (var rgbaSession = new SmartOcrSession(engine))
    {
        var fallback = await rgbaSession.ProcessAsync(sourceBytes, rgba,
            bmp.Width, bmp.Height, bmp.Width * 4, new OcrOptions("tr"),
            FramePixelLayout.Rgba32);
        Check(fallback.OcrExecuted && fallback.Lines.Count == 3,
            "RGBA32 yakalamada kodlanmış görüntü fallback çalışır");
    }
}


Check(OcrArtifactFilter.ShouldReject(new RecognitionResult("□",.97f),
    new OcrBox(12,33,15,10)), "Küçük yanlış simge filtresi");
Check(!OcrArtifactFilter.ShouldReject(new RecognitionResult("□",.97f),
    new OcrBox(12,33,60,45)), "Büyük gerçek sembol kutusu korunur");
Check(!OcrArtifactFilter.ShouldReject(new RecognitionResult("Merhaba",.91f),
    new OcrBox(12,33,150,24)), "Normal yazı korunur");
Check(OcrArtifactFilter.ShouldReject(new RecognitionResult("abc",.2f),
    new OcrBox(12,33,150,24)), "Düşük güvenli OCR elenir");

using(var sm = new SKBitmap(200,100))
{
    using(var cn = new SKCanvas(sm))cn.Clear(SKColors.White);
    var pre = ImageTensorBuilder.BuildDetection(sm,960,minSide:736);
    Check(pre.Width>=200 && pre.Height>=100 &&
        pre.Tensor.Dimensions[0]==1,"Uyarlanabilir küçük görüntü büyütme");

    using var cropOne = ImageTensorBuilder.Crop(sm,0,0,70,26);
    using var cropTwo = ImageTensorBuilder.Crop(sm,0,0,100,26);
    var batch = ImageTensorBuilder.BuildRecognitionBatch([cropOne,cropTwo]);
    Check(batch.Tensor.Dimensions[0]==2 &&
        batch.UsedWidths[0]<batch.UsedWidths[1] &&
        batch.BatchWidth>=batch.UsedWidths[1],
        "Toplu tanıma ortak tensor genişliği");

    using var testPaint = new SKPaint{Color=SKColors.Black};
    using(var cx = new SKCanvas(sm))
        cx.DrawRect(new SKRect(18,13,80,38),testPaint);
    var quad=new OcrQuad(new OcrPoint(0,0),
        new OcrPoint(110,0),new OcrPoint(110,60),new OcrPoint(0,60));
    using var warped=PerspectiveCropper.Rectify(sm,quad);
    Check(warped.Width==110 && warped.Height==60 &&
        warped.GetPixel(30,20).Red<80,
        "Dörtgen perspektif crop piksel testi");
}
var pTensor=new DenseTensor<float>([1,1,128,256]);
for(int x=30;x<210;x++)
{
    int mid=(int)Math.Round(28+x*.15);
    for(int y=mid-3;y<=mid+3;y++)
        pTensor[0,0,y,x]=.95f;
}
var estimated=TextAngleEstimator.Estimate(pTensor,
    new OcrBox(15,15,220,65),256,128);
Check(estimated.HasValue && estimated.Value.SlopeDegrees>6 &&
      estimated.Value.SlopeDegrees<15,
    "DBNet çıktı haritasından eğimli dörtgen tahmini");

var dictionaryPath = args.Length==2
    ? Path.Combine(args[0],"charset.txt")
    : null;
if(dictionaryPath is not null)
{
    var ctc = new CtcDecoder(dictionaryPath);
    int vocabulary = File.ReadAllLines(dictionaryPath).Length+2;
    var mock = new DenseTensor<float>([2,7,vocabulary]);
    mock[0,0,1]=1f; mock[0,1,0]=1f;
    mock[0,2,vocabulary-1]=1f; mock[0,3,2]=1f;
    mock[0,4,2]=1f; mock[0,5,0]=1f;
    mock[1,0,3]=1f; mock[1,1,0]=1f;
    var decode = ctc.DecodeDetailed(mock,0);
    Check(decode.Words.Count==2 &&
          decode.Words[0].StartStep==0 &&
          decode.Words[1].StartStep==3,
          "CTC kelime zaman hizalama");
    Check(ctc.DecodeDetailed(mock,1).Recognition.Text.Length>0,
          "Batch CTC bağımsız satır çözme");

    var modelCharacters = File.ReadAllLines(dictionaryPath);
    int turkishS = Array.IndexOf(modelCharacters, "ş") + 1;
    int foreignS = Array.IndexOf(modelCharacters, "š") + 1;
    int turkishI = Array.IndexOf(modelCharacters, "ı") + 1;
    int foreignSComma = Array.IndexOf(modelCharacters, "ș") + 1;
    if (turkishS > 0 && foreignS > 0 && turkishI > 0 && foreignSComma > 0)
    {
        var alphabetMock = new DenseTensor<float>([1, 4, vocabulary]);
        alphabetMock[0, 0, foreignS] = .99f;
        alphabetMock[0, 0, turkishS] = .91f;
        alphabetMock[0, 1, 0] = 1f;
        alphabetMock[0, 2, foreignSComma] = .99f;
        alphabetMock[0, 2, turkishS] = .92f;
        alphabetMock[0, 3, 0] = 1f;
        Check(ctc.DecodeDetailed(alphabetMock).Recognition.Text == "šș",
            "Varsayılan çok dilli CTC bozulmadan çalışır");
        Check(ctc.DecodeDetailed(alphabetMock, turkishEnglishOnly: true)
                  .Recognition.Text == "şş",
            "Türkçe CTC benzer yabancı harfleri maskeleyebilir");
    }
}

Console.WriteLine($"Tüm testler geçti: {passed}");
return 0;
