# Bonus +3 — Box có tỉ lệ cạnh bất thường

Theo RUBRIC.md, phần thưởng +3 yêu cầu một check mới có test. Check này bổ sung phát hiện hình dạng box quá dài/mảnh, khác với BOX_TINY kiểm cạnh ngắn và BOX_HUGE kiểm diện tích.

## Quy tắc

Với ảnh rộng W, cao H và box YOLO có chiều rộng w, chiều cao h chuẩn hoá:

```text
width_px  = w * W
height_px = h * H
ratio = max(width_px, height_px) / min(width_px, height_px)
ratio > cfg["aspect_ratio"]["max_ratio"] -> WARN BOX_EXTREME_ASPECT
```

Ngưỡng mặc định 10:1 nằm trong `configs/bonus.yaml`. Ví dụ ảnh 400×200, box w=0,4 và h=0,04 có kích thước 160×8 px, ratio=20: bị cảnh báo. Nếu chỉ dùng w/h sẽ tính nhầm là 10 và bỏ sót. Đúng bằng ngưỡng thì không cờ.

Check dùng giao diện `run(ds, cfg) -> list[Issue]`, trả tên ảnh, số dòng gốc, ratio, kích thước pixel và ngưỡng. Dòng sai định dạng/ID, box không có diện tích và ảnh không đọc được kích thước được bỏ qua để check lõi xử lý. Thứ tự ảnh/dòng ổn định; không ghi nhãn hoặc sửa ảnh.

## Chạy và xem bằng chứng

```powershell
.\.venv\Scripts\python.exe -m pytest bonus_tests -q
.\.venv\Scripts\python.exe -m pipeline.bonus
```

Máy Linux/macOS có thể thay đường dẫn Python bằng `python`. Runner tạo ba file trong `submission/bonus/`: `aspect_ratio.csv`, `aspect_ratio.txt`, `summary.json`. Có thể kiểm bản sao sau QC bằng `python -m pipeline.bonus --dataset work/run/ds --out work/bonus_after`.

Trên dữ liệu raw: **224 ảnh, 0 cảnh báo ở ngưỡng 10:1**. Đây là kết quả kiểm quy tắc hình học, không phải kết luận dataset không có lỗi. Không thay ngưỡng để tạo cảnh báo cho đủ số.

18 test mới ở `bonus_tests/test_aspect_ratio.py` bao gồm: chuyển sang pixel trên ảnh không vuông, box dọc/ngang, biên đúng ngưỡng, ngưỡng cấu hình, dòng trống và dòng hỏng, lớp sai, box rỗng, ảnh hỏng, đuôi JPG hoa, ngưỡng cấu hình không hợp lệ, runner không sửa nguồn, chạy hai lần cùng kết quả và từ chối ghi báo cáo trong dataset đầu vào. Pytest toàn repo tự thu thập các test này cùng 79 test gốc.

## Giới hạn và cách tích hợp

10:1 là heuristic thận trọng, chưa có đáp án gán sẵn để calibration. Vật thể dài, người bị che hoặc tư thế đặc biệt vẫn có thể có box hợp lệ; WARN cần người xem, không tự xoá hoặc cắt nhãn. Check này không xác nhận lớp hoặc vật thể có tồn tại.

Registry `pipeline/checks/__init__.py`, orchestrator, cấu hình lõi và test gốc đều được bảo vệ nên giữ nguyên. `pipeline/bonus.py` gọi check mới và bộ ghi báo cáo có sẵn bằng một lệnh riêng. Báo cáo lõi, manifest và kết quả train không bị thay đổi; bonus không được dùng để tuyên bố Release hoặc cải thiện mAP.
