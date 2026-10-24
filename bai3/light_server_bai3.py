"""
Bai 3 - Smart Light CoAP Server (light01)
Tai nguyen: coap://localhost:5683/iot/lab/light01/status
Ho tro: GET, PUT, Observe
"""
import asyncio
import json
from datetime import datetime

import aiocoap
import aiocoap.resource as resource
from aiocoap import Code

DEVICE_ID = "light01"
PORT = 5683
CONTENT_FORMAT_JSON = 50  # application/json


def now():
    return datetime.now().strftime("%H:%M:%S")


class LightStatusResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()
        self.status = "OFF"  # trang thai ban dau

    def _status_payload(self):
        return json.dumps({"device_id": DEVICE_ID, "status": self.status}).encode("utf-8")

    def _error(self, code, text):
        return aiocoap.Message(code=code, payload=text.encode("utf-8"))

    # Ghi nhan Client dang ky Observe (van goi lop cha de luu observer)
    async def add_observation(self, request, serverobservation):
        await super().add_observation(request, serverobservation)
        print(f"[{now()}] New Observe registration received "
              f"(tong so observer: {len(self._observations)})")

    # GET: tra ve trang thai hien tai
    async def render_get(self, request):
        # Khi Observe, aiocoap cung goi render_get de tao thong bao -> khong in log lap
        if request.opt.observe is None:
            print(f"[{now()}] GET request received: /iot/lab/light01/status")
        return aiocoap.Message(
            code=Code.CONTENT,
            payload=self._status_payload(),
            content_format=CONTENT_FORMAT_JSON,
        )

    # PUT: nhan lenh dieu khien ON/OFF
    async def render_put(self, request):
        print(f"[{now()}] PUT request received:")
        try:
            data = json.loads(request.payload.decode("utf-8"))
            device = data["device_id"]
            command = str(data["command"]).strip().upper()
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            print("Payload khong hop le")
            return self._error(Code.BAD_REQUEST, "Payload JSON khong hop le (can device_id va command)")

        print(f"Device: {device}")
        print(f"Command: {command}")

        if device != DEVICE_ID:
            return self._error(Code.NOT_FOUND, f"Khong tim thay thiet bi {device}")
        if command not in ("ON", "OFF"):
            print("Lenh khong hop le")
            return self._error(Code.BAD_REQUEST, "Lenh khong hop le (chi chap nhan ON/OFF)")

        if command == self.status:
            # Trang thai khong doi -> khong thong bao Observe
            print(f"Light state unchanged: {self.status}")
            return aiocoap.Message(
                code=Code.CHANGED,
                payload=f"Den {DEVICE_ID} da o trang thai {self.status} san".encode("utf-8"),
            )

        old = self.status
        self.status = command
        print(f"Light state changed: {old} -> {self.status}")
        print(f"Notify observers: {self.status}")
        self.updated_state()  # thong bao cho tat ca observer

        text = f"Da bat den {DEVICE_ID}" if command == "ON" else f"Da tat den {DEVICE_ID}"
        return aiocoap.Message(code=Code.CHANGED, payload=text.encode("utf-8"))


async def main():
    root = resource.Site()
    root.add_resource(
        [".well-known", "core"],
        resource.WKCResource(root.get_resources_as_linkheader),
    )
    root.add_resource(["iot", "lab", "light01", "status"], LightStatusResource())

    await aiocoap.Context.create_server_context(root, bind=("127.0.0.1", PORT))
    print("CoAP Smart Light Server started...")
    print("Resource: /iot/lab/light01/status")
    await asyncio.get_running_loop().create_future()  # chay mai cho den khi Ctrl+C


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.")