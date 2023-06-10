import json
import os
import re
from typing import Any, Dict, List, NamedTuple, Optional, Union
from uuid import uuid4

import requests
import xmltodict
from m3u8 import parse as m3u8parser

from .utils import (dict_to_list, extract_baseurl, extract_pssh_box,
                    find_param_value, joinurls, profile_codec_parser,
                    to_seconds)

class M3U8:
    BASEURL: str = None
    WIDEVINE_URN: str = "URN:UUID:EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED"
    KNOWN_TRACKS_TYPES: List[str] = ["AUDIO", "VIDEO", "TEXT", "APPLICATION"]

class m3u8extractor:
    def __init__(self):
        ...

    def get_download_type(self, track_data: Dict[str, Any]) -> str:
        if track_data.get("stream_info"): return "video"
        if track_data.get("type", "NONE") == "AUDIO": return "audio"
        if track_data.get("type", "NONE") == "SUBTITLES": return "timedtext"
        return None

    def get_codec(self, track_data: Dict[str, Any]) -> str:
        if track_data.get("stream_info"):
            codecs = track_data.get("stream_info").get("codecs", "none")
            video_range = track_data.get("stream_info").get("video_range", "none").lower()
            if "avc" in codecs and video_range == "sdr": codec, profile = [c for c in codecs.split(",") if "avc" in c][0], "avc" ; return {"codec": codec, "profile": profile}
            if "hvc" in codecs and video_range == "sdr": codec, profile = [c for c in codecs.split(",") if "hvc" in c][0], "hevc" ; return {"codec": codec, "profile": profile}
            if "hvc" in codecs and video_range == "pq": codec, profile = [c for c in codecs.split(",") if "hvc" in c][0], "hdr" ; return {"codec": codec, "profile": profile}
            if "dv" in codecs and video_range == "pq": codec, profile = [c for c in codecs.split(",") if "dv" in c][0], "dv" ; return {"codec": codec, "profile": profile}
            if "avc" in codecs: codec, profile = [c for c in codecs.split(",") if "avc" in c][0], "avc" ; return {"codec": codec, "profile": profile}
            if "hvc" in codecs and "120.90" in codecs: codec, profile = [c for c in codecs.split(",") if "hvc" in c][0], "hevc" ; return {"codec": codec, "profile": profile}
            if "hvc" in codecs: codec, profile = [c for c in codecs.split(",") if "hvc" in c][0], "hdr" ; return {"codec": codec, "profile": profile}
            if "dv" in codecs: codec, profile = [c for c in codecs.split(",") if "dv" in c][0], "dv" ; return {"codec": codec, "profile": profile}
            return {"codec": codecs, "profile": codecs}

        if track_data.get("type", "NONE") == "AUDIO":
            codec = track_data.get("group_id")
            profile = codec
            if re.search(r"stereo|aac", codec): profile = "aac"
            if re.search(r"ac3", codec): profile = "ac3"
            if re.search(r"eac3|joc|atmos", codec): profile = "eac3"

            return {"codec": codec, "profile": profile}

        if track_data.get("type", "NONE") == "SUBTITLES":
            codec = track_data.get("group_id")
            profile = codec

            return {"codec": codec, "profile": profile}

        return {"codec": None, "profile": None}

    def get_framerate(self, track_data: Dict[str, Any]) -> Union[str, float]:
        if (framerate := track_data.get("stream_info", {}).get("frame_rate")):
            try:
                framerate = float(framerate)
            except Exception:
                pass

        return framerate

    def detect_atmos(self, track_data: Dict[str, Any]) -> bool:
        if track_data.get("type", "NONE") == "AUDIO":
            if re.search(r"joc|atmos", track_data.get("group_id")):
                return True
        return False

    def get_bitrate(self, track_data: Dict[str, Any]) -> int:
        if track_data.get("type", "NONE") == "SUBTITLES":
            return 0

        if track_data.get("type", "NONE") == "AUDIO":
            if (url := track_data.get("uri")):
                for regex in [r"([0-9]*)k_", r"([0-9]*)_complete", r"_gr([0-9]*)"]:
                    if (bitrate := re.search(regex, url)):
                        bitrate = bitrate.group(1)
                        if bitrate.isdigit():
                            return 768 if int(bitrate) >= 768 else int(bitrate)

            if (bitrate := find_param_value(url, "g")):
                if bitrate.isdigit():
                    return 768 if int(bitrate) >= 768 else bitrate

        if (bitrate := track_data.get("stream_info", {}).get("bandwidth")):
            return int(float(int(bitrate) / 1000))

        return 0

    def get_width(self, track_data: Dict[str, Any]) -> int:
        width = track_data.get("@width") if track_data.get("@width") else track_data.get("@width")
        return int(width) if width else None

    def get_height(self, track_data: Dict[str, Any]) -> int:
        height = track_data.get("@height") if track_data.get("@height") else track_data.get("@height")
        return int(height) if height else None

    def get_language(self, track_data: Dict[str, Any]) -> str:
        return track_data.get("language")

    def get_channels(self, track_data: Dict[str, Any]) -> float:
        if (channels := track_data.get("channels")):
            channels = re.sub(r'/JOC|"', "", channels)
            try:
                channels = float(channels)
                if channels == 6.0: channels = 5.1
            except Exception:
                pass
            return channels

        return None

    def get_url(self, baseurl: str, track_data: Dict[str, Any]) -> str:
        if track_data.get("uri"):
            return track_data.get("uri") if track_data.get("uri").startswith("http") else joinurls(baseurl, track_data.get("uri"))
        return None

    def get_resolution(self, track_data: Dict[str, Any]) -> str:
        width, height = None, None
        if track_data.get("stream_info"):
            width = int(track_data.get("stream_info").get("resolution").split("x")[0])
            height = int(track_data.get("stream_info").get("resolution").split("x")[1])

        return {"height": height, "width": width}

    def get_content_type(self, track_data: Dict[str, Any]) -> str:
        if track_data.get("type", "NONE") == "AUDIO":
            if (characteristics := track_data.get("characteristics")):
                if characteristics.startswith("public.accessibility"):
                    return "descriptive"
            return "dialog"

        if track_data.get("type", "NONE") == "SUBTITLES":
            if "_sdh_" in track_data.get("uri").lower(): return "sdh"
            if "_forced_" in track_data.get("uri").lower(): return "forced"
            if "_normal_" in track_data.get("uri").lower(): return "normal"
            if (characteristics := track_data.get("characteristics")):
                if characteristics.startswith("public.accessibility"): return "sdh"
            if track_data.get("forced", "NO") == "YES": return "forced"
            return "normal"

        if track_data.get("stream_info"): return "content"
        return None

    def get_pssh(self) -> str:
        for key in self.data.get("keys", []):
            if isinstance(key, dict):
                if key.get("keyformat", "NONE").upper() == self.M3U8.WIDEVINE_URN:
                    uri = key.get("uri", "none")
                    pssh = uri.partition("base64,")[2]
                    return uri, pssh
        return None, None

