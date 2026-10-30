"""
Bai 3 - Light Controller Client
Lenh: ON / OFF / STATUS / EXIT
"""
import argparse
import asyncio
import json

import aiocoap
from aiocoap import Code, Message

URI = "coap://127.0.0.1:5683/iot/lab/light01/status"
DEVICE_ID = "light01"
CONTENT_FORMAT_JSON = 50


async def send_put(ctx, command, uri=URI, timeout=5):
    print("Sending PUT request...")
    payload = json.dumps({"device_id": DEVICE_ID, "command": command}).encode("utf-8")
    req = Message(code=Code.PUT, uri=uri, payload=payload, content_format=CONTENT_FORMAT_JSON)
    resp = await asyncio.wait_for(ctx.request(req).response, timeout)
    print(f"Response Code: {resp.code}")
    if resp.payload:
        print(resp.payload.decode("utf-8", errors="replace"))


async def send_get(ctx, uri=URI, timeout=5):
    print("Sending GET request...")
    resp = await asyncio.wait_for(ctx.request(Message(code=Code.GET, uri=uri)).response, timeout)
    print(f"Response Code: {resp.code}\nResponse:")
    print(resp.payload.decode("utf-8", errors="replace"))


async def controller_loop(ctx, uri, timeout):
    while True:
        try:
            cmd = await asyncio.to_thread(input, "Nhap lenh (ON/OFF/STATUS/EXIT): ")
        except (EOFError, KeyboardInterrupt):
            break
        cmd = cmd.strip().upper()

        if cmd == "EXIT":
            break
        if cmd not in ("ON", "OFF", "STATUS"):
            print("Lenh khong hop le! Chi chap nhan ON, OFF, STATUS hoac EXIT.")
            continue

        try:
            if cmd == "STATUS":
                await send_get(ctx, uri, timeout)
            else:
                await send_put(ctx, cmd, uri, timeout)
        except Exception as e:  # mat ket noi / timeout
            print(f"Loi giao tiep voi Server: {type(e).__name__}: {e}")
        print()

    print("Controller ket thuc.")


async def main(uri=URI, timeout=5):
    ctx = await aiocoap.Context.create_client_context(transports=["simple6"])
    try:
        await controller_loop(ctx, uri, timeout)
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
        print("\nController ket thuc.")
