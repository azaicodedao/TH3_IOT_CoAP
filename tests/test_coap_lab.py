"""Kiem thu qua UDP that, chay bang python -m unittest discover -s tests -v."""
import asyncio
import contextlib
import json
from pathlib import Path
import sys
import unittest

import aiocoap

ROOT = Path(__file__).resolve().parents[1]
PORT = 56830
BASE = f"coap://127.0.0.1:{PORT}"


class CoAPLabTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.processes = []
        self.readers = []
        self.ctx = await aiocoap.Context.create_client_context(transports=["simple6"])

    async def asyncTearDown(self):
        for process in self.processes:
            if process.returncode is None:
                process.terminate()
            await process.wait()
        for reader in self.readers:
            await reader
        await self.ctx.shutdown()

    async def start_server(self, script):
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-u", str(ROOT / script), "--port", str(PORT),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        self.processes.append(process)
        while True:
            line = await asyncio.wait_for(process.stdout.readline(), 5)
            if not line:
                self.fail("Server dung truoc khi khoi dong")
            print(line.decode().strip())
            if "started" in line.decode():
                break

        async def drain():
            async for line in process.stdout:
                print(line.decode().strip())

        self.readers.append(asyncio.create_task(drain()))

    async def request(self, path, method=aiocoap.GET, payload=b"", content_format=None):
        request = aiocoap.Message(code=method, uri=BASE + path, payload=payload)
        request.opt.content_format = content_format
        return await asyncio.wait_for(self.ctx.request(request).response, 3)

    async def run_client(self, script, *args, stdin=None):
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-u", str(ROOT / script), *args,
            stdin=asyncio.subprocess.PIPE if stdin else None,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        self.processes.append(process)
        output, _ = await asyncio.wait_for(process.communicate(stdin), 10)
        output = output.decode("utf-8", errors="replace").replace("\r\n", "\n")
        print(output)
        self.assertEqual(process.returncode, 0, output)
        self.assertNotIn("Traceback", output)
        return output

    async def test_bai1_get_post_errors_and_client(self):
        await self.start_server("bai1/coap_server_bai1.py")
        path = "/iot/lab/message"
        response = await self.request(path)
        self.assertEqual(response.code, aiocoap.CONTENT)
        self.assertEqual(response.payload, b"Xin chao tu CoAP Server")
        output = await self.run_client("bai1/coap_client_bai1.py", "--uri", BASE + path)
        self.assertIn("2.05 Content", output)
        self.assertIn("2.04 Changed", output)
        self.assertIn("B23DCCN821 - Nguyen Van Tien", output)
        response = await self.request(path)
        self.assertIn(b"B23DCCN821", response.payload)
        for payload in (b"", b"\xff"):
            self.assertEqual((await self.request(path, aiocoap.POST, payload)).code,
                             aiocoap.BAD_REQUEST)
        self.assertEqual((await self.request("/missing")).code, aiocoap.NOT_FOUND)
        output = await self.run_client("bai1/coap_client_bai1.py", "--uri", BASE + "/missing")
        self.assertIn("4.04 Not Found", output)

    async def test_bai2_updates_monitor_and_alerts(self):
        await self.start_server("bai2/sensor_server_bai2.py")
        path = "/iot/lab/sensor01/data"
        for _ in range(2):
            response = await self.request(path)
            self.assertEqual(response.code, aiocoap.CONTENT)
            self.assertEqual(response.opt.content_format, 50)
            data = json.loads(response.payload)
            self.assertEqual(data["device_id"], "sensor01")
            self.assertTrue(20 <= data["temperature"] <= 40)
            self.assertTrue(30 <= data["humidity"] <= 85)
            print(f"Sensor JSON: {data}")
            await asyncio.sleep(3.1)
        # Kiem tra client thuc te in du lieu dinh ky.
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-u", str(ROOT / "bai2/monitor_client_bai2.py"),
            "--uri", BASE + path, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT)
        self.processes.append(process)
        for _ in range(2):
            while True:
                line = await asyncio.wait_for(process.stdout.readline(), 5)
                self.assertTrue(line, "Monitor dung som")
                print(line.decode().strip())
                if b"------------------------------" in line:
                    break
        # Du lieu co dinh de xac nhan chinh xac ca hai canh bao va bien nguong.
        from bai2.monitor_client_bai2 import show
        import io
        for temperature, humidity, warning in ((36.1, 38.7, True), (35, 40, False)):
            response = aiocoap.Message(code=aiocoap.CONTENT, content_format=50,
                                      payload=json.dumps({"device_id": "sensor01",
                                                          "temperature": temperature,
                                                          "humidity": humidity}).encode())
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                show(response)
            output = captured.getvalue()
            print(output)
            self.assertEqual("CANH BAO: Nhiet do cao" in output, warning)
            self.assertEqual("CANH BAO: Do am thap" in output, warning)

    async def test_bai3_controller_and_multiple_observers(self):
        await self.start_server("bai3/light_server_bai3.py")
        path = "/iot/lab/light01/status"
        observations, pumps, queues = [], [], []
        monitor = None
        try:
            for _ in range(2):
                request = self.ctx.request(aiocoap.Message(code=aiocoap.GET,
                                                           uri=BASE + path, observe=0))
                observations.append(request.observation)
                response = await asyncio.wait_for(request.response, 3)
                self.assertIsNotNone(response.opt.observe)
                self.assertEqual(json.loads(response.payload)["status"], "OFF")
                queue = asyncio.Queue()
                queues.append(queue)

                async def pump(observation, queue):
                    async for response in observation:
                        await queue.put(response)

                pumps.append(asyncio.create_task(pump(request.observation, queue)))

            monitor = await asyncio.create_subprocess_exec(
                sys.executable, "-u", str(ROOT / "bai3/light_monitor_bai3.py"),
                "--uri", BASE + path, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT)
            self.processes.append(monitor)

            async def read_monitor_until(marker):
                while True:
                    line = await asyncio.wait_for(monitor.stdout.readline(), 4)
                    self.assertTrue(line, "Observe monitor dung som")
                    print(line.decode().strip())
                    if marker in line:
                        return

            await read_monitor_until(b"Status: OFF")
            for state in ("ON", "OFF"):
                output = await self.run_client(
                    "bai3/light_controller_bai3.py", "--uri", BASE + path,
                    stdin=f"INVALID\n{state}\nSTATUS\nEXIT\n".encode())
                self.assertIn("Lenh khong hop le", output)
                self.assertIn("2.04 Changed", output)
                self.assertIn(f'"status": "{state}"', output)
                await read_monitor_until(f"Status: {state}".encode())
                for queue in queues:
                    response = await asyncio.wait_for(queue.get(), 3)
                    self.assertEqual(json.loads(response.payload)["status"], state)
                    self.assertEqual(response.opt.content_format, 50)

            response = await self.request(path, aiocoap.PUT,
                                         b'{"device_id":"light01","command":"OFF"}', 50)
            self.assertEqual(response.code, aiocoap.CHANGED)
            for queue in queues:
                with self.assertRaises(TimeoutError):
                    await asyncio.wait_for(queue.get(), 0.3)
            print("PASS: 2 observers received ON/OFF; unchanged OFF sent no notification")
            for payload, code in ((b"not json", aiocoap.BAD_REQUEST),
                                  (b"[]", aiocoap.BAD_REQUEST),
                                  (b'{"device_id":"light01","command":"BAD"}', aiocoap.BAD_REQUEST),
                                  (b'{"device_id":"other","command":"ON"}', aiocoap.NOT_FOUND)):
                self.assertEqual((await self.request(path, aiocoap.PUT, payload, 50)).code, code)
        finally:
            for observation in observations:
                if not observation.cancelled:
                    observation.cancel()
            for task in pumps:
                task.cancel()
            await asyncio.gather(*pumps, return_exceptions=True)

    async def test_client_without_server(self):
        output = await self.run_client("bai1/coap_client_bai1.py", "--uri",
                                       "coap://127.0.0.1:56831/iot/lab/message",
                                       "--timeout", "0.2")
        self.assertIn("Loi ket noi/timeout", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
