import json
import math
import os
import re
from collections import OrderedDict
from typing import Any, Dict, List, NamedTuple, Optional, Union
from urllib.parse import urljoin, urlsplit

import isodate
import requests
import xmltodict

from .utils import joinurls, psshBox


class MPD(object):
    def __init__(self, mpd):
        self.session = requests.Session()
        self.mpd = mpd
        self.data = None
        self.baseurl = None
        self.mpdbaseurl = None
        self.duration = None
        self.buffertime = None
        self.adaptationset = []
        self.widevine_urn = "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
        self.known_tracks_types = ["audio", "video", "text"]
        self.parse()

    def joinurls(self, *kwargs) -> joinurls:
        return joinurls(*kwargs)

    def dict_to_list(self, item: Any) -> List[Any]:
        if type(item) in [dict, OrderedDict]: return [item]
        return item

    def extract_baseurl(self, url: str) -> str:
        split = urlsplit(url)
        path = "".join(split.path.rpartition("/")[:-1])
        print(url)
        print('split')
        print(split)
        print('path')
        print(path)
        print('return')
        print(url.split(path)[0] + path)
        return url.split(path)[0] + path

    def to_seconds(self, data: str) -> Union[int, float]:
        return isodate.parse_duration(data).total_seconds()

    def mpdtodict(self, data: str) -> xmltodict.parse:
        if isinstance(data, dict) and data.get("MPD"):
            return data
        if isinstance(data, str) and data.startswith("http"):
            return json.loads(json.dumps(xmltodict.parse(self.session.get(data).text)))
        if isinstance(data, str) and os.path.isfile(data):
            return json.loads(json.dumps(xmltodict.parse(open(data, "r").read())))
        if isinstance(data, str) and data.__contains__("MPD"):
            return json.loads(json.dumps(xmltodict.parse(data)))
        return None

    def parse(self) -> None:
        self.data = self.mpdtodict(self.mpd)
        if self.data.get("MPD", {}).get("@mediaPresentationDuration"):
            self.duration = self.to_seconds(self.data.get("MPD").get("@mediaPresentationDuration"))
        if self.data.get("MPD", {}).get("@minBufferTime"):
            self.buffertime = self.to_seconds(self.data.get("MPD").get("@minBufferTime"))
        self.adaptationset = self.load_adaptationset()
        if isinstance(self.mpd, str) and self.mpd.startswith("http"):
            #self.baseurl = self.extract_baseurl(self.mpd)
            self.baseurl = self.data.get("MPD").get("BaseURL")
            if self.data.get("MPD").get("Period").get("BaseURL"):
                self.baseurl = self.baseurl + self.data.get("MPD").get("Period").get("BaseURL")
        if self.data.get("MPD").get("BaseURL"):
            self.mpdbaseurl = self.data.get("MPD").get("BaseURL") 
            if self.data.get("MPD").get("Period").get("BaseURL"):
                self.mpdbaseurl = self.mpdbaseurl + self.data.get("MPD").get("Period").get("BaseURL")
            print(self.mpdbaseurl)
         
        return

    def load_adaptationset(self) -> List[Dict[str, Any]]:
        tracks = []
        periods = self.dict_to_list(self.data["MPD"]["Period"])
        for i, period in enumerate(periods):
            periods[i]["AdaptationSets"] = self.dict_to_list(period["AdaptationSet"])
            del periods[i]["AdaptationSet"]
            for ii, adaptation_set in enumerate(period["AdaptationSets"]):
                periods[i]["AdaptationSets"][ii]["Representations"] = self.dict_to_list(adaptation_set["Representation"])
                del periods[i]["AdaptationSets"][ii]["Representation"]

        for ad in period["AdaptationSets"]:
            if not (contenttype := ad.get("@contentType")):
                contenttype = ad.get("@mimeType").split("/")[0]
            if contenttype in self.known_tracks_types:
                tracks += [ad]
        return tracks

    def sort_type(self, contenttype: str) -> List[Dict[str, Any]]:
        tracks = []
        for t in self.adaptationset:
            if not (_contenttype := t.get("@contentType")):
                _contenttype = t.get("@mimeType").split("/")[0]
            if _contenttype == contenttype:
                tracks += [t]
        return tracks

