"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401


def run(ds, cfg):
    c = cfg["label_format"]
    issues = []
    for path in ds.label_files():
        stem, previous = path.stem, []
        size = ds.image_size(stem)
        for no, text in ds.read_label_lines(stem) or []:
            def add(code, message, severity=ERROR, **extra):
                issues.append(Issue("label_format", severity, code, stem, message, no, extra))

            try:
                cls, x, y, w, h = parse_yolo_line(text)
            except (ValueError, OverflowError):
                add("BAD_FORMAT", "dòng nhãn phải gồm 5 số hữu hạn, ID nguyên")
                continue
            if not 0 <= cls < len(ds.classes):
                add("BAD_CLASS_ID", f"ID lớp {cls} ngoài danh sách dự án")
                continue
            if w <= 0 or h <= 0:
                add("BOX_ZERO", "chiều rộng hoặc chiều cao không dương")
                continue
            box = (x, y, w, h)
            overflow = max(0, w / 2 - x, h / 2 - y, x + w / 2 - 1, y + h / 2 - 1)
            if overflow > c["overflow_tol"]:
                add("BOX_OUT_OF_IMAGE", f"box tràn ảnh {overflow:.6f}", overflow=overflow)
            if any(cls == old_cls and iou_xywh(box, old_box) > c["dup_box_iou"]
                   for old_cls, old_box in previous):
                add("DUP_BOX", "box trùng với dòng cùng lớp phía trước")
            previous.append((cls, box))
            if size and min(w * size[0], h * size[1]) < c["min_box_px"]:
                add("BOX_TINY", "cạnh ngắn của box dưới ngưỡng pixel", WARN)
            if w * h > c["max_box_frac"]:
                add("BOX_HUGE", "box phủ quá nhiều diện tích ảnh", WARN)
    return issues
