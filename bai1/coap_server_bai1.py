"""Bai 1: tai nguyen thong diep, ho tro GET va POST."""
import argparse
import asyncio
from datetime import datetime

import aiocoap
from aiocoap import resource


class MessageResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self.message = "Xin chao tu CoAP Server"

    async def render_get(self, request):
        print("GET request received: /iot/lab/message", flush=True)
        return aiocoap.Message(code=aiocoap.CONTENT,
                               payload=self.message.encode("utf-8"), content_format=0)

    async def render_post(self, request):
        try:
            message = request.payload.decode("utf-8")
            if not message.strip():
                raise ValueError("Thong diep rong")
        except (UnicodeDecodeError, ValueError):
            return aiocoap.Message(code=aiocoap.BAD_REQUEST,
                                   payload=b"Can thong diep UTF-8 khong rong")
        self.message = message
        print(f"POST request received:\nPayload: {message}\n"
              f"Time: {datetime.now():%H:%M:%S}", flush=True)
        return aiocoap.Message(code=aiocoap.CHANGED,
                               payload=b"Server da nhan thong diep", content_format=0)


async def main(host="127.0.0.1", port=5683):
    site = resource.Site()
    site.add_resource(["iot", "lab", "message"], MessageResource())
    ctx = await aiocoap.Context.create_server_context(
        site, bind=(host, port), transports=["simplesocketserver"])
    print(f"CoAP Server started on {host}:{port}", flush=True)
    try:
        await asyncio.get_running_loop().create_future()
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
