## 1. Thông tin sinh viên / nhóm thực hiện

- Họ và tên: Nguyễn Văn Tiến
- Mã sinh viên: B23DCCN821
- Lớp: D23CNPM04

## 2. Môi trường

- Python 3.x (đã kiểm thử với Python 3.12)
- Thư viện: `aiocoap`

```bash
pip install aiocoap
```

# CoAP Lab – Bài 3: Smart Light với CoAP Observe

## 1. Cấu trúc thư mục

```
TH3_CoAP/
|-- bai3/
|   |-- light_server_bai3.py       # Smart Light CoAP Server
|   |-- light_controller_bai3.py   # Light Controller Client (GET/PUT)
|   |-- light_monitor_bai3.py      # Light Monitoring Client (Observe)
|-- README.md
```

## 2. Thông tin kết nối

| Mục | Giá trị |
|---|---|
| Giao thức | CoAP over UDP |
| Địa chỉ Server | `127.0.0.1` |
| Cổng | `5683` |
| Thiết bị | `light01` (trạng thái ban đầu: `OFF`) |
| URI tài nguyên | `coap://127.0.0.1:5683/iot/lab/light01/status` |
| Phương thức | GET, PUT, Observe |

Payload điều khiển (PUT):

```json
{"device_id": "light01", "command": "ON"}
```

Payload trạng thái (GET / thông báo Observe):

```json
{"device_id": "light01", "status": "ON"}
```

## 3. Cách chạy Bài 3

Mở 3 terminal, thư mục hiện tại là `TH3_CoAP/bai3/`.

**Terminal 1 – Server**
```bash
python light_server_bai3.py
```

**Terminal 2 – Monitoring Client (Observe)**
```bash
python light_monitor_bai3.py
```

**Terminal 3 – Controller Client**
```bash
python light_controller_bai3.py
```
Nhập lệnh: `ON`, `OFF`, `STATUS`, `EXIT`. Nhấn `Ctrl+C` để dừng Server và Monitoring Client.

## 4. Mô tả hoạt động

- **Server** (`ObservableResource` của aiocoap):
  - `GET`: trả về trạng thái hiện tại dạng JSON (Content-Format `application/json`).
  - `PUT`: nhận lệnh `ON`/`OFF`, cập nhật trạng thái, trả `2.04 Changed` kèm thông báo xác nhận.
  - `Observe`: lưu danh sách Client đăng ký; chỉ gọi `updated_state()` để thông báo cho tất cả Client khi trạng thái **thực sự thay đổi** (gửi `ON` khi đèn đang `ON` thì không thông báo).
  - Lệnh sai hoặc JSON sai trả `4.00 Bad Request`; `device_id` không đúng trả `4.04 Not Found`.
- **Controller Client**: nhập lệnh từ bàn phím, gửi PUT (ON/OFF) hoặc GET (STATUS), hiển thị mã phản hồi và nội dung; bắt lỗi khi Server không phản hồi.
- **Monitoring Client**: đăng ký Observe (`observe=0`), nhận trạng thái ban đầu, sau đó tự động nhận thông báo mỗi khi trạng thái đổi, hiển thị mã thiết bị, trạng thái và thời điểm nhận. **Không dùng vòng lặp GET.** Tự đăng ký lại nếu mất kết nối.

## 5. Kết quả đạt được

- [x] Server định nghĩa và quản lý tài nguyên `light01/status`
- [x] Client gửi được GET và PUT
- [x] Đèn thay đổi trạng thái đúng lệnh
- [x] Monitoring Client đăng ký Observe thành công
- [x] Server tự động thông báo khi trạng thái thay đổi (kiểm thử với 2 Monitoring Client cùng lúc)
- [x] Hỗ trợ đồng thời điều khiển và giám sát
- [x] Xử lý lệnh không hợp lệ và lỗi giao tiếp cơ bản

## 6. Log minh chứng

**Terminal 1 – Server**
```
CoAP Smart Light Server started...
Resource: /iot/lab/light01/status
[00:32:17] New Observe registration received (tong so observer: 1)
[00:40:41] PUT request received:
Device: light01
Command: ON
Light state changed: OFF -> ON
Notify observers: ON
[00:41:27] GET request received: /iot/lab/light01/status
[00:42:11] PUT request received:
Device: light01
Command: OFF
Light state changed: ON -> OFF
Notify observers: OFF
```

**Terminal 2 – Monitoring Client**
```
Registering CoAP Observe...
Observe registration successful

[00:32:17] Initial State
Device: light01
Status: OFF

[00:40:41] State Updated
Device: light01
Status: ON

[00:42:11] State Updated
Device: light01
Status: OFF
```

**Terminal 3 – Controller Client**
```
Nhap lenh (ON/OFF/STATUS/EXIT): ON
Sending PUT request...
Response Code: 2.04 Changed
Da bat den light01

Nhap lenh (ON/OFF/STATUS/EXIT): STATUS
Sending GET request...
Response:
{"device_id": "light01", "status": "ON"}

Nhap lenh (ON/OFF/STATUS/EXIT): OFF
Sending PUT request...
Response Code: 2.04 Changed
Da tat den light01

Nhap lenh (ON/OFF/STATUS/EXIT): EXIT
Controller ket thuc.
```
