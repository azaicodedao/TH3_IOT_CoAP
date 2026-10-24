"""
Bai 3 - Light Monitoring Client (CoAP Observe)
Khong dung vong lap GET: dang ky Observe va cho Server thong bao.
"""
import asyncio
import json
from datetime import datetime

import aiocoap
from aiocoap import Code, Message

URI = "coap://127.0.0.1:5683/iot/lab/light01/status"


def now():
    return datetime.now().strftime("%H:%M:%S")


def show(title, response):
    try:
        data = json.loads(response.payload.decode("utf-8"))
        print(f"[{now()}] {title}")
        print(f"Device: {data.get('device_id')}")
        print(f"Status: {data.get('status')}")
    except ValueError:
        print(f"[{now()}] {title}: payload khong hop le: {response.payload!r}")
    print()


async def main():
    ctx = await aiocoap.Context.create_client_context()
    print("Registering CoAP Observe...")

    while True:  # tu dang ky lai neu mat ket noi
        request = ctx.request(Message(code=Code.GET, uri=URI, observe=0))
        try:
            first = await request.response
            print("Observe registration successful\n")
            show("Initial State", first)

            async for notification in request.observation:
                show("State Updated", notification)
            print("Server ket thuc Observe. Dang ky lai sau 3 giay...")
        except Exception as e:
            print(f"Loi ket noi voi Server: {type(e).__name__}: {e}")
            print("Thu dang ky lai sau 3 giay...")
        await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor ket thuc.")