"""
Evaluate trained NN detector (MobileNetV4) on the full dataset.
"""
import logging
from pathlib import Path
from datetime import datetime

DATASET_DIR  = Path("dataset_extra")
RESULTS_FILE = Path("results_nn_1.txt")
IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".webp"}

logging.getLogger().setLevel(logging.WARNING)


def get_images(folder):
    return sorted(f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTS)


def run():
    from nn_detector import NNDetector
    detector     = NNDetector()
    folders      = sorted(d for d in DATASET_DIR.iterdir() if d.is_dir())
    all_results  = []
    folder_stats = {}

    for folder in folders:
        images = get_images(folder)
        if not images:
            continue
        gt    = "real" if folder.name == "real" else "fake"
        stats = {"correct": 0, "total": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}
        print(f"\n[{folder.name}] {len(images)} images (ground truth: {gt.upper()})")

        for img_path in images:
            try:
                result    = detector.predict(str(img_path))
                predicted = result["prediction"]
                score     = result["final_score"]
                correct   = predicted == gt
            except Exception as e:
                predicted, score, correct = "error", -1.0, False
                print(f"  ERROR: {img_path.name} — {e}")

            stats["total"] += 1
            if correct:
                stats["correct"] += 1
            if gt == "fake" and predicted == "fake": stats["tp"] += 1
            elif gt == "real" and predicted == "fake": stats["fp"] += 1
            elif gt == "real" and predicted == "real": stats["tn"] += 1
            elif gt == "fake" and predicted == "real": stats["fn"] += 1

            all_results.append({
                "folder": folder.name, "file": img_path.name,
                "ground_truth": gt, "predicted": predicted,
                "correct": correct, "score": score,
            })
            mark = "✓" if correct else "✗"
            print(f"  {mark} {img_path.name:<35} {score:.3f} → {predicted.upper()}")

        acc = stats["correct"] / stats["total"] * 100
        folder_stats[folder.name] = stats
        print(f"  → Accuracy: {stats['correct']}/{stats['total']} = {acc:.1f}%")

    write_report(all_results, folder_stats)
    print(f"\nResults saved to: {RESULTS_FILE.resolve()}")


def write_report(all_results, folder_stats):
    lines = [
        "=" * 65,
        "  NN DETECTOR (MobileNetV4-Conv-Small, 2024) — EVALUATION REPORT",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 65, "",
        "PER-FOLDER SUMMARY", "-" * 65,
        f"  {'Folder':<25} {'GT':<5} {'Correct':>8} {'Total':>6} {'Accuracy':>9}",
        "  " + "-" * 55,
    ]

    tc, tt = 0, 0
    for name, s in folder_stats.items():
        gt  = "REAL" if name == "real" else "FAKE"
        acc = s["correct"] / s["total"] * 100 if s["total"] > 0 else 0
        lines.append(f"  {name:<25} {gt:<5} {s['correct']:>8} {s['total']:>6} {acc:>8.1f}%")
        tc += s["correct"]
        tt += s["total"]

    ov_acc = tc / tt * 100
    lines += [f"  {'OVERALL':<25} {'':5} {tc:>8} {tt:>6} {ov_acc:>8.1f}%", ""]

    tp = sum(s["tp"] for s in folder_stats.values())
    fp = sum(s["fp"] for s in folder_stats.values())
    fn = sum(s["fn"] for s in folder_stats.values())
    prec = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    rec  = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

    lines += [
        "OVERALL METRICS", "-" * 65,
        f"  Precision: {prec:.1f}%",
        f"  Recall:    {rec:.1f}%",
        f"  F1 Score:  {f1:.1f}%",
        f"  Accuracy:  {ov_acc:.1f}%", "", "=" * 65,
    ]

    RESULTS_FILE.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()