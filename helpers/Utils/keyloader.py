import json
import os
import re
import sys

from configs.config import wvripper_config
from helpers.Utils.ripprocess import ripprocess


class ExternalKeys:
    def __init__(self,):
        """CLASS FOR HANDLE EXTERNAL KEYS IN TXT"""
        # self.KEY_REGEX = re.compile(r"[a-z0-9]{32}:[a-z0-9]{32}|[a-z0-9]{1}:[a-z0-9]{32}|[a-z0-9]{32}")
        self.KEY_REGEX = re.compile(r"[a-z0-9]{32}:[a-z0-9]{32}")
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.txt_file = self.config.SETTINGS.external_txt_key

    def __repr__(self,):
        return "{}".format("PASS THE TXT KEYS")

    def open_txt(self, txt_file):
        with open(txt_file, "r") as t:
            return t.readlines()

    def formatter(self, keys):
        return [
            {
                "STREAM": None,
                "TITLE": None,
                "PSSH": None,
                "ID": idx,
                "KID": key.split(":")[0],
                "KEY": key.split(":")[1],
            }
            for idx, key in enumerate(keys, start=1)
        ]

    def create_empty_txt(self,):
        with open(self.txt_file, "w", encoding="utf-8") as f:
            f.write("KID:KEY")

        return

    def get_keys(self):
        KEYS = []
        if not os.path.isfile(self.txt_file):
            self.create_empty_txt()
        for key in self.open_txt(self.txt_file):
            if self.KEY_REGEX.search(key):
                KEYS.append(self.KEY_REGEX.search(key).group())

        return self.formatter(KEYS)


class utils:
    def __init__(self):
        """this class hold the utils for key database"""
        self.ripprocess = ripprocess()

    def jsonDumps(self, file, data, indent=4):
        with open(file, "w") as op:
            op.write(json.dumps(data, indent=indent))

    def jsonLoad(self, file):
        with open(file, "r") as data:
            return json.load(data)

    def formatter(self, keys, stream, pssh, title):
        return [
            {
                "STREAM": stream,
                "TITLE": title,
                "PSSH": pssh,
                "ID": idx,
                "KID": key.split(":")[0],
                "KEY": key.split(":")[1],
            }
            for idx, key in enumerate(keys, start=1)
        ]

    def list_keys(self, data):
        keys = []

        if isinstance(data, dict):
            for _, value in data.items():
                keys += value

        if isinstance(data, list):
            keys += data

        return keys


class database:
    def __init__(self, datafile):
        self.datafile = datafile
        self.utils = utils()
        self.ExternalKeys = ExternalKeys()

    def update(self, keys, stream, pssh, title):
        keys = self.load() + self.utils.formatter(keys, stream, pssh, title)
        self.utils.jsonDumps(self.datafile, keys)

    def load(self):
        if not os.path.isfile(self.datafile):
            self.utils.jsonDumps(self.datafile, [])
        return self.utils.jsonLoad(self.datafile) + self.ExternalKeys.get_keys()


class keyloader:
    def __init__(self, datafile, stream):
        """this class hold the func for key database"""
        self.stream = stream
        self.database = database(datafile)
        self.utils = utils()

    def add_keys(self, keys, pssh=None, name=None):
        self.database.update(keys, self.stream, pssh, name)
        return self.utils.formatter(keys, self.stream, pssh, name)

    def get_key_by_kid(self, kid):
        added = set()
        keys = []

        for key in self.utils.list_keys(self.database.load()):
            if not key["KEY"] in added and key["KID"] == kid:
                keys.append(key)
                added.add(key["KEY"])

        return keys

    def get_key_by_pssh(self, pssh):
        added = set()
        keys = []

        for key in self.utils.list_keys(self.database.load()):
            if key["PSSH"]:
                if not key["KEY"] in added and pssh in key["PSSH"]:
                    keys.append(key)
                    added.add(key["KEY"])

        return keys

    def generate_kid(self, encrypted_file):
        return self.utils.ripprocess.getKeyId(encrypted_file)

    def set_keys(self, keys, no_kid=False):
        command_keys = []
        for key in keys:
            command_keys.append("--key")
            command_keys.append(
                "{}:{}".format(key["ID"] if no_kid else key["KID"], key["KEY"])
            )

        return command_keys
