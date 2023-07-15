import json
import logging
import os
import sys
import subprocess

from pathlib import Path

from helpers.Utils.ProxyHandler import hold_proxy

PATH = Path(__file__).parent.parent.as_posix()
script = f"{PATH}/Packers/cmrg/main.py"

env = {key: value for key, value in os.environ.copy(
    ).items() if not key in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY")}


class release:
    def __init__(self, filename, pack_settings):
        self.filename = filename
        self.pack_settings = pack_settings
        self.logger = logging.getLogger(__name__)
        self.currentDir = os.getcwd()
        self.releaseDir = os.path.dirname(self.filename)

    def create_shels(self, fp, command):
        fp = Path(fp)
        bat = f"{fp.parent.as_posix()}/windows.bat"
        shell = f"{fp.parent.as_posix()}/linux.bash"

        with open(bat, "w") as b:
            b.write("python %s\n" % ' '.join(['\"%s\"' % arg for arg in command[1:]]))

        with open(shell, "w") as s:
            s.write("python3.9 %s\n" % ' '.join(['\"%s\"' % arg for arg in command[1:]]))

        return

    def upload(self):
        if os.path.isfile(self.filename) and os.path.isfile(script) and self.pack_settings["upload"]:
            command = ["python", script, "--path", self.filename]
            command.extend(["--trackers", self.pack_settings["trackers"]])

            if self.pack_settings["content_type"]:
                command.extend(["--type", self.pack_settings["content_type"]])

            if self.pack_settings["description"]:
                command.extend(["--desc", self.pack_settings["description"]])

            if self.pack_settings["seed"]:
                command.append("--seed")

            if self.pack_settings["local_seed"]:
                command.append("--local-seed")

            print("packing arguments: %s" % " ".join([str(c) for c in command]))

            self.create_shels(self.filename, command)
            subprocess.call(command, env=env)


        return
