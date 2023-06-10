import json
import logging
import subprocess
import re
import base64, struct, binascii, re, binascii
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union
from urllib.parse import urljoin


def joinurls(*kwargs) -> str:
    return urljoin(*["%s/" % (
        url.removesuffix("/").removeprefix("/")
        ) for url in list(kwargs)]).removesuffix("/")


def psshBox(
    pssh: Optional[str]
) -> Union[Optional[str], None]:

    try:
        init_data = base64.b64decode(pssh)
        pos = 0

        r_uint32 = init_data[pos:pos+4]
        length, = struct.unpack(">I", r_uint32)
        pos += 4

        r_uint32 = init_data[pos:pos+4]
        pssh, = struct.unpack(">I", r_uint32)
        pos += 4

        r_uint32 = init_data[pos:pos+4]
        version, = struct.unpack("<I", r_uint32)
        pos += 4

        uuid = init_data[pos:pos+16]
        pos += 16

        kids = []
        kid = None

        if version == 1:
            r_uint32 = init_data[pos:pos+4]
            num_kids, = struct.unpack(">I", r_uint32)
            pos += 4

            for i in range(num_kids):
                kids.append(binascii.b2a_hex(init_data[pos:pos+16]).decode())
                pos += 16

        r_uint32 = init_data[pos:pos+4]
        data_length, = struct.unpack(">I", r_uint32)
        pos += 4

        psshdata = init_data[pos:pos+data_length]

        if version == 0:
            kid = psshdata[2:18]

        pos += data_length

        pssh = base64.b64encode(psshdata).decode()
        return pssh
    except Exception:
        return pssh
    return