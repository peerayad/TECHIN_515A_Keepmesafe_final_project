# ML Training Report — Person Detection CNN
**Project:** GuardianPod | **Owner:** Proud | **Run #:** `1` ()
 
---
 
## 1. Run Info
| Field | Value |
|---|---|
| Date | April 10, 2026 |
| Run # | 1 |
| Epochs | 20 |
| Batch Size | 16 |
| Learning Rate | 0.001 |
| Device | Apple MPS (MacBook Air) |
 
---
 
## 2. Dataset
| Split | Person | Non-Person | Total |
|---|---|---|---|
| Training | 700 | 699 | 1,399 |
| Testing | 170 | 171 | 341 |
 
---
 
## 3. Results
| Metric | Value | Target | Status |
|---|---|---|---|
| Best Val Accuracy | 68.9% | ≥ 85% | ❌ |
| Best Epoch | 17 | — | — |
| False Positive Rate | 30.5% | < 10% | ❌ |
| False Negative Rate | 31.8% | < 15% | ❌ |
| Inference Time | Not tested | < 500 ms | ⏳ |
 
---
 
## 4. Confusion Matrix
|  | Pred: No | Pred: Yes |
|---|---|---|
| **Actual: No** | TN = 119 | FP = 52 |
| **Actual: Yes** | FN = 54 | TP = 116 |
 
---
 
## 5. Epoch Log
| Epoch | Train Acc | Train Loss | Val Acc | Val Loss | Saved |
|---|---|---|---|---|---|
| 1 | 50.0% | 0.773 | 51.0% | 0.691 | ✅ |
| 2 | 50.1% | 0.706 | 52.5% | 0.693 | ✅ |
| 3 | 53.9% | 0.699 | 49.9% | 0.692 | |
| 4 | 53.5% | 0.693 | 50.1% | 0.707 | |
| 5 | 52.0% | 0.695 | 52.8% | 0.687 | ✅ |
| 6 | 55.0% | 0.692 | 51.6% | 0.691 | |
| 7 | 53.5% | 0.693 | 57.5% | 0.688 | ✅ |
| 8 | 52.0% | 0.698 | 51.0% | 0.693 | |
| 9 | 54.0% | 0.689 | 50.4% | 0.706 | |
| 10 | 55.0% | 0.684 | 56.6% | 0.682 | |
| 11 | 56.8% | 0.676 | 63.0% | 0.661 | ✅ |
| 12 | 58.5% | 0.677 | 63.0% | 0.652 | |
| 13 | 63.1% | 0.660 | 63.6% | 0.638 | ✅ |
| 14 | 60.2% | 0.667 | 65.7% | 0.648 | ✅ |
| 15 | 62.9% | 0.655 | 64.5% | 0.646 | |
| 16 | 63.8% | 0.651 | 67.4% | 0.616 | ✅ |
| **17** | **64.0%** | **0.655** | **68.9%** | **0.622** | **✅ BEST** |
| 18 | 62.6% | 0.650 | 64.2% | 0.629 | |
| 19 | 66.5% | 0.640 | 67.7% | 0.628 | |
| 20 | 64.0% | 0.638 | 65.1% | 0.621 | |
 
---
 
## 6. Bugs / Errors
| Error | Fix | Status |
|---|---|---|
| `ReduceLROnPlateau` got unexpected keyword `verbose` | Removed `verbose=True` from scheduler init | ✅ Fixed |
 
---
 
## 7. Notes
> Model is underfitting — train acc (64%) ≈ val acc (68.9%), both too low.
> Epochs 1–10 were near random (~50%), model only started learning at Epoch 11.
> Still improving at Epoch 20, needs more epochs.
 
- Learning rate 0.001 may be too high → causing oscillation in early epochs
- FN rate 31.8% too high for security use case (missing real intruder)
- Dataset balanced (700 vs 699) so class imbalance is not the issue
 
---
 
## 8. Next Run Changes
- [ ] Increase epochs to 40–50
- [ ] Lower lr to 0.0005
- [ ] Add more augmentation (random crop, brightness)
- [ ] Test webcam after training
 
---
**Overall:** ❌ FAIL — Best Val 68.9%, target ≥ 85%
 