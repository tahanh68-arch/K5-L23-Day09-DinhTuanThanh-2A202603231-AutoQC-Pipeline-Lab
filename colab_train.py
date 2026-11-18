"""Upload to Google Colab and run: %run /content/colab_train.py

Select Runtime > Change runtime type > T4 GPU before running.
Runs the original training/comparison scripts; no fabricated metrics.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

REPO_URL = "https://github.com/tahanh68-arch/K5-L23-Day09-DinhTuanThanh-2A202603231-AutoQC-Pipeline-Lab.git"
SEEDS = [0, 1]
EPOCHS = 20
BATCH = 16
IMGSZ = 640


def run(*args, cwd=None):
    subprocess.run([str(a) for a in args], cwd=cwd, check=True)


def main():
    try:
        from google.colab import files
    except ImportError as exc:
        raise RuntimeError("Chạy file này trong Google Colab với GPU T4.") from exc

    print("1/6 — Kiểm tra GPU", flush=True)
    try:
        run("nvidia-smi", "-L")
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Chọn Runtime > Change runtime type > T4 GPU rồi chạy lại.") from exc

    # A new checkout per invocation avoids reusing stale data or partial results.
    import tempfile
    repo = Path(tempfile.mkdtemp(prefix="day09_", dir="/content")) / "repo"
    print("2/6 — Clone repo và kiểm tra export", flush=True)
    run("git", "clone", "--depth", "1", REPO_URL, repo)
    manifest_path = repo / "submission/export/clean_v1/manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("Repo GitHub chưa có clean_v1/manifest.json; cần push export trước khi train.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print("Quyết định QC:", manifest["decision"]["decision"],
          "— số ảnh clean:", manifest["n_images"], flush=True)
    print("Dataset Hold là bản nháp cho thí nghiệm, chưa được phát hành.", flush=True)
    run("git", "log", "-1", "--oneline", cwd=repo)

    print("3/6 — Cài thư viện theo requirements-train.txt", flush=True)
    os.environ["YOLO_CONFIG_DIR"] = str(repo / "work/yolo_settings")
    run(sys.executable, "-m", "pip", "install", "-q", "-r", repo / "requirements-train.txt")
    run(sys.executable, "-c",
        "import torch; assert torch.cuda.is_available(), 'PyTorch chưa nhận GPU'; "
        "print('GPU:', torch.cuda.get_device_name(0))")

    print("4/6 — Train raw/clean, 2 seed × 20 epoch (bốn lần train)", flush=True)
    run(sys.executable, "scripts/train_compare.py", "--variants", "raw", "clean",
        "--seeds", *SEEDS, "--epochs", EPOCHS, "--batch", BATCH,
        "--imgsz", IMGSZ, "--device", "0", cwd=repo)

    print("5/6 — Tổng hợp kết quả thật", flush=True)
    run(sys.executable, "scripts/summarize_results.py", cwd=repo)
    results = repo / "submission/results"
    required = [f"{variant}_seed{seed}.json" for variant in ("raw", "clean") for seed in SEEDS]
    for name in required:
        if not (results / name).exists():
            raise RuntimeError(f"Thiếu kết quả {name}; không đóng gói bài train chưa hoàn tất.")
    print((results / "comparison.md").read_text(encoding="utf-8"), flush=True)

    print("6/6 — Tải results.zip", flush=True)
    archive = Path("/content/day09_results.zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(results.iterdir()):
            if path.is_file() and path.suffix in {".json", ".md", ".png"}:
                z.write(path, Path("submission/results") / path.name)
    print("Giải nén ZIP vào repo local, giữ thư mục submission/results/.", flush=True)
    files.download(str(archive))


if __name__ == "__main__":
    main()
