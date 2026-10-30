# Lập trình Python với giao thức CoAP

## Thông tin sinh viên

- Họ và tên: Nguyễn Văn Tiến
- Mã sinh viên: B23DCCN821
- Lớp: D23CNPM04

- Họ và tên: Phạm Đức Của
- Mã sinh viên: B23DCCN104
- Lớp: D23CNPM04

## Môi trường và cài đặt

Đã kiểm thử trên Windows với Python 3.12.7 và `aiocoap 0.4.17`.
Mã nguồn sử dụng Python 3.10 trở lên. Không cần MQTT Broker hoặc RabbitMQ.

Chạy từ thư mục gốc của dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Các lệnh bên dưới dùng trực tiếp Python trong môi trường ảo, không cần kích hoạt
PowerShell script. Trên Linux/macOS, thay `.\.venv\Scripts\python.exe` bằng
`.venv/bin/python`.

## Cấu trúc thư mục

```text
TH3_IOT_CoAP/
|-- bai1/
|   |-- coap_server_bai1.py
|   |-- coap_client_bai1.py
|-- bai2/
|   |-- sensor_server_bai2.py
|   |-- monitor_client_bai2.py
|-- bai3/
|   |-- light_server_bai3.py
|   |-- light_controller_bai3.py
|   |-- light_monitor_bai3.py
|-- tests/test_coap_lab.py
|-- docs/verification.log
|-- requirements.txt
|-- README.md
```

## Tài nguyên và mô hình giao tiếp

Client gửi yêu cầu đến URI của tài nguyên trên server; server xử lý phương thức
và trả về mã CoAP cùng payload. Observe cho phép server gửi trạng thái mới đến
client đã đăng ký khi tài nguyên thay đổi.

| Bài | Thiết bị / tài nguyên | URI mặc định | Phương thức | Payload |
| --- | --- | --- | --- | --- |
| 1 | Thông điệp | `coap://127.0.0.1:5683/iot/lab/message` | GET, POST | UTF-8, text/plain (0) |
| 2 | sensor01 / data | `coap://127.0.0.1:5683/iot/lab/sensor01/data` | GET | application/json (50) |
| 3 | light01 / status | `coap://127.0.0.1:5683/iot/lab/light01/status` | GET, PUT, Observe | Trạng thái và PUT: application/json (50); xác nhận PUT: văn bản |

**Chạy lần lượt từng bài**: các server mặc định cùng dùng UDP cổng 5683.
Dừng server bài trước bằng Ctrl+C trước khi mở server bài tiếp theo.
Tất cả lệnh chạy dưới đây thực hiện từ thư mục gốc, mỗi terminal dùng một lệnh.

### Bài 1 — Gửi và nhận thông điệp

Terminal 1:

```powershell
.\.venv\Scripts\python.exe bai1/coap_server_bai1.py
```

Terminal 2:

```powershell
.\.venv\Scripts\python.exe bai1/coap_client_bai1.py
```

Client GET thông điệp chào mừng, sau đó POST:

```text
Xin chao tu CoAP Client - B23DCCN821 - Nguyen Van Tien
```

Server in payload và thời điểm nhận, trả `2.04 Changed` với nội dung
`Server da nhan thong diep`. GET thành công trả `2.05 Content`.
Server lưu thông điệp POST gần nhất trong bộ nhớ để trả ở GET tiếp theo;
khởi động lại server sẽ đặt lại thông điệp chào mừng.
Chạy lại client để gửi thêm thông điệp, hoặc thay thông tin:

```powershell
.\.venv\Scripts\python.exe bai1/coap_client_bai1.py --student-id B23DCCN821 --name "Nguyen Van Tien"
```

Thử URI không tồn tại để nhận `4.04 Not Found`:

```powershell
.\.venv\Scripts\python.exe bai1/coap_client_bai1.py --uri coap://127.0.0.1:5683/khong-ton-tai
```

Tắt server rồi chạy client với `--timeout 2` để thử lỗi kết nối/timeout.
POST rỗng hoặc không phải UTF-8 trả `4.00 Bad Request`.

### Bài 2 — Mô phỏng cảm biến nhiệt độ, độ ẩm

Terminal 1:

```powershell
.\.venv\Scripts\python.exe bai2/sensor_server_bai2.py
```

Terminal 2:

```powershell
.\.venv\Scripts\python.exe bai2/monitor_client_bai2.py
```

Server sinh dữ liệu ban đầu ngay khi chạy và cập nhật mỗi 3 giây, độc lập với
yêu cầu GET. Nhiệt độ trong khoảng 20–40°C; độ ẩm trong khoảng 30–85%.
GET trả dữ liệu mới nhất với Content-Format `application/json`:

```json
{"device_id": "sensor01", "temperature": 28.5, "humidity": 65.2}
```

Client GET mỗi 3 giây khi server phản hồi bình thường, kiểm tra và phân tích JSON,
in mã thiết bị, nhiệt độ, độ ẩm, thời điểm nhận. Nếu yêu cầu bị timeout,
client ghi lỗi và tiếp tục thử; mỗi yêu cầu chờ tối đa 5 giây mặc định.

- Nhiệt độ > 35°C: `CANH BAO: Nhiet do cao`.
- Độ ẩm < 40%: `CANH BAO: Do am thap`.
- Có thể xuất hiện đồng thời hai cảnh báo.
- Nhiệt độ ≤ 35°C và độ ẩm ≥ 40%: `Trang thai: Binh thuong`.

Nhấn Ctrl+C để dừng giám sát hoặc server.

