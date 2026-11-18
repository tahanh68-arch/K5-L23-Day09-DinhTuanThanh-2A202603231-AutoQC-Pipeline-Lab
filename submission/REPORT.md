# Báo cáo Day 09 — Đinh Tuấn Thành, 2A202603231

## 1. Kết luận trước

**Hold**: đầu vào 224 ảnh, loại 19 ảnh, xuất 205 ảnh dưới dạng **bản nháp**. Sau tự sửa và người duyệt mô phỏng 80 ảnh, không còn lỗi bắt buộc; 38/205 ảnh (18,54%) còn cảnh báo chưa duyệt, vượt ngưỡng 10%. Nguồn: `01_intake.csv`, `08_summary.json`, `export/clean_v1/manifest.json`.

## 2. Lỗi và phân việc

Số từ `02_error_list_v1.csv`: **issue / số ảnh khác nhau**; mẫu số 224 ảnh cho intake, 205 ảnh cho QC. YAML và thống kê lớp là cấp dataset; nhiều nhóm có thể cùng xuất hiện trên một ảnh.

| Mã lỗi | Issue / ảnh | Ai xử lý, lý do |
|---|---:|---|
| CORRUPT_IMAGE | 2 / 2 | Máy loại ảnh không đọc được |
| BAD_SIZE | 3 / 3 | Máy loại ảnh dưới độ phân giải |
| DUP_IMAGE_EXACT | 8 / 8 | Máy loại bản trùng byte |
| DUP_IMAGE_NEAR | 2 / 2 | Máy loại bản gần trùng |
| LEAK_TEST | 4 / 4 | Máy loại ảnh trùng test/val |
| MISSING_LABEL_FILE | 6 / 6 | Người gán; máy không tạo nhãn rỗng |
| BAD_FORMAT | 3 / 3 | Máy bỏ dòng không đọc được |
| BAD_CLASS_ID | 6 / 6 | Máy bỏ dòng sai ID |
| BOX_ZERO | 4 / 4 | Máy bỏ box không có diện tích |
| BOX_OUT_OF_IMAGE | 8 / 8 | Máy cắt box về trong ảnh |
| DUP_BOX | 7 / 7 | Máy bỏ dòng trùng phía sau |
| BAD_CLASS_NAME | 2 / 1 YAML | Máy chuẩn hoá tên lớp |
| EMPTY_LABEL | 12 / 12 | Người xác nhận ảnh nền hay thiếu nhãn |
| BOX_TINY | 6 / 4 | Người kiểm guideline vật nhỏ |
| BOX_HUGE | 3 / 3 | Người xác nhận box quá lớn |
| CLASS_RARE | 4 / cấp dataset | Người xem thống kê; có token ID lỗi trước sửa |
| POSSIBLE_MISSING | 53 / 52 | Người kiểm vật bị thiếu |
| POSSIBLE_WRONG_CLASS | 18 / 18 | Người xác nhận lớp |
| POSSIBLE_LOOSE_BOX | 28 / 24 | Người kiểm độ khít box |
| POSSIBLE_FALSE_POS | 29 / 27 | Người kiểm box thừa |

`03_fixes.csv` có 35 bản ghi: 20 bỏ dòng, 8 cắt box, 1 sửa tên lớp, 6 chuyển người gán. Hàng đợi sau sửa có 125 ảnh. Điểm ưu tiên cộng trọng số lỗi, confidence và dấu vết tự sửa: `img_0020` đứng đầu (11,524 điểm), sau đó sáu ảnh thiếu nhãn (10 điểm/ảnh). Duyệt mô phỏng 80/125 ảnh, trong đó 74 ảnh có cảnh báo ngữ nghĩa; đây là số ảnh được xem, không phải số lỗi được xác nhận đúng.

## 3. Calibration (2 ngưỡng)

| Tham số | Khởi đầu → chọn | Precision / Recall trước → sau | Lý do |
|---|---|---|---|
| `duplicates.phash_dist` | 2 → 4 | NEAR: 1,000 / 0,500 → 1,000 / 0,667 | Bắt thêm một ca chèn không tăng FP; chọn mức thấp nhất của plateau 4–14 để hạn chế loại nhầm |
| `second_opinion.conf` | 0,25 → 0,60 | WRONG_CLASS: 0,556 / 0,833 → 0,625 / 0,833; MISSING: 0,500 / 1,000 → 0,571 / 1,000 | Giảm FP và giữ recall hai nhóm này; 0,70 bắt đầu giảm recall MISSING |

