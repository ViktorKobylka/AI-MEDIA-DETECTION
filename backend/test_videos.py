import json
import logging
import time
from pathlib import Path

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("video_test")

DATASET_DIR  = Path("video_dataset")
RESULTS_FILE = Path("video_test_results.json")
VIDEO_EXTS   = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
FRAMES       = 30
SKIP         = 10


def predict_video(detector, video_path: Path) -> dict:
    """Run frame-by-frame detection on a single video."""
    try:
        import cv2
        import torch
        from torchvision import transforms
        from PIL import Image

        tf = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225]),
        ])

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {"error": "cannot open video"}

        total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps    = cap.get(cv2.CAP_PROP_FPS)

        scores = []
        idx    = 0

        while cap.isOpened() and len(scores) < FRAMES:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % SKIP == 0:
                rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img   = Image.fromarray(rgb)
                tensor = tf(img).unsqueeze(0).to(detector.device)
                with torch.no_grad():
                    logit = detector._model(tensor)
                score = float(torch.sigmoid(logit).item())
                scores.append(score)
            idx += 1

        cap.release()

        if not scores:
            return {"error": "no frames extracted"}

        avg_score  = sum(scores) / len(scores)
        fake_count = sum(1 for s in scores if s >= 0.5)
        fake_ratio = fake_count / len(scores)

        if fake_ratio >= 0.6:
            verdict    = "AI-GENERATED"
            confidence = "HIGH" if avg_score >= 0.75 else "MEDIUM"
        elif fake_ratio >= 0.35:
            verdict    = "UNCERTAIN"
            confidence = "LOW"
        else:
            verdict    = "REAL"
            confidence = "HIGH" if avg_score <= 0.25 else "MEDIUM"

        return {
            "frames_sampled": len(scores),
            "ai_frame_count": fake_count,
            "ai_frame_ratio": round(fake_ratio, 3),
            "avg_score":      round(avg_score, 4),
            "verdict":        verdict,
            "confidence":     confidence,
            "duration_s":     round(total / fps, 1) if fps > 0 else None,
        }

    except Exception as e:
        return {"error": str(e)}


def run():
    from nn_detector import NNDetector
    detector = NNDetector()

    folders = {"fake": [], "real": []}
    for folder in ["fake", "real"]:
        path = DATASET_DIR / folder
        if path.exists():
            folders[folder] = sorted(
                f for f in path.iterdir()
                if f.suffix.lower() in VIDEO_EXTS
            )

    total_videos = sum(len(v) for v in folders.values())
    if total_videos == 0:
        print("No videos found in video_dataset/fake/ or video_dataset/real/")
        return

    print(f"\nTesting {total_videos} videos...\n")

    all_results  = []
    correct      = 0
    total        = 0

    for gt_label, videos in folders.items():
        if not videos:
            continue

        print(f"{'='*60}")
        print(f"  {gt_label.upper()} videos ({len(videos)} files)")
        print(f"{'='*60}")

        for video_path in videos:
            t0     = time.time()
            result = predict_video(detector, video_path)
            elapsed = time.time() - t0

            verdict    = result.get("verdict", "ERROR")
            confidence = result.get("confidence", "-")
            avg_score  = result.get("avg_score", -1)
            error      = result.get("error")

            if error:
                status = "ERROR"
                mark   = "!"
            else:
                predicted_fake = verdict == "AI-GENERATED"
                actual_fake    = gt_label == "fake"
                correct_pred   = predicted_fake == actual_fake
                mark   = "✓" if correct_pred else "✗"
                status = verdict
                if correct_pred:
                    correct += 1
                total += 1

            print(f"  {mark} {video_path.name:<35} "
                  f"{status:<15} score={avg_score:.3f}  "
                  f"conf={confidence:<7}  ({elapsed:.1f}s)")

            all_results.append({
                "file":        str(video_path),
                "ground_truth": gt_label,
                "verdict":     verdict,
                "confidence":  confidence,
                "correct":     mark == "✓",
                **{k: v for k, v in result.items() if k != "error"},
            })

        print()

    # Summary
    accuracy = correct / total * 100 if total > 0 else 0
    fake_results  = [r for r in all_results if r["ground_truth"] == "fake"]
    real_results  = [r for r in all_results if r["ground_truth"] == "real"]
    fake_correct  = sum(1 for r in fake_results if r.get("correct"))
    real_correct  = sum(1 for r in real_results if r.get("correct"))

    print(f"{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Total videos:    {total}")
    print(f"  Correct:         {correct} / {total} = {accuracy:.1f}%")
    if fake_results:
        print(f"  AI-gen correct:  {fake_correct} / {len(fake_results)} = "
              f"{fake_correct/len(fake_results)*100:.1f}%")
    if real_results:
        print(f"  Real correct:    {real_correct} / {len(real_results)} = "
              f"{real_correct/len(real_results)*100:.1f}%")
    print(f"{'='*60}\n")

    RESULTS_FILE.write_text(json.dumps(all_results, indent=2))
    print(f"Full results saved to: {RESULTS_FILE.resolve()}")


if __name__ == "__main__":
    run()
