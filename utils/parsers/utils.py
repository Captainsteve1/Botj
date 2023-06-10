import base64
import binascii
import re
import struct
from collections import OrderedDict
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union
from urllib.parse import parse_qs, urljoin, urlparse, urlsplit

import isodate

AUDIOMAP = {
    "1": "pcm",
    "mp3": "mp3",
    "mp4a.66": "aac",
    "mp4a.67": "aac",
    "mp4a.68": "aac",
    "mp4a.69": "mp3",
    "mp4a.6B": "mp3",
    "mp4a.40.2": "aac",
    "mp4a.40.02": "aac",
    "mp4a.40.5": "aac",
    "mp4a.40.05": "aac",
    "mp4a.40.29": "aac",
    "mp4a.40.42": "aac",
    "ac-3": "ac3",
    "mp4a.a5": "ac3",
    "mp4a.A5": "ac3",
    "ec-3": "eac3",
    "mp4a.a6": "eac3",
    "mp4a.A6": "eac3",
    "vorbis": "vorbis",
    "opus": "opus",
    "flac": "flac",
    "vp8": "vp8",
    "vp8.0": "vp8",
    "theora": "theora",
}

def dict_to_list(item: Any) -> List[Any]:
    if type(item) in [dict, OrderedDict]: return [item]
    return item

def find_param_value(url: str, param: str) -> str:
    if (value := parse_qs(urlparse(url).query).get(param)):
        return value[0]
    return None

def extract_baseurl(url: str) -> str:
    split = urlsplit(url)
    path = "".join(split.path.rpartition("/")[:-1])
    return url.split(path)[0] + path

def to_seconds(data: str) -> Union[int, float]:
    return isodate.parse_duration(data).total_seconds()

def joinurls(*kwargs) -> str:
    return urljoin(*["%s/" % (
        url.removesuffix("/").removeprefix("/")
        ) for url in list(kwargs)]).removesuffix("/")

def profile_codec_parser(codec: str = None) -> str:
    hevc = r"hvc1\.1|hevc1\.1|hev1\.1"
    hdr = r"hvc1\.2|hevc1\.2|hev1\.2"
    dv = r"dvh"
    avc = r"avc"

    aac = r"mp4a"
    ac3 = r"ac-3"
    eac3 = r"ec-3"

    vtt = r"vtt"
    dfxp = r"ttml|xml|dfxp"

    codec = str(codec)
    if (audio_codec := AUDIOMAP.get(codec)): return audio_codec

    if re.search(hevc, codec): return "hevc"
    if re.search(hdr, codec): return "hdr"
    if re.search(dv, codec): return "dv"
    if re.search(avc, codec): return "avc"

    if re.search(aac, codec): return "aac"
    if re.search(ac3, codec): return "ac3"
    if re.search(eac3, codec): return "eac3"

    if re.search(vtt, codec): return "vtt"
    if re.search(dfxp, codec): return "dfxp"

    return codec


def extract_pssh_box(rawpssh: str) -> str:
    try:
        init = base64.b64decode(rawpssh)
        _, = struct.unpack(">I", init[0:4])
        _, = struct.unpack(">I", init[4:8])
        version, = struct.unpack(">I", init[8:12])
        _ = init[12:28]

        position = 28
        kids = []

        if version == 1:
            num_kids, = struct.unpack(">I", init[position:position+4])
            position += 4
            for _ in range(num_kids):
                kids.append(binascii.b2a_hex(init[position:position+16]).decode())
                position += 16

        data_length, = struct.unpack(">I", init[position:position+4])
        position += 4
        b64pssh = base64.b64encode(init[position:position+data_length]).decode()
        return b64pssh
    except Exception:
        return rawpssh
