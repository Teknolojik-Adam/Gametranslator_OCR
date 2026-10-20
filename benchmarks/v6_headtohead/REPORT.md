# GameTranslatorOCR vs RapidOCR PP-OCRv6 (Fedora CPU)

Both used already installed models, no downloads. Tests: 11/33 original images/lines + 10/30 new images/lines, 2 passes each.
Hybrid: v5 detector + v6 recognizer + 6px crop. RapidOCR: v6 detector + v6 recognizer.

| Set | Engine | Noise-filtered joined text accuracy | Exact lines | Exact-line precision | Exact-line F1 | Extra square boxes | Mean CPU | p95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| original | GameTranslatorOCR hybrid | 100.0% | 33/33 | 100.0% | 100.0% | 0 | 210.7 ms | 237.5 ms |
| original | RapidOCR PP-OCRv6 | 99.82% | 32/33 | 96.97% | 96.97% | 0 | 328.7 ms | 352.3 ms |
| holdout | GameTranslatorOCR hybrid | 100.0% | 30/30 | 88.24% | 93.75% | 4 | 198.6 ms | 225.8 ms |
| holdout | RapidOCR PP-OCRv6 | 100.0% | 30/30 | 58.82% | 74.07% | 21 | 358.1 ms | 576.5 ms |

Accuracy ignores only standalone square (□) false boxes, which are counted separately as extra detections. Ordering differences can still affect joined-text accuracy.
Exact-line precision counts ALL detected text boxes including extraneous boxes.
Scores on synthetic images do not establish real game accuracy, and model detectors are not identical.

## Notable mismatches
### original
#### game_hybrid_tuned
#### rapid_default
- 06_low_contrast.png: correct 2/3, extra squares 0, detected ['The mission begins', 'Yeni görev alindı', 'Return to base']
### holdout
#### game_hybrid_tuned
- H01_unseen.png: correct 3/3, extra squares 3, detected ['□', 'Işığa doğru', '□', '□', 'Kapı kilitli', 'Run quickly']
- H06_unseen.png: correct 3/3, extra squares 1, detected ['Press SPACE', 'Hedefe yaklaşıyoruz', 'Karanlık çöktü', '□']
#### rapid_default
- H01_unseen.png: correct 3/3, extra squares 14, detected ['□', '□', '□', 'Işığa doğru', '□', '□', '□', '□', '□', 'Kapı kilitli', '□', '□', '□', '□', 'Run quickly', '□', '□']
- H06_unseen.png: correct 3/3, extra squares 7, detected ['□', '□', 'Press SPACE', '□', '□', '□', 'Hedefe yaklaşıyoruz', '□', 'Karanlık çöktü', '□']