Đánh đổi: LOOSE_BOX giảm P/R từ 0,286/0,400 xuống 0,200/0,200; FALSE_POS giữ 0,313/1,000 vì dùng `fp_conf` riêng. Không nâng conf để ép Release. Nguồn: `calibration/calibration_report.md`, `calibration.json` (hai sweep).

Calib chỉ 39 ảnh nên có thể gây hiểu nhầm: pHash=16 đạt recall NEAR 5/6, nhưng trên raw tăng tổng cờ trùng/rò rỉ từ 14 lên 26 ảnh (NEAR 2→7, LEAK 4→11), chưa xác nhận bằng mắt rằng cờ tăng thêm đều đúng. Vì tự loại ảnh có hậu quả trực tiếp, chọn 4 thận trọng hơn và thừa nhận bỏ sót. Recall calib không phải recall đã đo trên raw.

## 4. Cửa chặn và điểm mù

Đã chạy `python -m pipeline.run --budget 0 --work work/run_nb --reports work/rep_nb --export-dir work/exp_nb`: **Rework**, mã thoát **20**, còn 6 lỗi thiếu file nhãn; không tồn tại `work/exp_nb/clean_v1`. Lần chạy chính không có lỗi bắt buộc nhưng 38/205 ảnh còn cảnh báo chưa duyệt nên Hold. Test e2e kiểm chạy lại cùng kết quả và dừng/tiếp tục khi người sửa nhãn.

Điểm mù đo trên calib: (1) pHash=4 bỏ sót `calib_037`, `calib_038` (2/6 ca NEAR); (2) second opinion bỏ sót sai lớp ở `calib_009` (1/6) và box lỏng ở `calib_002`, `calib_006`, `calib_012`, `calib_024` (4/5). Model kiểm cũng có thể sai; không tự sửa nhãn ngữ nghĩa theo model.

Đã tạo 10 ảnh vẽ nhãn trong `work/viz/` để học viên kiểm bằng mắt. Ví dụ máy phát hiện để đối chiếu: `img_0020.txt:3` sai ID, `img_0030.txt:9` tràn ảnh, `img_0050.txt:1` box rỗng. Chưa ghi nhận kết quả học viên tự kiểm bằng mắt.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)

**Chưa chạy**: hiện hoàn thiện phần lõi trên CPU, chưa có phiên Colab GPU. Khi train: cùng model, siêu tham số, val/test và ít nhất hai seed. So chênh mAP với độ lệch giữa seed; raw có rò rỉ test/val, clean còn nhãn chưa duyệt là hai giả thuyết cần kiểm. Không khẳng định clean tốt hơn khi chưa có số liệu.

## 6. Quyết định và ghi chú AI

Giữ **Hold**. Muốn Release cần xử lý cảnh báo qua quy trình duyệt được phê duyệt để dưới 10% ảnh chưa duyệt còn cảnh báo và giữ 0 lỗi bắt buộc; không đổi ngân sách 80 hay ngưỡng gate của bài để ép kết quả. Chưa làm thưởng CVAT.

- Prompt: triển khai bốn module theo docstring/test; check chỉ đọc, autofix chỉ sửa bản sao, không dùng đáp án raw hay nhãn test để sửa.
- Kiểm: 79 test gốc pass, hai sweep calibration, pipeline và budget=0. Học viên cần đọc và giải thích code AI trước khi nộp.
- Một lần AI thiếu: lần chạy test đầu dùng thư mục tạm chưa có thư mục cha nên 69 fixture lỗi; tạo `work/`, chỉ định basetemp trong workspace rồi chạy lại. Đây là lỗi thiết lập test, không phải kết quả kiểm nhãn.

Windows: checker gốc so đường dẫn dùng dấu gạch chéo ngược với danh sách bảo vệ dùng `/`, báo nhầm `pipeline/calibrate.py`. `scripts/check_submission_windows.py --no-train` chỉ chuẩn hoá phép so trong bộ nhớ và đặt TEMP/TMP trong workspace; giữ nguyên file đề, test và kiểm SHA1.
