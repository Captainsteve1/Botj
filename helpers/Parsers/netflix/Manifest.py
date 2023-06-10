import json
import logging
import os, base64
import re
from pprint import pprint

from configs.config import wvripper_config
from helpers.Parsers.netflix.MSLClient import MSLClient
from helpers.Parsers.netflix.Profiles import Profiles
from helpers.Utils.ripprocess import ripprocess
from helpers.wvtracks import wvtracks
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt


class Manifest:
    def __init__(
        self,
        netflixId=None,
        video_profile="M/HPL",
        audio_profile="ATMOS",
        resolution=1080,
    ):
        self.logger = logging.getLogger(__name__)
        self.netflixId = netflixId
        self.video_profile = video_profile
        self.audio_profile = audio_profile
        self.resolution = resolution
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.SERVICE = self.config.SERVICES.NETFLIX
        self.ripprocess = ripprocess()
        self.Profiles = Profiles()
        self.PSSH_LIST = []
        #________________________
        self.clientMAIN = None
        self.clientHIGH = None
        self.clientHEVC = None
        self.clientHDR = None
        self.clientDV5 = None
        self.clientVP9 = None
        #________________________
        self.responsetMAIN = None
        self.responsetHIGH = None
        self.responsetHEVC = None
        self.responsetHDR = None
        self.responsetDV5 = None
        self.responsetVP9 = None

    def set_clients(self, profile, client, response):

        if profile == "MAIN":
            self.clientMAIN = client
            self.responsetMAIN = response
        elif profile == "HIGH":
            self.clientHIGH = client
            self.responsetHIGH = response
        elif profile == "HEVC":
            self.clientHEVC = client
            self.responsetHEVC = response
        elif profile == "HDR":
            self.clientHDR = client
            self.responsetHDR = response
        elif profile == "DOLBY_VISION":
            self.clientDV5 = client
            self.responsetDV5 = response
        elif profile == "VP9":
            self.clientVP9 = client
            self.responsetVP9 = response

        return 

    def get_pssh_from_response(self, response):
        if response is None:
            self.logger.info("Wrong response...")
            exit(-1)

        return response["result"]["video_tracks"][0]["drmHeader"]["bytes"]

    def get_client(self, profile):
        if profile == "MAIN":
            return self.clientMAIN, self.get_pssh_from_response(self.responsetMAIN)
        elif profile == "HIGH":
            return self.clientHIGH, self.get_pssh_from_response(self.responsetHIGH)
        elif profile == "HEVC":
            return self.clientHEVC, self.get_pssh_from_response(self.responsetHEVC)
        elif profile == "HDR":
            return self.clientHDR, self.get_pssh_from_response(self.responsetHDR)
        elif profile == "DOLBY_VISION":
            return self.clientDV5, self.get_pssh_from_response(self.responsetDV5)
        elif profile == "VP9":
            return self.clientVP9, self.get_pssh_from_response(self.responsetVP9)
        else:
            raise ValueError(f"NO CLIENT FOR THIS PROFILE: {profile}")

        return None, None

    def check_video_profile(self, video_profile):
        if video_profile == "MAIN" and self.clientMAIN is None:
            return False
        elif video_profile == "HIGH" and self.clientHIGH is None:
            return False
        elif video_profile == "HEVC" and self.clientHEVC is None:
            return False
        elif video_profile == "HDR" and self.clientHDR is None:
            return False
        elif video_profile == "DOLBY_VISION" and self.clientDV5 is None:
            return False
        elif video_profile == "VP9" and self.clientVP9 is None:
            return False

        return True

    def get_keys(self, netflixId, video_profile, PSSH):
        if not netflixId == self.netflixId:
            self.logger.info(f"\nWrong ID: {netflixId}...")
            return []

        if self.check_video_profile(video_profile) is False:
            self.logger.info(f"\nWrong PROFILE: {video_profile}...")
            return []

        self.logger.info(f"\nGetting {video_profile}...")

        # if video_profile == "MAIN":
        #     self.logger.info(f"\nUsing sd PSSH")
        #     PSSH = sorted(self.PSSH_LIST, key=lambda k: int(k["Height"]))[0]["Pssh"]

        license_client, init_data_b64 = self.get_client(video_profile)

        wvdecrypt = WvDecrypt(
            init_data_b64=PSSH,
            cert_data_b64=None,
            device=self.config.DEVICES.NETFLIX,
        )
        challenge = wvdecrypt.get_challenge()
        data = license_client.get_license(challenge)
        license_b64 = data["result"][0]["licenseResponseBase64"]
        wvdecrypt.update_license(license_b64)
        _, keyswvdecrypt = wvdecrypt.start_process()
        KEYS = keyswvdecrypt

        return KEYS

    def MSL(self):
        device = self.config.DEVICES.NETFLIX
        save_rsa_location = self.SERVICE.token_file
        languages = self.SERVICE.manifest_language
        email = self.SERVICE.email
        password = self.SERVICE.password
        esn = self.SERVICE.androidesn

        return {
            "device": device,
            "save_rsa_location": save_rsa_location,
            "languages": languages,
            "email": email,
            "password": password,
            "esn": esn,
            "wv_keyexchange": True,
            "proxies": None,
            "profiles": [],
        }

    def get_by_resolution(self, profile):

        if self.resolution >= 1080:
            return self.Profiles.get(profile=profile, resolution="FHD")
        elif self.resolution < 1080 and self.resolution >= 720:
            return self.Profiles.get(profile=profile, resolution="HD")
        elif self.resolution < 720:
            return self.Profiles.get(profile=profile, resolution="SD")

        return None

    def get_audio_profiles(self):
        if not self.audio_profile.upper() in self.Profiles.AUDIO:
            raise ValueError("Unknown profile: {}".format(self.audio_profile.upper()))

        return self.Profiles.AUDIO[self.audio_profile.upper()]

    def get_profile_playbacks(self, profile, profiles):
        self.logger.info(f"Getting {profile} Profile Manifest...")

        MSL = self.MSL()
        MSL.update({"profiles": list(set(profiles))})

        extra_params = dict()

        if profile != "MAIN":
            extra_params["showAllSubDubTracks"] = True

        client = MSLClient(MSL)

        try:
            response = client.load_playlist(int(self.netflixId), extra_params=extra_params)
            self.logger.debug("Manifest resp: {}".format(response))
            self.set_clients(profile, client, response)
            return response["result"]
        except Exception as e:
            self.ReportManifestError(e, profile)
            return None

        return None

    def ReportManifestError(self, Error, profile):
        if "This title is not available to watch instantly" in str(Error):
            self.logger.info("This item does not have {} Manifest.".format(profile))
            return

        self.logger.info("Error: {}".format(Error))

        return

    def get_netflix_profile_name(self, profile):
        _h264_re = re.compile("^playready-h264")
        _h265_re = re.compile("^hevc-main")
        _vp9_re = re.compile("^vp9-")
        _hdr10_re = re.compile("hevc-hdr-main")
        _dv5_re = re.compile("-dv5-")
        _dd_re = re.compile("^dd-")
        _ddp_re = re.compile("^ddplus-")
        _aac_re = re.compile("^heaac-")
        _webvtt_re = re.compile("^webvtt-")
        _ttml_re = re.compile("^(dfxp|simplesdh)")

        if _h264_re.search(profile):
            return "AVC"
        elif _hdr10_re.search(profile):
            return "HDR"
        elif _h265_re.search(profile):
            return "HEVC"
        elif _vp9_re.search(profile):
            return "VP9"
        elif _dv5_re.search(profile):
            return "DOLBY_VISION"
        elif _webvtt_re.search(profile):
            return "WEBVTT"
        elif _ttml_re.search(profile):
            return "DFXP"
        elif _dd_re.search(profile):
            return "AC3"
        elif _ttml_re.search(profile):
            return "DFXP"
        elif _ddp_re.search(profile):
            return "EAC3"
        elif _aac_re.search(profile):
            return "AAC"

        return profile

    def drmHeaderId(self, drmHeaderId):
        array_of_bytes = bytearray(b"\x00\x00\x002pssh\x00\x00\x00\x00")
        array_of_bytes.extend(bytes.fromhex("edef8ba979d64acea3c827dcd51d21ed"))
        array_of_bytes.extend(b"\x00\x00\x00\x12\x12\x10")
        array_of_bytes.extend(bytes.fromhex(drmHeaderId.replace("-", "")))
        pssh = base64.b64encode(bytes.fromhex(array_of_bytes.hex()))
        return pssh.decode()

    def getPlayback(self,):
        """get playback for multi manifest, sorted."""

        self.wvtracks = wvtracks()

        collected_tracks = []

        PROFILES = [self.video_profile]

        if self.video_profile == "M/HPL":
            PROFILES = ["MAIN", "HIGH"]

        for PROFILE in PROFILES:
            results = self.get_profile_playbacks(
                PROFILE,
                self.Profiles.BASE
                + self.get_by_resolution(PROFILE)
                + self.get_audio_profiles(),
            )

            # HEVC FALLBACK TO DO PROFILES...

            if not results and PROFILE == "HEVC":
                self.logger.info(f"Trying HEVC DO PROFILES...")
                results = self.get_profile_playbacks(
                    PROFILE,
                    self.Profiles.BASE
                    + self.Profiles.add_do(self.get_by_resolution(PROFILE))
                    + self.get_audio_profiles(),
                )

            # Video Parsing...

            if not results:
                continue

            for video_track in results["video_tracks"]:
                for downloadable in video_track["streams"]:
                    isDecryptable = True

                    if downloadable.get("content_profile") == "playready-h264hpl40-dash":
                        if not "SEGMENT_MAP_2KEY" in downloadable.get("tags"):
                            print("Detected (Undecryptable Profile (Chrome is the way)) -> {} | {}kbps".format(downloadable.get("content_profile"), downloadable.get("bitrate")))
                            # isDecryptable = False

                    DownloadType = "URL"
                    Type = "CONTENT"
                    Size = int(float(downloadable["size"]))
                    Url = downloadable["urls"][0]["url"]
                    Codec = downloadable["content_profile"]
                    Profile = self.get_netflix_profile_name(Codec)
                    Drm = downloadable["isDrm"]
                    FrameRate = downloadable["framerate_value"]
                    Height = downloadable["res_h"]
                    Width = downloadable["res_w"]
                    Bitrate = downloadable["bitrate"]
                    PSSH = self.drmHeaderId(downloadable["drmHeaderId"])
                    self.PSSH_LIST.append({"Pssh": PSSH, "Height": int(Height)})

                    collected_tracks.append(
                        {
                            "Height": Height,
                            "Width": Width,
                            "Profile": Profile,
                            "Codec": Codec,
                            "Bitrate": "{}".format(Bitrate),
                            "Size": "{}".format(f"{int(float(Size))/1048576:0.2f} MiB" if int(float(Size)) < 1073741824 else f"{int(float(Size))/1073741824:0.2f} GiB"),
                            "isDecryptable": isDecryptable
                        }
                    )

                    if isDecryptable:
                        self.wvtracks.add_video(
                            DownloadType=DownloadType,
                            Type=Type,
                            Url=Url,
                            Size=Size,
                            Codec=Codec,
                            PSSH=PSSH,
                            Extras={"NFProfile": PROFILE},
                            Profile=Profile,
                            Drm=Drm,
                            FrameRate=FrameRate,
                            Height=Height,
                            Width=Width,
                            Bitrate=Bitrate,
                        )

            # Audio Parsing...

            for audio_track in results["audio_tracks"]:
                DownloadType = "URL"
                Type = (
                    "DESCRIPTIVE"
                    if "audio description" in audio_track["languageDescription"].lower()
                    else "DIALOG"
                )
                Original = self.isOriginal(audio_track["languageDescription"])
                Name, Language = self.ripprocess.countrycode(audio_track["language"])
                Name = self.noOriginal(audio_track["languageDescription"])
                for downloadable in audio_track["streams"]:
                    Url = downloadable["urls"][0]["url"]
                    Size = int(float(downloadable["size"]))
                    Codec = downloadable["content_profile"]
                    Profile = self.get_netflix_profile_name(Codec)
                    Drm = downloadable["isDrm"]
                    Channels = downloadable["channels"]
                    Bitrate = downloadable["bitrate"]

                    self.wvtracks.add_audio(
                        DownloadType=DownloadType,
                        Type=Type,
                        Url=Url,
                        Size=Size,
                        Codec=Codec,
                        Profile=Profile,
                        Drm=Drm,
                        Original=Original,
                        Channels=Channels,
                        Language=Language,
                        Name=Name,
                        Bitrate=Bitrate,
                    )

            # Subtitle Parsing...

            for text_track in results["timedtexttracks"]:
                if text_track["language"] == "none" or text_track["language"] is None:
                    continue

                DownloadType = "URL"
                Type = (
                    "SUBTITLE"
                    if text_track["languageDescription"] != "Off"
                    else "FORCED"
                )
                if text_track["rawTrackType"].lower() == "closedcaptions":
                    Type = "CC"
                Name, Language = self.ripprocess.countrycode(text_track["language"])
                if not Type == "FORCED":
                    Name = text_track["languageDescription"]
                Codec = "webvtt-lssdh-ios8"
                Profile = self.get_netflix_profile_name(Codec)
                Url = next(
                    iter(
                        text_track["ttDownloadables"]["webvtt-lssdh-ios8"][
                            "downloadUrls"
                        ].values()
                    )
                )

                self.wvtracks.add_subtitle(
                    DownloadType=DownloadType,
                    Type=Type,
                    Url=Url,
                    Codec=Codec,
                    Profile=Profile,
                    Language=Language,
                    Name=Name,
                )

        if not collected_tracks == []:
            collected_tracks = sorted(collected_tracks, key=lambda k: (int(k["Bitrate"]), int(k["Height"])))
            hpa = collected_tracks[-1]
            print("\nHighest Profile -> {} | {}kbps | {} | isDecryptable: {}".format(hpa.get("Codec"), hpa.get("Bitrate"), hpa.get("Size"), hpa.get("isDecryptable")))

        return self.wvtracks.filtering(video_order=self.resolution)

    def isOriginal(self, language_text):

        if "Original".lower() in language_text.lower():
            return True

        brackets = re.search(r"\[(.*)\]", language_text)
        if brackets:
            return True

        return False

    def noOriginal(self, language_text):
        language_text = re.sub(" - Audio Description", "", language_text)
        brackets = re.search(r"\[(.*)\]", language_text)
        if brackets:
            return language_text.replace(brackets[0], "").strip()

        return language_text