class PARSER(object):
    def __init__(self, mpd: MPD):
        self.mpd = mpd

    def int_or_(self, item: Union[str, int]) -> Union[str, int]:
        if isinstance(item, str):
            try:
                return int(item)
            except Exception:
                pass
        return item

    def get_or_none(self, item: str, *kwargs) -> Union[str, None]:
        for data in kwargs:
            if data.get(item): return self.int_or_(data.get(item))
        return None

    def convert_fps(self, fps: str) -> Union[str, int]:
        if isinstance(fps, int): return int(fps)
        try:
            n1, n2 = fps.split("/")
            fps = float(int(n1) / int(n2)) * 10
            return f"{fps:0.3f}"
        except Exception:
            return fps

        return

    def extract_range(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if (_range := data.get("SegmentBase", {} ).get("Initialization", {} ).get("@range")):
            return {"Range": "bytes={}".format(_range)}
        return None

    def extract_pssh(self, data: Dict[str, Any]) -> str:
        pssh = None
        if (contentprotection := data.get("ContentProtection")):
            for protection in self.mpd.dict_to_list(contentprotection):
                if protection.get("@schemeIdUri").lower() == self.mpd.widevine_urn:
                    if not (pssh := protection.get("cenc:pssh")):
                        pssh = protection.get("pssh")
                    if isinstance(pssh, str):
                        return pssh
                    if isinstance(pssh, dict):
                        return pssh.get("#text")
        return pssh

    def item_type(self, data: Dict[str, Any]) -> Optional[bool]:
        if data.get("BaseURL"):
            return "http"
        return "dash"

    def detect_profile(self, data: str) -> str:
        if not isinstance(data, str):
            return data
        if data.__contains__("hvc1.2"):
            return "hdr"
        if data.__contains__("hvc1.1"):
            return "hevc"
        if data.__contains__("hevc"):
            return "hevc"
        if data.__contains__("dvh"):
            return "dv"
        if data.__contains__("avc"):
            return "avc"
        if data.__contains__("mp4a"):
            return "aac"
        if data.__contains__("ec-3"):
            return "eac3"
        if data.__contains__("ac-3"):
            return "ac3"
        if data.__contains__("vtt"):
            return "vtt"
        if data.__contains__("ttml"):
            return "dfxp"
        if data.__contains__("xml"):
            return "dfxp"

        return data

    def tracks(self, baseurl: str) -> None:
        tracks = []
        for track in self.mpd.adaptationset:
            if not (contenttype := self.get_or_none("@contentType", track)):
                contenttype = track.get("@mimeType").split("/")[0]
            #print(tracks)
            for index, item in enumerate(track.get("Representations")):
                codec = self.get_or_none("@codecs", item, track)
                profile = self.detect_profile(self.get_or_none("@codecs", item, track))
                fps = self.convert_fps(self.get_or_none("@frameRate", item, track))
                bitrate = self.get_or_none("@bandwidth", item, track)
                if isinstance(bitrate, int): bitrate = int(float(bitrate / 1000))
                width = self.get_or_none("@width", item, track)
                height = self.get_or_none("@height", item, track)
                language = self.get_or_none("@lang", item, track)
                pssh = self.extract_pssh(track)
                init_headers_range = self.extract_range(item)
                download_type = self.item_type(item)
                #print(item)
                
                if download_type == "http":
                    url = item.get("BaseURL") #
                    print(url)
                    if not isinstance(url, str): url = url.get("#text") if url else None
                    tracks += [{
                        "url": joinurls(baseurl, url),
                        "fps": fps,
                        "bitrate": bitrate,
                        "width": width,
                        "height": height,
                        "pssh_p": psshBox(pssh),
                        "pssh": pssh,
                        "init_headers_range": init_headers_range,
                        "language": language,
                        "codec": codec,
                        "profile": profile,
                        "baseurl": baseurl,
                        "buffertime": self.mpd.buffertime,
                        "duration": self.mpd.duration,
                        "contenttype": contenttype,
                        "id": index,
                        "download_type": download_type,
                    }]
                elif download_type == "dash":
                    if not (segmenttemplate := self.get_or_none("SegmentTemplate", item, track)):
                        raise ValueError("Couldn't find a SegmentTemplate for a Representation")

                    if not segmenttemplate.get("@startNumber"):
                        segmenttemplate["@startNumber"] = 0

                    dash_information = {
                        "id": item.get("@id"),
                        "baseurl": baseurl,
                        "init": segmenttemplate.get("@initialization"),
                        "segment": segmenttemplate.get("@media"),
                    }

                    if segmenttemplate.get("SegmentTimeline"):
                        timeline = self.mpd.dict_to_list(segmenttemplate.get("SegmentTimeline").get("S"))
                        seg_num_list = []
                        current_time = 0
                        for s in timeline:
                            if "@t" in s:
                                current_time = int(s["@t"])
                            for _ in range(1 + (int(s["@r"]) if "@r" in s else 0)):
                                seg_num_list.append(current_time)
                                current_time += int(s["@d"])
                    else:
                        start = segmenttemplate.get("@startNumber", 0)
                        timescale = segmenttemplate.get("@timescale")
                        segment_duration = segmenttemplate.get("@duration")
                        period_duration = self.mpd.to_seconds(item.get("@duration")) if item.get("@duration") else self.mpd.to_seconds(self.mpd.data["MPD"].get("@mediaPresentationDuration"))
                        segment_duration = float(segment_duration) / float(timescale)
                        total_segments = math.ceil(period_duration / segment_duration)
                        seg_num_list = range(int(start), int(start) + total_segments)

                    segments = []
                    segments.append(urljoin(dash_information["baseurl"], dash_information["init"].replace("$RepresentationID$", dash_information["id"].replace("/", "_"))))
                    for seg in seg_num_list:
                        segment = dash_information["segment"]
                        segment = segment.replace("$RepresentationID$", dash_information["id"].replace("/", "_"))
                        segment = segment.replace("$Number$", str(seg))
                        segment = segment.replace("$Time$", str(seg))
                        segment = urljoin(dash_information["baseurl"], segment)
                        segments.append(segment)

                    tracks += [{
                        "segments": segments,
                        "fps": fps,
                        "bitrate": bitrate,
                        "width": width,
                        "height": height,
                        "pssh_p": psshBox(pssh),
                        "pssh": pssh,
                        "init_headers_range": init_headers_range,
                        "language": language,
                        "codec": codec,
                        "profile": profile,
                        "baseurl": baseurl,
                        "dash_information": dash_information,
                        "buffertime": self.mpd.buffertime,
                        "duration": self.mpd.duration,
                        "contenttype": contenttype,
                        "id": index,
                        "download_type": download_type,
                    }]
        #print(tracks)
        return tracks


