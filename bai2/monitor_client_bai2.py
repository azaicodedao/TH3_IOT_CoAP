"""Bai 2: GET du lieu cam bien moi 3 giay, canh bao nguong."""
import argparse
import asyncio
from datetime import datetime
import json
import math

import aiocoap


def show(response):
    if not response.code.is_successful():
        raise ValueError(f"Server tra ve {response.code}")
    if response.opt.content_format != 50:
        raise ValueError("Content-Format phai la application/json")
    data = json.loads(response.payload.decode("utf-8"))
    if not isinstance(data, dict) or data.get("device_id") != "sensor01":
        raise ValueError("Sai du lieu thiet bi")
    temperature, humidity = data.get("temperature"), data.get("humidity")
    if any(type(value) not in (int, float) or not math.isfinite(value)
           for value in (temperature, humidity)):
        raise ValueError("Nhiet do va do am phai la so huu han")
    print(f"[{datetime.now():%H:%M:%S}] Received sensor data\n"
          f"Device: {data['device_id']}\nTemperature: {temperature} C\nHumidity: {humidity} %")
    if temperature > 35:
        print("CANH BAO: Nhiet do cao")
    if humidity < 40:
        print("CANH BAO: Do am thap")
    if temperature <= 35 and humidity >= 40:
        print("Trang thai: Binh thuong")
    print("\n------------------------------\n", flush=True)


async def main(args):
    ctx = await aiocoap.Context.create_client_context(transports=["simple6"])
    try:
        while True:
            started = asyncio.get_running_loop().time()
            try:
                request = aiocoap.Message(code=aiocoap.GET, uri=args.uri)
                response = await asyncio.wait_for(ctx.request(request).response, args.timeout)
                show(response)
            except (TimeoutError, aiocoap.error.Error, OSError, ValueError) as exc:
                print(f"Loi nhan du lieu: {type(exc).__name__}: {exc}", flush=True)
            elapsed = asyncio.get_running_loop().time() - started
            await asyncio.sleep(max(0, 3 - elapsed))
    finally:
        await ctx.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default="coap://127.0.0.1:5683/iot/lab/sensor01/data")
    parser.add_argument("--timeout", type=float, default=5)
    try:
        asyncio.run(main(parser.parse_args()))
    except KeyboardInterrupt:
        print("\nMonitor stopped.")
