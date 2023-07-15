import base64
import binascii
import codecs
import glob
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
import urllib.parse
from threading import Thread
from urllib.parse import urlsplit, urlunsplit
from helpers.Utils.ripprocess import ripprocess
import utils.modules.pycaption as pycaption
import pycountry
import requests
import unidecode
import xmltodict
from cryptography.fernet import Fernet
from natsort import natsorted
from titlecase import titlecase

from configs.config import wvripper_config


class mpd_handler:
    def __init__(self):
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.logger = logging.getLogger(__name__)
        self.youtube_dl = self.config.BIN.youtube
        self.ffmpeg = self.config.BIN.ffmpeg
        self.mp4dump = self.config.BIN.mp4dump
        self.ripprocess = ripprocess()

    def extract_kid(self, data):
        try:
            return re.sub(
                " ",
                "",
                re.compile(r"default_KID.*\[(.*)\]").search(data.decode()).group(1),
            )
        except AttributeError:
            return None

    def extract_pssh(self, data):
        WV_SYSTEM_ID = "[ed ef 8b a9 79 d6 4a ce a3 c8 27 dc d5 1d 21 ed]"
        pssh = None
        data = json.loads(data)
        for atom in data:
            if atom["name"] == "moov":
                for child in atom["children"]:
                    if child["name"] == "pssh" and child["system_id"] == WV_SYSTEM_ID:
                        pssh = child["data"][1:-1].replace(" ", "")
                        pssh = binascii.unhexlify(pssh)
                        pssh = pssh[0:]
                        pssh = base64.b64encode(pssh).decode("utf-8")
                        return pssh

        return pssh

    def get_pssh_kid(self, mp4_file):
        cmd = [self.mp4dump, "--format", "json", "--verbosity", "1", mp4_file]
        data = subprocess.check_output(cmd)
        kid = self.extract_kid(data)
        pssh = self.extract_pssh(data)

        return pssh, kid

    def getMpdFormats(self, url, proxies=None, cookies=None):
        jsonfile = "info.info.json"

        yt_cmd = [
            self.youtube_dl,
            "--skip-download",
            "--write-info-json",
            "--quiet",
            "--no-warnings",
            "-o",
            "info",
            url,
        ]

        if cookies:
            yt_cmd += ["--cookies", cookies]

        if proxies:
            yt_cmd += ["--proxy", proxies.get("https")]

        subprocess.call(yt_cmd)

        while not os.path.isfile(jsonfile):
            time.sleep(0.2)
        with open(jsonfile) as js:
            data = json.load(js)
        if os.path.isfile(jsonfile):
            os.remove(jsonfile)

        return data

    def getFragments(self, data, format_id):
        Segments = []
        for fmt in data["formats"]:
            if fmt["format_id"] == format_id:
                base_url = fmt["fragment_base_url"]
                for frag in fmt["fragments"]:
                    url = urllib.parse.urljoin(base_url, frag["path"])
                    Segments.append(url)

        return Segments

    def getUrlBase(self, url):
        split = urlsplit(url)
        path = "".join(split.path.rpartition("/")[:-1])
        return url.split(path)[0] + path

    def getSubsFromMpd(self, url, proxies=None, cookies=None):
        baseurl = self.getUrlBase(url)
        Response = requests.get(url=url, proxies=proxies, cookies=cookies)
        Mpd = json.loads(json.dumps(xmltodict.parse(Response.text)))
        AdaptationSet = Mpd["MPD"]["Period"]["AdaptationSet"]

        subtitles = []

        for track in AdaptationSet:
            if track["@contentType"] == "text":
                Language, langAbbrev = self.ripprocess.countrycode(track["@lang"])
                RepresentationID = track["Representation"]["@id"]
                initialization = track["SegmentTemplate"]["@initialization"]
                initialization = initialization.replace(
                    "$RepresentationID$", RepresentationID
                )
                initialization = initialization.replace(".dash", ".vtt")
                Url = urllib.parse.urljoin(baseurl, initialization)
                Info = {
                    "Language": Language,
                    "langAbbrev": langAbbrev,
                    "Url": Url,
                }
                subtitles.append(Info)

        return subtitles

    def getSegmentsByTrackId(self, baseurl, formats, id):
        Segments = []
        Id = re.sub("/", "_", id)
        for item in formats:
            if item["format_id"] == Id:
                for frag in item["fragments"]:
                    Segments.append(baseurl + frag["path"])

        return Segments

    def remove_dups(self, List, keyword=""):
        Added_ = set()
        Proper_ = []
        for L in List:
            if L[keyword] not in Added_:
                Proper_.append(L)
                Added_.add(L[keyword])

        return Proper_

    def parseMpdUrl(self, url, proxies=None, cookies=None, quality=1080):
        baseurl = self.getUrlBase(url)
        Response = requests.get(url=url, proxies=proxies, cookies=cookies)
        Formats = self.getMpdFormats(url, proxies, cookies)["formats"]
        Mpd = json.loads(json.dumps(xmltodict.parse(Response.text)))
        AdaptationSet = Mpd["MPD"]["Period"]["AdaptationSet"]

        videos = []
        audios = []
        subtitles = []
        VIDEO_PSSH, AUDIO_PSSH = None, None

        for track in AdaptationSet:
            if "video" in track["@mimeType"]:
                if track.get("ContentProtection") is not None:
                    for x in track.get("ContentProtection"):
                        if (
                            x.get("@schemeIdUri")
                            == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
                        ):
                            VIDEO_PSSH = x.get("cenc:pssh")
                            break

        for track in AdaptationSet:
            if "audio" in track["@mimeType"]:
                if track.get("ContentProtection") is not None:
                    for x in track.get("ContentProtection"):
                        if (
                            x.get("@schemeIdUri")
                            == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
                        ):
                            AUDIO_PSSH = x.get("cenc:pssh")
                            break

        for track in AdaptationSet:
            if track["@contentType"] == "text":
                Language, langAbbrev = self.ripprocess.countrycode(track["@lang"])
                Info = {
                    "Language": Language,
                    "langAbbrev": langAbbrev,
                    "Profile": "WEBVTT",
                    "Url": urllib.parse.urljoin(
                        baseurl, track["Representation"]["BaseURL"]["#text"]
                    ),
                }
                subtitles.append(Info)

        for ad in AdaptationSet:
            if ad["@contentType"] == "audio":
                Language, langAbbrev = self.ripprocess.countrycode(ad["@lang"])
                Info = {
                    "Language": Language,
                    "langAbbrev": langAbbrev,
                    "Id": ad["Representation"]["@id"],
                    "Profile": ad["Representation"]["@codecs"],
                    "PSSH": AUDIO_PSSH,
                    "Bitrate": ad["Representation"]["@bandwidth"],
                    "Segments": self.getSegmentsByTrackId(
                        baseurl, Formats, ad["Representation"]["@id"]
                    ),
                }

                audios.append(Info)

        for ad in AdaptationSet:
            if ad["@contentType"] == "video":
                for item in ad["Representation"]:
                    Info = {
                        "Width": item["@width"],
                        "Height": item["@height"],
                        "Id": item["@id"],
                        "Profile": item["@codecs"],
                        "PSSH": VIDEO_PSSH,
                        "Bitrate": item["@bandwidth"],
                        "Segments": self.getSegmentsByTrackId(
                            baseurl, Formats, item["@id"]
                        ),
                    }
                    videos.append(Info)

        videos = sorted(videos, key=lambda k: int(k["Bitrate"]))
        audios = sorted(audios, key=lambda k: int(k["Bitrate"]), reverse=True)
        audios = self.remove_dups(audios, "Language")

        while int(videos[-1]["Height"]) > quality:
            videos.pop(-1)

        return videos, audios, subtitles, baseurl

    def parseMpdFormats(self, data, quality=1080):
        formats = data["formats"]
        videos = []
        audios = []
        for track in formats:
            if "audio" in track["format"] or "audio" in track["format_id"]:
                Language, langAbbrev = "Arabic", "ara"

                if track.get("language"):
                    if track.get("language") != "null":
                        Language, langAbbrev = self.ripprocess.countrycode(
                            track.get("language")
                        )

                Segments = self.getFragments(data, track.get("format_id"))
                Info = {
                    "Protocol": track.get("protocol"),
                    "ID": track.get("format_id"),
                    "Profile": track.get("acodec"),
                    "Bitrate": str(int(float(track["tbr"]))),
                    "Segments": Segments,
                    "Language": Language,
                    "langAbbrev": langAbbrev,
                }
                audios.append(Info)

            if (
                "video" in track["format"]
                or "video" in track["format_id"]
                or "avc" in track["vcodec"]
            ):
                Segments = self.getFragments(data, track.get("format_id"))
                Info = {
                    "Protocol": track.get("protocol"),
                    "ID": track.get("format_id"),
                    "Profile": track.get("vcodec"),
                    "Bitrate": str(int(float(track["tbr"]))),
                    "Segments": Segments,
                    "Width": track.get("width"),
                    "Height": track.get("height"),
                }

                videos.append(Info)

        videos = sorted(videos, key=lambda k: int(k["Bitrate"]))
        audios = sorted(audios, key=lambda k: int(k["Bitrate"]), reverse=True)
        audios = self.remove_dups(audios, "Language")

        while int(videos[-1]["Height"]) > quality:
            videos.pop(-1)

        return videos, audios
