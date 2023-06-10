import base64
import binascii
import glob
import html
import json
import logging
import os
import re
import shutil
import string
import subprocess
import sys
import time
import unicodedata
from collections.abc import Sequence
from collections import namedtuple

import ffmpy
import pycountry
import requests
import tldextract
import tqdm
import unidecode
import yarl
from natsort import natsorted
from titlecase import titlecase

from configs.config import wvripper_config
from utils.modules.youtube_dl import YoutubeDL




class ripprocess(object):
    def __init__(self):
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.logger = logging.getLogger(__name__)

    def get_pssh_from_kid(self, kid):
        array_of_bytes = bytearray(b"\x00\x00\x002pssh\x00\x00\x00\x00")
        array_of_bytes.extend(bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed"))
        array_of_bytes.extend(b"\x00\x00\x00\x12\x12\x10")
        array_of_bytes.extend(bytes.fromhex(kid.replace("-", "")))
        pssh = base64.b64encode(bytes.fromhex(array_of_bytes.hex()))
        return pssh.decode()

    def sort_list(self, media_list, keyword1=None, keyword2=None):
        if keyword1:
            if keyword2:
                return sorted(
                    media_list, key=lambda k: (int(k[keyword1]), int(k[keyword2]))
                )
            else:
                sorted(media_list, key=lambda k: int(k[keyword1]))

        return media_list

    def yt2json(self, url, proxies=None, pyversion=True):
        jsonfile = "info.info.json"

        if pyversion:
            
            options = {
                'writeinfojson': True,
                'skip_download' : True,
                'outtmpl' : 'info',
                'no_warnings': True,
                'quiet': True
            }

            if proxies:
                options.update({"proxies": proxies})

            with YoutubeDL(options) as ydl:
                ydl.download([url])

        else:
            options = [
                self.config.BIN.youtube,
                "--skip-download",
                "--write-info-json",
                "--quiet",
                "--no-warnings",
                "-o",
                "info",
                url,
            ]

            if proxies:
                options += ["--proxy", proxies.get("https")]

            subprocess.call(options)


        with open(jsonfile) as js:
            data = json.load(js)

        os.remove(jsonfile)

        return data

    def parse_proxy_url(self, url):
        url = yarl.URL(url)
        config = {
            "scheme": url.scheme,
            "user": url.user,
            "password": url.password,
            "host": url.host,
            "port": url.port,
        }

        return config

    def getKeyId(self, mp4_file):
        data = subprocess.check_output(
            [self.config.BIN.mp4dump, "--format", "json", "--verbosity", "1", mp4_file]
        )
        try:
            return re.sub(" ", "", re.compile(r"default_KID.*\[(.*)\]").search(data.decode()).group(1),)
        except AttributeError:
            return None

    def flatten(self, l):
        return list(self.flatten_g(l))

    def flatten_g(self, l):
        basestring = (str, bytes)
        for el in l:
            if isinstance(el, Sequence) and not isinstance(el, basestring):
                for sub in self.flatten_g(el):
                    yield sub
            else:
                yield el

    def removeExtentsion(self, string: str):
        if "." in string:
            return ".".join(string.split(".")[:-1])
        else:
            raise ValueError("string has no extentsion: {}".format(string))

    def replaceExtentsion(self, string: str, ext: str):
        if "." in string:
            return ".".join(string.split(".")[:-1]) + f".{ext}"
        else:
            raise ValueError("string has no extentsion: {}".format(string))

    def domain(self, url):
        return "{0.domain}.{0.suffix}".format(tldextract.extract(url))

    def remove_dups(self, List, keyword=""):
        Added_ = set()
        Proper_ = []
        for L in List:
            if L[keyword] not in Added_:
                Proper_.append(L)
                Added_.add(L[keyword])

        return Proper_

    def find_str(self, s, char):
        index = 0

        if char in s:
            c = char[0]
            for ch in s:
                if ch == c:
                    if s[index : index + len(char)] == char:
                        return index

                index += 1

        return -1

    def updt(self, total, progress):
        barLength, status = 80, ""
        progress = float(progress) / float(total)
        if progress >= 1.0:
            progress, status = 1, "\r\n"
        block = int(round(barLength * progress))
        text = "\r{} | {:.0f}% {}".format(
            "█" * block + "" * (barLength - block), round(progress * 100, 0), status,
        )
        sys.stdout.write(text)
        sys.stdout.flush()

    def Get_PSSH(self, mp4_file):
        WV_SYSTEM_ID = "[ed ef 8b a9 79 d6 4a ce a3 c8 27 dc d5 1d 21 ed]"
        pssh = None
        stdout = subprocess.check_output(
            [self.config.BIN.mp4dump, "--format", "json", "--verbosity", "1", mp4_file],
        encoding="utf8")
        data = json.loads(stdout)
        for atom in data:
            if atom["name"] == "moov":
                for child in atom["children"]:
                    if child["name"] == "pssh":
                        if child["system_id"] == WV_SYSTEM_ID:
                            pssh = child["data"][1:-1].replace(" ", "")
                            pssh = binascii.unhexlify(pssh)
                            if pssh.startswith(b"\x08\x01"):
                                pssh = pssh[0:]
                            pssh = base64.b64encode(pssh).decode("utf-8")
                            return pssh

        return None

    def parseCookieFile(self, cookiesfile):
        cookies = {}
        with open(cookiesfile, "r") as fp:
            for line in fp:
                if not re.match(r"^\#", line):
                    lineFields = line.strip().split("\t")
                    try:
                        cookies[lineFields[5]] = lineFields[6]
                    except Exception:
                        pass
        return cookies

    def countrycode(self, code, site_domain="None"):
        languageCodes = {
            "zh-Hans": "zhoS",
            "zh-Hant": "zhoT",
            "pt-BR": "brPor",
            "es-ES": "euSpa",
            "en-GB": "enGB",
            "en-PH": "enPH",
            "nl-BE": "nlBE",
            "fil": "enPH",
            "yue": "zhoS",
            "fr-CA": "caFra",
        }

        for langcode, langname, lange_lang in [
            ("cmn-Hans", "Mandarin Chinese (Simplified)", "zh-Hans"),
            ("cmn-Hant", "Mandarin Chinese (Traditional)", "zh-Hant"),
            ("es-419", "Spanish", "spa"),
            ("es-ES", "European Spanish", "euSpa"),
            ("pt-BR", "Brazilian Portuguese", "brPor"),
            ("pt-PT", "Portuguese", "por"),
            ("fr-CA", "French Canadian", "caFra"),
            ("fr-FR", "French", "fra"),
            ("iw", "Modern Hebrew", "heb"),
            # ("es", "European Spanish", "euSpa"),
        ]:
            if langcode == code:
                return langname, lange_lang

        lang_code = code[: code.index("-")] if "-" in code else code
        lang = pycountry.languages.get(alpha_2=lang_code)
        if lang is None:
            lang = pycountry.languages.get(alpha_3=lang_code)

        try:
            languagecode = languageCodes[code]
        except KeyError:
            languagecode = lang.alpha_3

        return self.clean_text(lang.name), languagecode

    def isduplelist(self, a, b):
        return set(a) == set(b) and len(a) == len(b)

    def readfile(self, file, lines=False):
        read = ""
        if os.path.isfile(file):
            with open(file, "r") as f:
                if lines:
                    read = f.readlines()
                    return read
            read = f.read()
        else:
            self.logger.info("File: %s, is not found" % file)
            return None

        return read

    def strip(self, inputint, left=True, right=False):
        if left:
            return str(inputint.lstrip("0"))
        if right:
            return str(inputint.rstrip("0"))

        return

    def RemoveExtraWords(self, name):
        if re.search("[eE]pisode [0-9]+", name):
            name = name.replace((re.search("[eE]pisode [0-9]+", name)).group(0), "")

        if re.search(r"(\(.+?)\)", name):
            name = name.replace(re.search(r"(\(.+?)\)", name).group(), "")

        if re.search(r"(\[.+?\])", name):
            value = re.search(r"(\[.+?\])", name).group()
            name = name.replace(value, "")

        name = (
            name.replace(" : ", " ")
            .replace(": ", " ")
            .replace(",", "")
            .replace(":", " ")
            .replace("&", "and")
            .replace("ÃƒÂ³", "o")
            .replace("'", "")
            .replace('"', "")
        )
        name = re.sub(" +", " ", name)
        name = name.strip()

        return name

    def DecodeString(self, text):
        for encoding in ("utf-8-sig", "utf-8", "utf-16"):
            try:
                return text.decode(encoding)
            except UnicodeDecodeError:
                continue

        return text.decode("latin-1")

    def EncodeString(self, text):
        for encoding in ("utf-8-sig", "utf-8", "utf-16"):
            try:
                return text.encode(encoding)
            except UnicodeDecodeError:
                continue

        return text.encode("latin-1")

    def clean_text(self, text):
        whitelist = (
            "-_.() %s%s" % (string.ascii_letters, string.digits) + "',&#$%@`~!^&+=[]{}"
        )

        cleaned_text = (
            unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()
        )

        return "".join(c for c in cleaned_text if c in whitelist)

    def RemoveCharcters(self, text):
        text = self.EncodeString(text)
        text = self.DecodeString(text)
        text = self.RemoveExtraWords(text)
        text = self.clean_text(text)
        text = unidecode.unidecode(titlecase(text))

        return text

    def clean_dir(self, title):
        for file in glob.glob(f"{title}*.*"):
            if not file.endswith(".mkv"):
                try:
                    os.remove(file)
                except Exception:
                    self.logger.info(f"{file} cant be erased.")
        return

    def FixInvalidJson(self, jsonStr):
        jsonStr = re.sub(r'\\', '', jsonStr)
        jsonStr = re.sub(r'{"', '{`', jsonStr)
        jsonStr = re.sub(r'"}', '`}', jsonStr)
        jsonStr = re.sub(r'":"', '`:`', jsonStr)
        jsonStr = re.sub(r'":', '`:', jsonStr)
        jsonStr = re.sub(r'","', '`,`', jsonStr)
        jsonStr = re.sub(r'",', '`,', jsonStr)
        jsonStr = re.sub(r',"', ',`', jsonStr)
        jsonStr = re.sub(r'\["', '\[`', jsonStr)
        jsonStr = re.sub(r'"\]', '`\]', jsonStr)
        jsonStr = re.sub(r'"',' ', jsonStr)
        jsonStr = re.sub(r'\`','\"', jsonStr)
        return json.loads(jsonStr)

    def FixInvalidJson2(self, jsonStr):
        jsonStr = re.sub(r'\\', '', jsonStr)

        try:
            return json.loads(jsonStr)
        except ValueError:
            while True:
                b = re.search(r'[\w|"]\s?(")\s?[\w|"]', jsonStr)
                if not b:
                    break

                s, e = b.span(1)
                c = jsonStr[s:e]
                c = c.replace('"',"'")
                jsonStr = jsonStr[:s] + c + jsonStr[e:]

            return json.loads(jsonStr)

class EpisodesNumbersHandler:
    def __init__(self):
        return

    def numberRange(self, start: int, end: int):
        if list(range(start, end + 1)) != []:
            return list(range(start, end + 1))

        if list(range(end, start + 1)) != []:
            return list(range(end, start + 1))

        return [start]

    def ListNumber(self, Number: str):
        if Number.isdigit():
            return [int(Number)]

        if Number.strip() == "~" or Number.strip() == "":
            return self.numberRange(1, 999)

        if "-" in Number:
            start, end = Number.split("-")
            if start.strip() == "" or end.strip() == "":
                raise ValueError("wrong Number: {}".format(Number))
            return self.numberRange(int(start), int(end))

        if "~" in Number:
            start, _ = Number.split("~")
            if start.strip() == "":
                raise ValueError("wrong Number: {}".format(Number))
            return self.numberRange(int(start), 999)

        return

    def sortNumbers(self, Numbers):
        SortedNumbers = []
        for Number in Numbers.split(","):
            SortedNumbers += self.ListNumber(Number.strip())

        return natsorted(list(set(SortedNumbers)))
