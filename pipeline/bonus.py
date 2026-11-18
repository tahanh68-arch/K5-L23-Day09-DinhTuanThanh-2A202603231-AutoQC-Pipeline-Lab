"""Chạy check bonus chỉ đọc, không sửa dataset hoặc kết quả pipeline lõi.

    python -m pipeline.bonus
    python -m pipeline.bonus --dataset work/run/ds --out work/bonus_after

Cảnh báo vẫn trả mã 0: đây là báo cáo bổ sung cho người duyệt.
"""
import argparse
import json
import yaml

from .checks import aspect_ratio
from .common import ROOT, Dataset, load_config
from .steps.report import write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/raw")
    parser.add_argument("--config", default="configs/bonus.yaml")
    parser.add_argument("--out", default="submission/bonus")
    args = parser.parse_args(argv)
    dataset = (ROOT / args.dataset).resolve()
    out = (ROOT / args.out).resolve()
    if not (dataset / "images").is_dir():
        parser.error(f"không có thư mục ảnh: {dataset / 'images'}")
    if out.is_relative_to(dataset):
        parser.error("thư mục báo cáo phải nằm ngoài dataset đầu vào")
    cfg = load_config()
    cfg["aspect_ratio"] = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))["aspect_ratio"]
    ds = Dataset(dataset, cfg["classes"])
    issues = aspect_ratio.run(ds, cfg)
    n_images = len(ds.image_files())
    n_warn_images = len({issue.image for issue in issues})
    write_report(issues, out / "aspect_ratio", "Bonus — box có tỉ lệ cạnh bất thường", n_images)
    summary = dict(
        check="aspect_ratio", dataset=dataset.relative_to(ROOT).as_posix() if dataset.is_relative_to(ROOT) else str(dataset),
        max_ratio=cfg["aspect_ratio"]["max_ratio"], n_images=n_images,
        n_issues=len(issues), n_warn_images=n_warn_images,
        warn_ratio=round(n_warn_images / n_images, 4) if n_images else 0.0,
        note="Chỉ cảnh báo cho người xem; không tự sửa nhãn, không thay đổi quyết định QC hoặc dữ liệu train.",
    )
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Bonus: quét {n_images} ảnh; {len(issues)} box bất thường trên {n_warn_images} ảnh -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