### Bài 3 — Điều khiển đèn thông minh và Observe

Terminal 1 — Server:

```powershell
.\.venv\Scripts\python.exe bai3/light_server_bai3.py
```

Terminal 2 — Monitoring Client:

```powershell
.\.venv\Scripts\python.exe bai3/light_monitor_bai3.py
```

Terminal 3 — Controller Client:

```powershell
.\.venv\Scripts\python.exe bai3/light_controller_bai3.py
```

Đèn bắt đầu ở trạng thái `OFF`. Controller nhận lệnh:

| Lệnh | Hoạt động |
| --- | --- |
| ON | PUT bật đèn, hiển thị mã phản hồi và xác nhận |
| OFF | PUT tắt đèn, hiển thị mã phản hồi và xác nhận |
| STATUS | GET trạng thái hiện tại |
| EXIT | Kết thúc controller |

Payload PUT:

```json
{"device_id": "light01", "command": "ON"}
```

Payload trạng thái GET / Observe:

```json
{"device_id": "light01", "status": "ON"}
```

Monitoring Client gửi GET với tùy chọn `observe=0`, nhận trạng thái ban đầu rồi
chờ thông báo từ server qua `request.observation`; **không GET định kỳ**.
Server dùng `ObservableResource.updated_state()` chỉ khi trạng thái thực sự đổi.
Lệnh ON khi đang ON hoặc OFF khi đang OFF vẫn được xác nhận nhưng không gửi
thông báo thay đổi. Có thể mở nhiều terminal monitoring cùng lúc.

Client đăng ký lại sau 3 giây nếu Observe kết thúc hoặc thư viện báo lỗi kết nối.
Trong lúc đèn đứng yên, không có thông báo mới là bình thường; client không dùng
heartbeat để phát hiện server tắt ngay lập tức. Nhấn Ctrl+C để dừng monitoring.
JSON/lệnh sai trả `4.00 Bad Request`; mã thiết bị sai trả `4.04 Not Found`.

## Chạy trên hai máy hoặc đổi cổng

Mỗi server hỗ trợ `--host` và `--port`; mỗi client hỗ trợ `--uri` và `--timeout`
(giây, mặc định 5). Ví dụ máy server có IP LAN `192.168.1.10`:

```powershell
.\.venv\Scripts\python.exe bai3/light_server_bai3.py --host 192.168.1.10 --port 5683
.\.venv\Scripts\python.exe bai3/light_monitor_bai3.py --uri coap://192.168.1.10:5683/iot/lab/light01/status
.\.venv\Scripts\python.exe bai3/light_controller_bai3.py --uri coap://192.168.1.10:5683/iot/lab/light01/status
```

Thay bằng IP thật của máy server, cho phép UDP 5683 qua tường lửa và bảo đảm hai
máy liên lạc được. Server mặc định chỉ lắng nghe loopback `127.0.0.1`.
URI dùng địa chỉ số này thay cho `localhost` để tránh khác biệt phân giải IPv4/IPv6.
Muốn chạy nhiều server đồng thời, chọn cổng khác nhau và cập nhật URI client.

## Kết quả và log minh chứng

Đã chạy kiểm thử tự động qua UDP loopback trên Windows, sử dụng server và client
thật ở cổng thử nghiệm 56830, cùng các dữ liệu cố định để kiểm tra ngưỡng cảnh báo:

- Bài 1: GET/POST, thông tin sinh viên, GET thông điệp gần nhất, payload lỗi,
  URI không tồn tại và xử lý khi server không chạy.
- Bài 2: JSON và Content-Format đúng, dữ liệu trong khoảng mô phỏng, cập nhật
  định kỳ, client nhận hai chu kỳ; cảnh báo nhiệt độ/độ ẩm và biên 35°C, 40%.
- Bài 3: Controller ON/OFF/STATUS/EXIT và lệnh sai; monitoring nhận OFF → ON → OFF;
  hai observer kiểm thử cùng nhận thay đổi bên cạnh monitoring chạy riêng;
  PUT trạng thái không đổi không phát thông báo; JSON, lệnh và thiết bị sai.

Log thực thi: [docs/verification.log](docs/verification.log).
Log có phân biệt dữ liệu cảm biến ngẫu nhiên và dữ liệu cố định 36.1°C/38.7%
dùng để kiểm tra hai cảnh báo. Chưa kiểm thử trên hai máy vật lý.

Chạy lại kiểm thử (không cần mở server thủ công, cổng 56830 và 56831 phải trống):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Nộp qua GitHub

Nộp các thư mục `bai1`, `bai2`, `bai3`, `tests`, `docs`, README và requirements.
`.gitignore` đã loại môi trường ảo và cache Python. Kiểm tra thay đổi, commit và
push lên repository của sinh viên/nhóm, sau đó nộp đường dẫn repository theo yêu
cầu môn học.

## Tài liệu tham khảo

- [aiocoap Documentation — ví dụ server và client](https://aiocoap.readthedocs.io/en/latest/examples.html)
- [ObservableResource](https://aiocoap.readthedocs.io/en/latest/module/aiocoap.resource.html)
- [UDP simple6 cho client](https://aiocoap.readthedocs.io/en/latest/module/aiocoap.transports.simple6.html)
- [UDP simplesocketserver](https://aiocoap.readthedocs.io/en/latest/module/aiocoap.transports.simplesocketserver.html)

Các chương trình chọn `simple6` cho client và `simplesocketserver` cho server để
chạy UDP unicast trên Windows với bộ thư viện tối thiểu của bài thực hành.
