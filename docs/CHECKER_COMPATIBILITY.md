# Đối chiếu checker gốc và bản tương thích

Đã chạy lại checker gốc sau khi đặt TEMP/TMP trong workspace trên Windows: **79 test pass, 4 lỗi kiểm bài, 0 cảnh báo**. Hai nguyên nhân dưới đây giải thích đủ bốn lỗi. Giữ nguyên script đề và file kết quả train; không bỏ bước kiểm test hoặc file bảo vệ.

## 1. Hai báo nhầm ở calibration

`scripts/check_submission.py:74` dùng `str(p.relative_to(ROOT))` để tra danh sách bảo vệ. Windows trả `pipeline\calibrate.py`, còn `_protected.json` lưu `pipeline/calibrate.py`. Vì chuỗi không khớp, checker quét nhầm file calibration đã viết sẵn và báo hai từ `MANIFEST`, `data/calib`.

Bản tương thích chỉ đổi biểu diễn đường dẫn sang `p.relative_to(ROOT).as_posix()` trong bộ nhớ. Vòng kiểm SHA1 toàn bộ file bảo vệ vẫn chạy trước đó như cũ.

## 2. Hai báo nhầm hash ở kết quả clean

`scripts/train_compare.py:72` lưu SHA1 của byte nguyên gốc manifest. Hàm `sha1` trong checker gốc (dòng 50–51) lại thay CRLF bằng LF; dòng 133 dùng hàm này để so với hash do train sinh.

| Đối tượng | SHA1 |
|---|---|
| Manifest nguyên byte, dùng để train | `b238dad931538e88b7b0c98dcf7cd09118622392` |
| Manifest sau đổi CRLF thành LF | `bc6d61def32b1272a3b83671b4ae70703b7d21bd` |
| `clean_seed0.json`, `clean_seed1.json` ghi nhận | `b238dad931538e88b7b0c98dcf7cd09118622392` |

Bản tương thích chỉ so manifest bằng `hashlib.sha1(mf.read_bytes()).hexdigest()`, cùng cách script train tạo hash. Hash sai thực sự vẫn bị chặn. Hash các file bảo vệ tiếp tục được chuẩn hoá xuống dòng như đề.

Đã kiểm thêm: bốn run cùng config/model/epoch/batch/imgsz, đủ seed 0/1; 205 hash nhãn khớp manifest; kết quả nhập nguyên byte từ ZIP; dữ liệu export trong Git index giữ đúng byte đã train. `.gitattributes` đặt `-text` cho export để Git không tự đổi xuống dòng và làm mất truy vết. Không sửa các file do pipeline/train sinh.

## Chạy trên máy này

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe scripts/check_submission_windows.py
```

Kết quả bản tương thích: **79 test pass, 0 lỗi, 0 cảnh báo**. Đây không phải tuyên bố checker gốc đã chạy sạch; cần giữ ghi chú tương thích khi nộp hoặc đối chiếu với giảng viên.

## Giải thích bốn module để đối chiếu

| Module | Logic cần hiểu |
|---|---|
| `label_format` | Đọc dòng YOLO, giữ số dòng gốc; lỗi parse/ID/kích thước không dương thì dừng kiểm hình học dòng đó. So mép box với ảnh, IoU với các box cùng lớp phía trước; chỉ đọc dữ liệu. |
| `second_opinion` | Dự đoán đủ confidence và diện tích mới dùng cảnh báo thiếu/sai lớp/box lỏng. Box nhãn được so thêm với dự đoán qua ngưỡng `fp_conf` riêng để cảnh báo box thừa. Có nhãn cùng lớp phù hợp thì ưu tiên nó. Tất cả chỉ là cảnh báo cho người. |
| `autofix` | Chỉ sửa bản sao, chỉ xử lý ERROR. Gom lỗi theo file và số dòng gốc; bỏ dòng thắng cắt box. Thiếu file nhãn thì ghi `needs_label`, không tạo nhãn rỗng. Mỗi sửa có before/after. |
| `gate` | Có bất kỳ ERROR nào thì Rework, kể cả ảnh đã duyệt. Nếu không, đếm ảnh khác nhau còn WARN và chưa được duyệt; chia cho tổng ảnh. Từ 10% là Hold, dưới 10% là Release. |
