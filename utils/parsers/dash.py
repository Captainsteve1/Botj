import json
import os
import re
from typing import Any, Dict, List, NamedTuple, Optional, Union
from uuid import uuid4

import requests
import xmltodict

from .utils import (dict_to_list, extract_baseurl, extract_pssh_box, joinurls,
                    profile_codec_parser, to_seconds)


class MPD:
    BASEURL: str = None
    MPDBASEURL: str = None
    MEDIAPRESENTATIONDURATION: int = None
    PERIOD_DURATION: int = None
    MINBUFFERTIME: int = None
    ADAPTATIONSET: List[Dict[str, Any]] = None
    WIDEVINE_URN: str = "URN:UUID:EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED"
    KNOWN_TRACKS_TYPES: List[str] = ["AUDIO", "VIDEO", "TEXT", "APPLICATION"]

class xml2dict:
    def __init__(self):
        ...

    def get_download_type(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        # TODO: sometimes adaptationset does not have contentType or mimeType
        # so i gotta check adaptationset tracks if it videos or audios or anything
        # this issue was found on viki mpd that does not have pssh as well
        content_type = adaptationset.get("@contentType") if adaptationset.get("@contentType") else adaptationset.get("@mimeType").split("/")[0]
        if content_type.lower() in ["text", "application"]: content_type = "timedtext"
        return content_type

    def get_codec(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        codecs = adaptationset.get("@codecs") if adaptationset.get("@codecs") else track_data.get("@codecs")
        return codecs

    def get_profile(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        codecs = adaptationset.get("@codecs") if adaptationset.get("@codecs") else track_data.get("@codecs")
        return profile_codec_parser(codecs)

    def get_framerate(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> Union[str, float]:
        frameRate = adaptationset.get("@frameRate") if adaptationset.get("@frameRate") else track_data.get("@frameRate")
        try:
            return round(eval(frameRate), 3)
        except Exception:
            return frameRate

    def detect_atmos(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> bool:
        if "DolbyDigitalPlusExtensionType" in str(track_data) or "DolbyDigitalPlusExtensionType" in str(adaptationset):
            return True
        return False

    def get_size(self, bitrate: int) -> int:
        PERIOD_DURATION = self.MPD.PERIOD_DURATION if self.MPD.PERIOD_DURATION else 0
        if int(PERIOD_DURATION) == 0:
            if not self.MPD.MEDIAPRESENTATIONDURATION:
                return None
            PERIOD_DURATION = self.MPD.MEDIAPRESENTATIONDURATION

        size = (bitrate * PERIOD_DURATION) / 8 * 1000
        return size

    def get_bitrate(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> int:
        bitrate = adaptationset.get("@bandwidth") if adaptationset.get("@bandwidth") else track_data.get("@bandwidth")
        PERIOD_DURATION = self.MPD.PERIOD_DURATION if self.MPD.PERIOD_DURATION else 0
        MEDIAPRESENTATIONDURATION = self.MPD.MEDIAPRESENTATIONDURATION

        _bitrate = float(bitrate)

        if int(PERIOD_DURATION) == 0:
            if not MEDIAPRESENTATIONDURATION:
                return int(float(_bitrate / 1000))
            PERIOD_DURATION = MEDIAPRESENTATIONDURATION

        _bitrate = int(float((PERIOD_DURATION * _bitrate + PERIOD_DURATION * _bitrate) / (PERIOD_DURATION + PERIOD_DURATION) / 1000))
        return _bitrate

    def get_width(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> int:
        width = adaptationset.get("@width") if adaptationset.get("@width") else track_data.get("@width")
        return int(width) if width else None

    def get_height(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> int:
        height = adaptationset.get("@height") if adaptationset.get("@height") else track_data.get("@height")
        return int(height) if height else None

    def get_language(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        language = adaptationset.get("@lang") if adaptationset.get("@lang") else track_data.get("@lang")
        return language

    def get_channels(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> float:
        if not (channels := track_data.get(
            "AudioChannelConfiguration", {}).get("@value")): channels = adaptationset.get(
            "AudioChannelConfiguration", {}).get("@value")

        try:
            channels = str(channels).replace("F801", "5.1").replace("A000", "2")
            channels = float(channels)
        except ValueError:
            pass

        if isinstance(channels, float):
            if channels > 2.0: channels = 5.1

        return channels

    def get_protocol_type(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        if track_data.get("BaseURL"): return "http"
        return "dash"

    def get_url(self, baseurl: str, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        if (url := track_data.get("BaseURL")):
            return url if url.startswith("http") else joinurls(baseurl, url)
        return None

    def get_track_id(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        id = adaptationset.get("@id") if adaptationset.get("@id") else track_data.get("@id")
        return id

    def get_extras(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        return {"track_data": track_data, "adaptationset": adaptationset}

    def get_pssh(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> str:
        pssh = None
        contentprotection = track_data.get("ContentProtection") if track_data.get("ContentProtection") else adaptationset.get("ContentProtection")
        if contentprotection:
            for protection in dict_to_list(contentprotection):
                if protection.get("@schemeIdUri").upper() == self.MPD.WIDEVINE_URN:
                    if not (pssh := protection.get("cenc:pssh")):
                        pssh = protection.get("pssh")
                    if isinstance(pssh, str):
                        return pssh
                    if isinstance(pssh, dict):
                        return pssh.get("#text")
        return pssh

    def get_segments(
        self,
        track_data: Dict[str, Any],
        adaptationset: Dict[str, Any],
        baseurl: str,
        underscore_convertor: Optional[bool] = False
    ) -> str:
        if self.get_protocol_type(track_data, adaptationset) == "dash":
            segmenttemplate = adaptationset.get("SegmentTemplate") if adaptationset.get("SegmentTemplate") else track_data.get("SegmentTemplate")
            if not segmenttemplate:
                raise ValueError("Couldn't find a SegmentTemplate for a Representation")

            id = track_data.get("@id").replace("/", "_") if underscore_convertor else track_data.get("@id")
            init = segmenttemplate.get("@initialization")
            media = segmenttemplate.get("@media")
            start_number = int(segmenttemplate.get("@startNumber", 0))
            segments = []

            if (timeline := segmenttemplate.get("SegmentTimeline")):
                _last_time_offset = 0

                segments.append(joinurls(baseurl, init.replace("$RepresentationID$", id)))

                for s in dict_to_list(timeline.get("S")):
                    for _ in range(int(s.get("@r")) + 1 if s.get("@r") else 1):
                        url = media
                        if "$RepresentationID$" in url:
                            url = url.replace("$RepresentationID$", id)
                        if "$Number$" in url:
                            url = url.replace("$Number$", str(start_number))
                            start_number += 1
                        if "$Time$" in url:
                            url = url.replace("$Time$", str(_last_time_offset))
                            _last_time_offset += int(s["@d"])
                        segments.append(joinurls(baseurl, url))
                return segments
            interval_duration = float(int(segmenttemplate.get("@duration")) / int(segmenttemplate.get("@timescale")))
            if not (PERIOD_DURATION := self.MPD.PERIOD_DURATION):
                PERIOD_DURATION = self.MPD.MEDIAPRESENTATIONDURATION
            repeat = int(round(PERIOD_DURATION / interval_duration))

            segments.append(joinurls(baseurl, init.replace("$RepresentationID$", id)))

            for number in range(start_number, repeat + start_number):
                url = media
                if "$RepresentationID$" in url:
                    url = url.replace("$RepresentationID$", id)
                if "$Number$" in url:
                    url = url.replace("$Number$", str(number))
                segments.append(joinurls(baseurl, url))
            return segments

        return []

class pympd(xml2dict):
    def __init__(self, content: str, headers: Dict[str, Any] = {}):
        self.MPD = MPD
        self.content = content
        self.session = requests.Session()
        self.headers = headers
        self.youtubedl_data = None
        self.data = self.extract_mpd(self.content)
        self.MPD.ADAPTATIONSET = self.get_adaptationsets(self.data)
        self.parse_mpd_data()
        xml2dict.__init__(self)

    def extract_mpd(self, data: str) -> Dict[str, Any]:
        if isinstance(data, dict) and data.get("MPD"):
            return data
        if isinstance(data, str) and data.startswith("http"):
            return json.loads(json.dumps(xmltodict.parse(self.session.get(data, headers=self.headers).text)))
        if isinstance(data, str) and os.path.isfile(data):
            return json.loads(json.dumps(xmltodict.parse(open(data, "r").read())))
        if isinstance(data, str) and data.__contains__("Representation"):
            return json.loads(json.dumps(xmltodict.parse(data)))
        return None

    def set_adaptationsets_content_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if (content_type := data.get("@contentType")):
            content_type = content_type.split("/")[0].upper()
            data |= {"@contentType": str(content_type)}
            return data

        if (content_type := data.get("@mimeType")):
            content_type = content_type.split("/")[0].upper()
            data |= {"@contentType": str(content_type)}
            return data

        if re.search(r"video/mp4|video|avc|hvc", str(data)):
            content_type = "VIDEO"
        if re.search(r"audio/mp4|audio|mp4a|ec3|e-c3", str(data)):
            content_type = "AUDIO"
        if re.search(r"subtitle|timedtext|vtt|srt|ttml", str(data)):
            content_type = "TEXT"

        data |= {"@contentType": str(content_type)}
        return data

    def get_adaptationsets(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        periods = dict_to_list(data["MPD"]["Period"])
        for i, period in enumerate(periods):
            periods[i]["AdaptationSets"] = dict_to_list(period["AdaptationSet"])
            del periods[i]["AdaptationSet"]
            for ii, adaptation_set in enumerate(period["AdaptationSets"]):
                periods[i]["AdaptationSets"][ii]["Representations"] = dict_to_list(adaptation_set["Representation"])
                del periods[i]["AdaptationSets"][ii]["Representation"]

        return [adaptationsets for adaptationsets in [self.set_adaptationsets_content_type(ad) for ad in period["AdaptationSets"]] if (
            contenttype := adaptationsets.get("@contentType") if adaptationsets.get(
                "@contentType") else adaptationsets.get("@mimeType"
                ).split("/")[0]).upper() in self.MPD.KNOWN_TRACKS_TYPES]

    def parse_mpd_data(self) -> None:
        if (MEDIAPRESENTATIONDURATION := self.data.get("MPD", {}).get("@mediaPresentationDuration")):
            self.MPD.MEDIAPRESENTATIONDURATION = to_seconds(MEDIAPRESENTATIONDURATION)
        if (MINBUFFERTIME := self.data.get("MPD", {}).get("@minBufferTime")):
            self.MPD.MINBUFFERTIME = to_seconds(MINBUFFERTIME)
        if (PERIOD_DURATION := self.data.get("MPD", {}).get("Period", {}).get("@duration")):
            self.MPD.PERIOD_DURATION = to_seconds(PERIOD_DURATION)
        if isinstance(self.content, str) and self.content.startswith("http"):
            self.MPD.BASEURL = extract_baseurl(self.content)
        if self.data.get("MPD").get("BaseURL"):
            self.MPD.MPDBASEURL = self.data.get("MPD").get("BaseURL")
        return

    def get_tracks_by_type(self, _type: Union[str, List[str]]) -> List[Dict[str, Any]]:
        _type = [_type] if isinstance(_type, str) else _type
        return [adaptationset for adaptationset in self.MPD.ADAPTATIONSET if self.get_download_type(None, adaptationset) in _type]

    def get_youtubedl_segments(self, track_data: Dict[str, Any], adaptationset: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(self.content, str) and self.content.startswith("http") and self.get_protocol_type(track_data, adaptationset) == "dash":
            if not self.youtubedl_data: self.youtubedl_data = youtube_dl_parser(url=self.content, headers=self.headers, output=(_ := re.sub("-", "", str(uuid4()))))
            format_id = self.get_track_id(track_data, adaptationset)
            return [joinurls(track["fragment_base_url"], fragment["path"]) for track in self.youtubedl_data["formats"] if re.sub("/", "_", track["format_id"]) == re.sub("/", "_", format_id) for fragment in track["fragments"]]
        return []

    def tracks(
        self,
        baseurl: str = None,
        youtubedl_extractor: Optional[bool] = False,
        underscore_convertor: Optional[bool] = False,
    ) -> List[Dict[str, Any]]:
        if not baseurl: baseurl = self.MPD.BASEURL or self.MPD.MPDBASEURL
        assert baseurl != None
        return [{
            "protocol" : self.get_protocol_type(track_data, adaptationset),
            "download_type" : self.get_download_type(track_data, adaptationset).lower(),
            "codec" : self.get_codec(track_data, adaptationset),
            "profile" : self.get_profile(track_data, adaptationset),
            "framerate" : self.get_framerate(track_data, adaptationset),
            "atmos_track" : self.detect_atmos(track_data, adaptationset),
            "size" : self.get_size(self.get_bitrate(track_data, adaptationset)),
            "bitrate" : self.get_bitrate(track_data, adaptationset),
            "width" : self.get_width(track_data, adaptationset),
            "height" : self.get_height(track_data, adaptationset),
            "language" : self.get_language(track_data, adaptationset),
            "channels" : self.get_channels(track_data, adaptationset),
            "url" : self.get_url(baseurl, track_data, adaptationset),
            "segments" : self.get_segments(track_data, adaptationset, baseurl=baseurl, underscore_convertor=underscore_convertor),
            "raw_pssh" : self.get_pssh(track_data, adaptationset),
            "pssh" : extract_pssh_box(self.get_pssh(track_data, adaptationset)),
            "extras" : self.get_extras(track_data, adaptationset),
            "content_type" : {"timedtext": "normal", "audio": "dialog", "video": "content"}[self.get_download_type(track_data, adaptationset).lower()],
            "youtubedl_segments" : self.get_youtubedl_segments(track_data, adaptationset) if youtubedl_extractor else [],
            "track_id" : self.get_track_id(track_data, adaptationset),
            "track_number" : track_number
        } for adaptationset in self.MPD.ADAPTATIONSET for track_number, track_data in enumerate(adaptationset.get("Representations"), start=1)]