class pym3u8(m3u8extractor):
    def __init__(self, content: str, from_file=None, from_str=None, headers: Dict[str, Any] = {}):
        self.M3U8 = M3U8
        self.content = content
        self.session = requests.Session()
        self.headers = headers
        self.youtubedl_data = None
        self.m3u8_data = ""
        self.from_file = from_file
        self.from_str = from_str
        self.data = self.extract_m3u8(self.content)
        self.M3U8.BASEURL = extract_baseurl(self.content) if self.content.startswith("http") else None
        m3u8extractor.__init__(self)

    def extract_m3u8(self, data: str) -> Dict[str, Any]:
        if self.from_str:
            return m3u8parser(self.from_str)
        if self.from_file:
            with open(self.from_file, "r", encoding="utf-8") as f:
                return m3u8parser(f.read())
        self.m3u8_data = self.session.get(data, headers=self.headers).content.decode("utf-8")
        # self.m3u8_data = m3u8parser(self.m3u8_data)
        return m3u8parser(self.m3u8_data)

    def get_sub_segments_by_duration(self) -> List[str]:
        assert self.M3U8.BASEURL != None
        segment = sorted(self.data["segments"], key=lambda k: int(k["duration"]))[-1]
        return segment.get("uri") if segment.get("uri").startswith("http") else joinurls(self.M3U8.BASEURL, segment.get("uri"))

    def get_sub_segments(self) -> List[str]:
        assert self.M3U8.BASEURL != None
        return list(dict.fromkeys([segment.get("uri") if segment.get("uri").startswith("http") else joinurls(self.M3U8.BASEURL, segment.get("uri")) for segment in self.data["segments"]]))

    def get_segments(self,) -> List[Dict[str, Any]]:
        assert self.M3U8.BASEURL != None
        uri, raw_pssh = self.get_pssh()
        durations = []
        duration = 0
        for segment in self.data["segments"]:
            if segment.get("discontinuity"):
                durations.append(duration)
                duration = 0
            duration += segment.get("duration")
        durations.append(duration)
        largest_continuity = durations.index(max(durations))
        discontinuity = 0
        main_segs = []

        for segment in self.data["segments"]:
            if segment.get("discontinuity"):
                discontinuity += 1

            if discontinuity == largest_continuity:
                main_segs.append(segment)


        segments = []
        inits = [s.get("init_section", {}).get("uri") for s in main_segs if s.get("init_section", {}).get("uri")]
        init = inits[0]
        init = init if init.startswith("http") else joinurls(self.M3U8.BASEURL, init)
        segments.append(init)

        for s in main_segs:
            s = s.get("uri") if s.get("uri").startswith("http") else joinurls(self.M3U8.BASEURL, s.get("uri"))
            segments.append(s)

        return {"segments": segments, "total": len(segments), "raw_pssh": raw_pssh, "pssh" : extract_pssh_box(raw_pssh)}

        # segments.extend(
        #     list(dict.fromkeys([s.get("uri") if s.get("uri").startswith("http") else joinurls(self.M3U8.BASEURL, s.get("uri")) for s in main_segs]))
        #     )

        # return {"segments": segments, "total": len(segments), "raw_pssh": raw_pssh, "pssh" : extract_pssh_box(raw_pssh)}

        # for seg in main_segs:
        #     init = s.get("init_section", {}).get("uri")
        #     segments.append(seg)


        # for s in main_segs:
        #     init = s.get("init_section", {}).get("uri")
        #     if init:
        #         seg_list = [init if init.startswith("http") else joinurls(self.M3U8.BASEURL, init)]
        #         seg_list += list(dict.fromkeys([s.get("uri") if s.get("uri").startswith("http") else joinurls(self.M3U8.BASEURL, s.get("uri")) for s in main_segs]))
        #         seg_list = {"segments": seg_list, "total": len(seg_list), "raw_pssh": raw_pssh, "pssh" : extract_pssh_box(raw_pssh)}
        #         return seg_list

        # return []

    def tracks(self) -> List[Dict[str, Any]]:
        assert self.M3U8.BASEURL != None
        tracks = [{
            "protocol" : "hls",
            "download_type" : self.get_download_type(track_data),
            **self.get_codec(track_data),
            "framerate" : self.get_framerate(track_data),
            "atmos_track" : self.detect_atmos(track_data),
            "bitrate" : self.get_bitrate(track_data),
            **self.get_resolution(track_data),
            "language" : self.get_language(track_data),
            "channels" : self.get_channels(track_data),
            "url" : self.get_url(self.M3U8.BASEURL, track_data),
            "content_type" : self.get_content_type(track_data),
            "track_number" : track_number
        } for track_number, track_data in enumerate(self.data["playlists"] + self.data["media"], start=1)]

        # tracks = [t for t in tracks if t["download_type"]]
        # ac3 = [t for t in tracks if t["profile"] == "ac3"]
        # ac3 = ac3 or [t for t in tracks if t["profile"] == "aac"]
        # ac3 = ac3 or [t for t in tracks if t["profile"] == "eac3"]
        # avc = [t for t in tracks if t["profile"] == "avc"]
        return tracks # [t for t in tracks if t["download_type"]]
