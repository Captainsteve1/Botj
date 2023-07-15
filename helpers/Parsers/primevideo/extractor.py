import json
import logging
import os
import re
import urllib.parse

import requests
import untangle
from configs.config import wvripper_config
from helpers.Parsers.primevideo.utils import (_language_fixer,
                                              mpd_duration_extractor,
                                              profile_detector)
from helpers.Utils.ripprocess import ripprocess
from helpers.wvtracks import wvtracks


class extractor:
    def __init__(self):
        """CLASS FOR AMZN MPD PARSING"""
        self.logger = logging.getLogger(__name__)
        self.ripprocess = ripprocess()
        self.urnpssh = "urn:uuid:EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED"


    @staticmethod
    def clean_mpd(xml_input):
        xml_input = re.sub(rf"(<SegmentDurations.+?/SegmentDurations>)", "", xml_input, flags=re.S)
        xml_input = re.sub(r"(<SegmentList.+?/><SegmentURL mediaRange=\"[0-9]+-([0-9]+)\"/></SegmentList>)", r"<size>\2</size>", xml_input, flags=re.S)
        return xml_input

    def mpd_downloader(self, mpd_url, mpd_filename):
        xml_input = requests.get(mpd_url).text
        # with open(mpd_filename, "wb") as mpdfile:
        #     mpdfile.write(xml_input)
        return untangle.parse(self.clean_mpd(xml_input))

    def PlayBacksExtractor(self, playbacks, wvtracks):
        self.wvtracks = wvtracks

        for playback in playbacks:
            audio_only = playback.get("audio_only")
            mpd_url = playback.get("manifest").get("manifest_full")
            mpd_filename = "{} {}-{}.mpd".format(playback.get("profile"), playback.get("manifest").get("cdn"), playback.get("client"))
            default_audio = _language_fixer(playback.get("default_audio")) if playback.get("default_audio") else None

            print(f"Parsing {mpd_filename}")

            mpd_data = self.mpd_downloader(mpd_url, mpd_filename)
            duration = mpd_duration_extractor(mpd_data)
            wvstream = True
            videopssh, audiopssh = None, None

            Extras = {
                "profile": playback.get("profile"),
                "client": playback.get("client"),
                "cert": playback.get("cert"),
                "region": playback.get("region"),
                "license_url": playback.get("license_url"),
                "license_headers": playback.get("license_headers"),
            }

            for content in mpd_data.MPD.Period.AdaptationSet:
                if content["group"] == "2" and audio_only is not True:
                    for videocontent in content.ContentProtection:
                        if videocontent["schemeIdUri"] == self.urnpssh:
                            videopssh = videocontent.cenc_pssh.cdata
                            for videourls in content.Representation:
                                DownloadType = "URL"
                                Type = "CONTENT"
                                PSSH = videopssh
                                Size = int(videourls.size.cdata)
                                # Size = int(
                                #     videourls.SegmentList.SegmentURL[-1][
                                #         "mediaRange"
                                #     ].split("-")[1]
                                # )
                                Url = "{}/{}".format(
                                    mpd_url.rsplit("/", 1)[0], videourls.BaseURL.cdata,
                                )
                                Codec = videourls["codecs"]
                                Profile = profile_detector(Codec)
                                Drm = True
                                FrameRate = round(eval(videourls["frameRate"]), 3)
                                Height = int(videourls["height"])
                                Width = int(videourls["width"])
                                Bitrate = (
                                    int(float(((Size / duration) * 8) / 1000))
                                    if duration
                                    else int(int(videourls["bandwidth"]) / 1000)
                                )

                                self.wvtracks.add_video(
                                    DownloadType=DownloadType,
                                    Type=Type,
                                    Url=Url,
                                    Size=Size,
                                    Codec=Codec,
                                    Profile=Profile,
                                    Drm=Drm,
                                    PSSH=PSSH,
                                    Extras=Extras,
                                    FrameRate=FrameRate,
                                    Height=Height,
                                    Width=Width,
                                    Bitrate=Bitrate,
                                )

                if content["group"] == "1":
                    try:
                        Type = "DESCRIPTIVE" if "descriptive" in content["audioTrackId"].lower() else "DIALOG"
                        Name, Language = self.ripprocess.countrycode(content["audioTrackId"].lower().split("_")[0])
                        Language = _language_fixer(content["audioTrackId"])
                    except Exception:
                        try:
                            Type = "DESCRIPTIVE" if "descriptive" in content["lang"].lower() else "DIALOG"
                            Name, Language = self.ripprocess.countrycode(content["lang"].lower().split("_")[0])
                            Language = _language_fixer(content["lang"])
                        except Exception:
                            Type = "DIALOG"
                            Name = "English"
                            Language = "en"

                    if Language == "es":
                        Name = "European Spanish"

                    try:
                        for audiocontent in content.ContentProtection:
                            if audiocontent["schemeIdUri"] == self.urnpssh and audiocontent.cenc_pssh.cdata != videopssh:
                                audiopssh = audiocontent.cenc_pssh.cdata
                                for audiourls in content.Representation:
                                    DownloadType = "URL"
                                    Original =True if Language == default_audio else False
                                    PSSH = audiopssh
                                    Size = int(audiourls.size.cdata)
                                    # Size = int(
                                    #     audiourls.SegmentList.SegmentURL[-1][
                                    #         "mediaRange"
                                    #     ].split("-")[1]
                                    # )
                                    Url = "{}/{}".format(
                                        mpd_url.rsplit("/", 1)[0], audiourls.BaseURL.cdata,
                                    )

                                    Codec = audiourls["codecs"]
                                    Profile = profile_detector(Codec)
                                    Drm = True
                                    Bitrate = int(int(audiourls["bandwidth"]) / 1000)

                                    self.wvtracks.add_audio(
                                        DownloadType=DownloadType,
                                        Type=Type,
                                        Url=Url,
                                        Size=Size,
                                        Codec=Codec,
                                        PSSH=PSSH,
                                        Profile=Profile,
                                        Drm=Drm,
                                        Extras=Extras,
                                        Original=Original,
                                        Language=Language,
                                        Name=Name,
                                        Bitrate=Bitrate,
                                    )

                                wvstream = False

                            if audiocontent["schemeIdUri"] == self.urnpssh and audiocontent.cenc_pssh.cdata == videopssh and wvstream:
                                audiopssh = audiocontent.cenc_pssh.cdata
                                for audiourls in content.Representation:
                                    DownloadType = "URL"
                                    Original =True if Language == default_audio else False
                                    PSSH = audiopssh
                                    # Size = int(
                                    #     audiourls.SegmentList.SegmentURL[-1][
                                    #         "mediaRange"
                                    #     ].split("-")[1]
                                    # )
                                    Size = int(audiourls.size.cdata)
                                    Url = "{}/{}".format(
                                        mpd_url.rsplit("/", 1)[0], audiourls.BaseURL.cdata,
                                    )

                                    Codec = audiourls["codecs"]
                                    Profile = profile_detector(Codec)
                                    Drm = True
                                    Bitrate = int(int(audiourls["bandwidth"]) / 1000)

                                    self.wvtracks.add_audio(
                                        DownloadType=DownloadType,
                                        Type=Type,
                                        Url=Url,
                                        Size=Size,
                                        Codec=Codec,
                                        PSSH=PSSH,
                                        Profile=Profile,
                                        Drm=Drm,
                                        Extras=Extras,
                                        Original=Original,
                                        Language=Language,
                                        Name=Name,
                                        Bitrate=Bitrate,
                                    )

                    except AttributeError:
                        for audiourls in content.Representation:
                            DownloadType = "URL"
                            Original = True if Language == default_audio else False

                            PSSH = None
                            Size = int(audiourls.size.cdata)
                            # Size = int(
                            #     audiourls.SegmentList.SegmentURL[-1]["mediaRange"].split(
                            #         "-"
                            #     )[1]
                            # )
                            Url = "{}/{}".format(
                                mpd_url.rsplit("/", 1)[0], audiourls.BaseURL.cdata,
                            )

                            Codec = audiourls["codecs"]
                            Profile = profile_detector(Codec)
                            Drm = False
                            Bitrate = int(int(audiourls["bandwidth"]) / 1000)

                            self.wvtracks.add_audio(
                                DownloadType=DownloadType,
                                Type=Type,
                                Url=Url,
                                Size=Size,
                                Codec=Codec,
                                Profile=Profile,
                                PSSH=PSSH,
                                Drm=Drm,
                                Extras=Extras,
                                Original=Original,
                                Language=Language,
                                Name=Name,
                                Bitrate=Bitrate,
                            )

        for track in playbacks[0]["subtitles"]["normal"]:
            languageCode = track.get("timedTextTrackId") if track.get("timedTextTrackId") else track.get("languageCode")
            Name, Language = self.ripprocess.countrycode(languageCode.lower().split("_")[0])
            Language = _language_fixer(languageCode)
            if Language == "es":
                Name = "European Spanish"
            DownloadType = "URL"
            Type = "SDH" if "_sdh" in languageCode else "SUBTITLE"
            Codec = "TTMLv2"
            Profile = profile_detector(Codec)
            Url = self.ripprocess.replaceExtentsion(track["url"], "srt")
            self.wvtracks.add_subtitle(
                DownloadType=DownloadType,
                Type=Type,
                Url=Url,
                Codec=Codec,
                Extras=Extras,
                Profile=Profile,
                Language=Language,
                Name=Name,
            )

        for track in playbacks[0]["subtitles"]["forced"]:
            languageCode = track.get("timedTextTrackId") if track.get("timedTextTrackId") else track.get("languageCode")
            Name, Language = self.ripprocess.countrycode(languageCode.lower().split("_")[0])
            Language = _language_fixer(languageCode)
            if Language == "es":
                Name = "European Spanish"
            DownloadType = "URL"
            Type = "FORCED"
            Codec = "TTMLv2"
            Profile = profile_detector(Codec)
            Url = self.ripprocess.replaceExtentsion(track["url"], "srt")
            self.wvtracks.add_subtitle(
                DownloadType=DownloadType,
                Type=Type,
                Url=Url,
                Codec=Codec,
                Extras=Extras,
                Profile=Profile,
                Language=Language,
                Name=Name,
            )

        return self.wvtracks
