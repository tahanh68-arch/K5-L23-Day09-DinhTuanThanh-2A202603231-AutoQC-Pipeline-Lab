"""Bonus: cảnh báo box quá dài hoặc quá mảnh theo kích thước pixel.

run(ds, cfg) -> list[Issue], chỉ đọc ảnh/nhãn.
Ngưỡng cfg['aspect_ratio']['max_ratio'] áp dụng cho cạnh dài / cạnh ngắn.
Box có tỉ lệ đúng bằng ngưỡng không bị cờ. Lỗi định dạng, ID hoặc diện tích
không hợp lệ thuộc check khác nên được bỏ qua. Cảnh báo không chứng minh
nhãn sai: vật bị che khuất hay sát mép ảnh có thể có box dài hợp lệ.
"""
import math

from ..common import WARN, Issue, parse_yolo_line


def run(ds, cfg):
    limit = float(cfg["aspect_ratio"]["max_ratio"])
    if not math.isfinite(limit) or limit <= 1:
        raise ValueError("aspect_ratio.max_ratio phải là số hữu hạn lớn hơn 1")
    issues = []
    for image in ds.image_files():
        size = ds.image_size(image.stem)
        if not size or min(size) <= 0:
            continue
        for no, text in ds.read_label_lines(image.stem) or []:
            try:
                cls, _, _, width, height = parse_yolo_line(text)
            except (ValueError, OverflowError):
                continue
            if not 0 <= cls < len(ds.classes) or width <= 0 or height <= 0:
                continue
            width_px, height_px = width * size[0], height * size[1]
            if not all(math.isfinite(v) and v > 0 for v in (width_px, height_px)):
                continue
            ratio = max(width_px, height_px) / min(width_px, height_px)
            if math.isfinite(ratio) and ratio > limit:
                issues.append(Issue(
                    "aspect_ratio", WARN, "BOX_EXTREME_ASPECT", image.stem,
                    f"box {width_px:.2f} x {height_px:.2f}px, cạnh dài/ngắn={ratio:.2f} > {limit:g}; cần người xem",
                    no, {"aspect_ratio": ratio, "width_px": width_px,
                         "height_px": height_px, "max_ratio": limit},
                ))
    return issues
