"""
Bai 3 - Light Controller Client
Lenh: ON / OFF / STATUS / EXIT
"""
import asyncio
import json
import sys

import aiocoap
from aiocoap import Code, Message

URI = "coap://127.0.0.1:5683/iot/lab/light01/status"
DEVICE_ID = "light01"
CONTENT_FORMAT_JSON = 50


async def send_put(ctx, command):
    print("Sending PUT request...")
    payload = json.dumps({"device_id": DEVICE_ID, "command": command}).encode("utf-8")
    req = Message(code=Code.PUT, uri=URI, payload=payload, content_format=CONTENT_FORMAT_JSON)
    resp = await ctx.request(req).response
    print(f"Response Code: {resp.code}")
    if resp.payload:
        print(resp.payload.decode("utf-8", errors="replace"))


async def send_get(ctx):
    print("Sending GET request...")
    resp = await ctx.request(Message(code=Code.GET, uri=URI)).response
    print("Response:")
    print(resp.payload.decode("utf-8", errors="replace"))


async def main():
    ctx = await aiocoap.Context.create_client_context()
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
                await send_get(ctx)
            else:
                await send_put(ctx, cmd)
        except Exception as e:  # mat ket noi / timeout
            print(f"Loi giao tiep voi Server: {type(e).__name__}: {e}")
        print()

    await ctx.shutdown()
    print("Controller ket thuc.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nController ket thuc.")