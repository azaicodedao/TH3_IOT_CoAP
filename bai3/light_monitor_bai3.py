"""
Bai 3 - Light Monitoring Client (CoAP Observe)
Khong dung vong lap GET: dang ky Observe va cho Server thong bao.
"""
import argparse
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
        if not response.code.is_successful():
            raise ValueError(f"Server tra ve {response.code}")
        if response.opt.content_format != 50:
            raise ValueError("Content-Format phai la application/json")
        data = json.loads(response.payload.decode("utf-8"))
        if (not isinstance(data, dict) or data.get("device_id") != "light01"
                or data.get("status") not in ("ON", "OFF")):
            raise ValueError("Sai du lieu trang thai den")
        print(f"[{now()}] {title}")
        print(f"Device: {data.get('device_id')}")
        print(f"Status: {data.get('status')}")
    except ValueError:
        print(f"[{now()}] {title}: payload khong hop le: {response.payload!r}")
    print()


async def observe_loop(ctx, uri, timeout):
    print("Registering CoAP Observe...")

    while True:  # tu dang ky lai neu mat ket noi
        request = ctx.request(Message(code=Code.GET, uri=uri, observe=0))
        try:
            first = await asyncio.wait_for(request.response, timeout)
            if not first.code.is_successful() or first.opt.observe is None:
                raise ValueError(f"Server khong chap nhan Observe: {first.code}")
            print("Observe registration successful\n")
            show("Initial State", first)

            async for notification in request.observation:
                show("State Updated", notification)
            print("Server ket thuc Observe. Dang ky lai sau 3 giay...")
        except Exception as e:
            print(f"Loi ket noi voi Server: {type(e).__name__}: {e}")
            print("Thu dang ky lai sau 3 giay...")
        finally:
            if not request.observation.cancelled:
                request.observation.cancel()
        await asyncio.sleep(3)


async def main(uri=URI, timeout=5):
    ctx = await aiocoap.Context.create_client_context(transports=["simple6"])
    try:
        await observe_loop(ctx, uri, timeout)
    finally:
        await ctx.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default=URI)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    try:
        asyncio.run(main(args.uri, args.timeout))
    except KeyboardInterrupt:
        print("\nMonitor ket thuc.")
