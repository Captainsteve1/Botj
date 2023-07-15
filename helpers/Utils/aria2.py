import asyncio
import contextlib
import logging
import os
import re
import shutil
import subprocess
import sys
from threading import Thread

import pproxy
from configs.config import wvripper_config
from helpers.Utils.ripprocess import ripprocess

non_proxy_env = {key: value for key, value in os.environ.copy(
        ).items() if not key in [
    "http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY"]}

@contextlib.asynccontextmanager
async def start_pproxy(email: str, password: str, host: str, port: int, localhost: str):
    rerouted_proxy = f"http://{localhost}"
    server = pproxy.Server(rerouted_proxy)
    remote = pproxy.Connection(f"http+ssl://{host}:{port}#{email}:{password}")
    handler = await server.start_server(dict(rserver=[remote]))
    try:
        yield rerouted_proxy
    finally:
        handler.close()
        await handler.wait_closed()

class aria2:
    def __init__(self, ):
        self.ripprocess = ripprocess()
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.aria2c_exe = self.config.BIN.aria2c
        self.logger = logging.getLogger(__name__)

    def run(self, command: 'List[str]'):
        exit_code = subprocess.call(command, env=non_proxy_env)
        if exit_code != 0:
            print("Aria2 Exit with %d Commands %s" % (exit_code, " ".join(["\"%s\"" % arg for arg in command])))
            sys.exit(-1)
        print()

    async def run_pproxy(self, command: 'List[str]', proxies):
        print(f"Runing pproxy on {proxies.get('localhost')} to convert https proxies to http")
        proxies = {key: value for key, value in proxies.items() if not key in ("type")}
        async with start_pproxy(**proxies) as proxy:
            command.insert(1, "--all-proxy")
            command.insert(2, proxy)
            proc = await asyncio.create_subprocess_exec(*command, env=non_proxy_env)
            await proc.communicate()
            if proc.returncode != 0:
                print("Aria2 Exit with %d Commands %s" % (proc.returncode, " ".join(["\"%s\"" % arg for arg in command])))
                sys.exit(-1)
            print()

        return

    def aria2DashJoiner(self, fragments, output, fixbytes=False):
        print("\nJoining files...")
        total = int(len(fragments))
        openfile = open(output, "wb")
        for current, fragment in enumerate(fragments):
            if os.path.isfile(fragment):
                if fixbytes:
                    with open(fragment, "rb") as f:
                        wvdll = f.read()
                    if (
                        re.search(
                            b"tfhd\x00\x02\x00\x1a\x00\x00\x00\x01\x00\x00\x00\x02",
                            wvdll,
                            re.MULTILINE | re.DOTALL,
                        )
                        is not None
                    ):
                        fw = open(fragment, "wb")
                        m = re.search(
                            b"tfhd\x00\x02\x00\x1a\x00\x00\x00\x01\x00\x00\x00",
                            wvdll,
                            re.MULTILINE | re.DOTALL,
                        )
                        segment_fixed = (
                            wvdll[: m.end()] + b"\x01" + wvdll[m.end() + 1 :]
                        )
                        fw.write(segment_fixed)
                        fw.close()
                shutil.copyfileobj(open(fragment, "rb"), openfile)
                os.remove(fragment)
                self.ripprocess.updt(total, current + 1)
        openfile.close()
        print()

    def Url(self, url, output, proxies = {}):
        command = [
            self.aria2c_exe, url,
            "--file-allocation=prealloc",
            "--auto-file-renaming=false",
            "--continue=true",
            "--enable-color=true",
            "--download-result=hide",
            "--console-log-level=warn",
            "--summary-interval=0",
            "--retry-wait=5",
            "--max-connection-per-server=16", # split the connection made for one dash server
            "--max-concurrent-downloads=64", # download 64 dash per once
            "--split=16", # split the connection made for one dash request
            "--human-readable=true",
            "-o", output
        ]

        if proxies == {}:
            return self.run(command)

        if proxies != {}:
            if proxies.get('type') == 'http':
                if proxies.get('proxy_url'):
                    command += [f"--all-proxy={proxies.get('proxy_url')}"]
                    return self.run(command)
                    return
                command += [f"--all-proxy={proxies.get('host')}:{proxies.get('port')}", f"--all-proxy-user={proxies.get('email')}", f"--all-proxy-passwd={proxies.get('password')}"]
                return self.run(command)
            elif proxies.get('type') == 'https':
                asyncio.run(self.run_pproxy(command, proxies=proxies))

        return

    def Dash(self, segments, output, proxies = {}, fixbytes=False):
        txt = output.replace(".mp4", ".links")
        folder = output.replace(".mp4", "_Segments")
        segments = list(dict.fromkeys(segments))
        if not os.path.exists(folder): os.makedirs(folder)

        segments_loc = []
        segments_skipped = []

        writer = open(txt, "w+")
        for counter, segment in enumerate(segments):
            out = f"{str(counter).zfill(4)}.mp4"
            out_path = os.path.join(*[os.getcwd(), folder, out])
            segments_loc.append(out_path)

            if os.path.isfile(out_path) and not os.path.isfile("%s.aria2" % out_path):
                segments_skipped.append(out_path)

            if not os.path.isfile(out_path):
                writer.write(f"{segment}\n\tout={out}\n\tdir={folder}\n")
        writer.close()

        command = [
            self.aria2c_exe, f"--input-file={txt}",
            "--file-allocation=prealloc",
            "--auto-file-renaming=false",
            "--continue=true",
            "--enable-color=true",
            "--download-result=hide",
            "--console-log-level=warn",
            "--summary-interval=0",
            "--retry-wait=5",
            "--max-connection-per-server=16",
            "--max-concurrent-downloads=16",
            "--split=16",
            "--human-readable=true",
        ]

        print(F"Downloading {len(segments_loc)} | Skipped {len(segments_skipped)}")

        if proxies == {}:
            self.run(command)

        if proxies != {}:
            if proxies.get('type') == 'http':
                if proxies.get('proxy_url'):
                    command += [f"--all-proxy={proxies.get('proxy_url')}"]
                    return self.run(command)
                    return
                command += [f"--all-proxy={proxies.get('host')}:{proxies.get('port')}", f"--all-proxy-user={proxies.get('email')}", f"--all-proxy-passwd={proxies.get('password')}"]
                self.run(command)
            elif proxies.get('type') == 'https':
                asyncio.run(self.run_pproxy(command, proxies=proxies))

        self.aria2DashJoiner(segments_loc, output, fixbytes=fixbytes)

        return
