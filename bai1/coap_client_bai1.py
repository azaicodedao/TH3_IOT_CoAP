"""Bai 1: gui GET va POST chua thong tin sinh vien."""
import argparse
import asyncio

import aiocoap


async def main(args):
    ctx = await aiocoap.Context.create_client_context(transports=["simple6"])
    payload = f"Xin chao tu CoAP Client - {args.student_id} - {args.name}"
    try:
        for method, body in ((aiocoap.GET, b""), (aiocoap.POST, payload.encode("utf-8"))):
            print(f"Sending {method} request...\nURI: {args.uri}")
            if body:
                print(f"Payload: {payload}")
            request = aiocoap.Message(code=method, uri=args.uri, payload=body)
            if body:
                request.opt.content_format = 0
            try:
                response = await asyncio.wait_for(ctx.request(request).response, args.timeout)
                print(f"Response:\nCode: {response.code}\n"
                      f"Payload: {response.payload.decode('utf-8', errors='replace')}\n")
            except (TimeoutError, aiocoap.error.Error, OSError) as exc:
                print(f"Loi ket noi/timeout: {type(exc).__name__}: {exc}")
    finally:
        await ctx.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default="coap://127.0.0.1:5683/iot/lab/message")
    parser.add_argument("--student-id", default="B23DCCN821")
    parser.add_argument("--name", default="Nguyen Van Tien")
    parser.add_argument("--timeout", type=float, default=5)
    try:
        asyncio.run(main(parser.parse_args()))
    except KeyboardInterrupt:
        print("\nClient stopped.")
