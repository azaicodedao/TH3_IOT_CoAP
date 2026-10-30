"""Bai 2: mo phong cam bien, cap nhat moi 3 giay."""
import argparse
import asyncio
import json
import random

import aiocoap
from aiocoap import resource


class SensorResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self.update()

    def update(self):
        self.data = {"device_id": "sensor01",
                     "temperature": round(random.uniform(20, 40), 1),
                     "humidity": round(random.uniform(30, 85), 1)}
        print(f"Sensor updated: {json.dumps(self.data)}", flush=True)

    async def update_loop(self):
        while True:
            await asyncio.sleep(3)
            self.update()

    async def render_get(self, request):
        print("GET request received: /iot/lab/sensor01/data", flush=True)
        return aiocoap.Message(code=aiocoap.CONTENT,
                               payload=json.dumps(self.data).encode("utf-8"),
                               content_format=50)


async def main(host="127.0.0.1", port=5683):
    sensor = SensorResource()
    site = resource.Site()
    site.add_resource(["iot", "lab", "sensor01", "data"], sensor)
    ctx = await aiocoap.Context.create_server_context(
        site, bind=(host, port), transports=["simplesocketserver"])
    print(f"Sensor CoAP Server started on {host}:{port}", flush=True)
    try:
        await sensor.update_loop()
    finally:
        await ctx.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    args = parser.parse_args()
    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        print("\nServer stopped.")
