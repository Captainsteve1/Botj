import json
import logging
import os
import time

from configs.config import wvripper_config
from helpers.Parsers.netflix.MSLClient import MSLClient
from helpers.Parsers.netflix.Profiles import Profiles
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt


class License:
    def __init__(self, netflixId, profile):
        self.logger = logging.getLogger(__name__)
        self.netflixId = netflixId
        self.profile = profile
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.SERVICE = self.config.SERVICES.NETFLIX
        self.Profiles = Profiles()

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

    def check_response(self, response):
        response = str(response)
        if self.profile == "MAIN":
            if (
                not "playready-h264mpl" in response
                and "playready-h264bpl" not in response
            ):
                self.logger.info(
                    "This item does not have {} Manifest".format(self.profile)
                )
                return False
        elif self.profile == "HIGH":
            if not "playready-h264hpl" in response:
                self.logger.info(
                    "This item does not have {} Manifest".format(self.profile)
                )
                return False
        elif self.profile == "VP9 KEYS":
            if not "vp9-profile" in response:
                self.logger.info(
                    "This item does not have {} Manifest".format(self.profile)
                )
                return False
        elif self.profile == "HEVC":
            if not "hevc-main" in response:
                self.logger.info(
                    "This item does not have {} Manifest".format(self.profile)
                )
                return False

        elif self.profile == "HDR":
            if not "hevc-hdr-" in response:
                self.logger.info(
                    "This item does not have {} Manifest".format(self.profile)
                )
                return False

        elif self.profile == "DOLBY_VISION":
            if not "hevc-dv5-" in response and "hevc-dv-" not in response:
                self.logger.info(
                    "This item does not have {} Manifest".format(self.profile)
                )
                return False

        return True

    def get_widevine_params(self, response):
        cert_data_b64 = (
            "CAUSwwUKvQIIAxIQ5US6QAvBDzfTtjb4tU/7QxiH8c+TBSKOAjCCAQoCggEBAObzvlu2hZRsapAPx4A"
            + "a4GUZj4/GjxgXUtBH4THSkM40x63wQeyVxlEEo1D/T1FkVM/S+tiKbJiIGaT0Yb5LTAHcJEhODB40"
            + "TXlwPfcxBjJLfOkF3jP6wIlqbb6OPVkDi6KMTZ3EYL6BEFGfD1ag/LDsPxG6EZIn3k4S3ODcej6YS"
            + "zG4TnGD0szj5m6uj/2azPZsWAlSNBRUejmP6Tiota7g5u6AWZz0MsgCiEvnxRHmTRee+LO6U4dswz"
            + "F3Odr2XBPD/hIAtp0RX8JlcGazBS0GABMMo2qNfCiSiGdyl2xZJq4fq99LoVfCLNChkn1N2NIYLrS"
            + "tQHa35pgObvhwi7ECAwEAAToQdGVzdC5uZXRmbGl4LmNvbRKAA4TTLzJbDZaKfozb9vDv5qpW5A/D"
            + "NL9gbnJJi/AIZB3QOW2veGmKT3xaKNQ4NSvo/EyfVlhc4ujd4QPrFgYztGLNrxeyRF0J8XzGOPsvv"
            + "9Mc9uLHKfiZQuy21KZYWF7HNedJ4qpAe6gqZ6uq7Se7f2JbelzENX8rsTpppKvkgPRIKLspFwv0EJ"
            + "QLPWD1zjew2PjoGEwJYlKbSbHVcUNygplaGmPkUCBThDh7p/5Lx5ff2d/oPpIlFvhqntmfOfumt4i"
            + "+ZL3fFaObvkjpQFVAajqmfipY0KAtiUYYJAJSbm2DnrqP7+DmO9hmRMm9uJkXC2MxbmeNtJHAHdbg"
            + "KsqjLHDiqwk1JplFMoC9KNMp2pUNdX9TkcrtJoEDqIn3zX9p+itdt3a9mVFc7/ZL4xpraYdQvOwP5"
            + "LmXj9galK3s+eQJ7bkX6cCi+2X+iBmCMx4R0XJ3/1gxiM5LiStibCnfInub1nNgJDojxFA3jH/IuU"
            + "cblEf/5Y0s1SzokBnR8V0KbA=="
        )

        try:
            init_data_b64 = response["result"]["video_tracks"][0]["drmHeader"]["bytes"]
        except KeyError:
            self.logger.info("Cannot get init_data_b64, {}".format(response))
            init_data_b64 = None

        return init_data_b64, cert_data_b64

    def licenseResponseBase64(self, data_response):
        try:
            license_b64 = data_response["result"][0]["licenseResponseBase64"]
        except Exception:
            self.logger.info("MSL LICENSE Error Message: {}".format(data_response))
            return None

        return license_b64

    def get_keys(self,):
        KEYS = []
        self.logger.info(f"\nGetting {self.profile}...")

        MSL = self.MSL()

        LICENSE_PROFILES = self.Profiles.BASE
        LICENSE_PROFILES += self.Profiles.AUDIO["ATMOS"]
        LICENSE_PROFILES += (
            self.Profiles.get(profile=self.profile, resolution="SD")
            if self.profile == "MAIN"
            else self.Profiles.get(profile=self.profile, resolution="HD")
        )


        BASE = ["heaac-2-dash", "heaac-2hq-dash"] + ["BIF240", "BIF320", "dfxp-ls-sdh"]

        BASE += ["playready-h264hpl22-dash",
                "playready-h264hpl30-dash",
                "playready-h264hpl31-dash",
                "playready-h264hpl40-dash"]

        dv = ['BIF240', 'BIF320', 'webvtt-lssdh-ios8', 'dfxp-ls-sdh', 'ddplus-2.0-dash', 'dd-5.1-dash', 'ddplus-5.1-dash', 'ddplus-5.1hq-dash', 'ddplus-atmos-dash', 'hevc-dv5-main10-L30-dash-cenc', 'hevc-dv5-main10-L31-dash-cenc', 'hevc-dv5-main10-L40-dash-cenc', 'hevc-dv5-main10-L41-dash-cenc', 'hevc-dv5-main10-L30-dash-cenc-prk', 'hevc-dv5-main10-L31-dash-cenc-prk', 'hevc-dv5-main10-L40-dash-cenc-prk', 'hevc-dv5-main10-L41-dash-cenc-prk', 'hevc-dv5-main10-L30-dash-cenc-tl', 'hevc-dv5-main10-L31-dash-cenc-tl', 'hevc-dv5-main10-L40-dash-cenc-tl', 'hevc-dv5-main10-L41-dash-cenc-tl']
        hdr = ['BIF240', 'BIF320', 'webvtt-lssdh-ios8', 'dfxp-ls-sdh', 'ddplus-2.0-dash', 'dd-5.1-dash', 'ddplus-5.1-dash', 'ddplus-5.1hq-dash', 'ddplus-atmos-dash', 'hevc-hdr-main10-L30-dash-cenc', 'hevc-hdr-main10-L31-dash-cenc', 'hevc-hdr-main10-L40-dash-cenc', 'hevc-hdr-main10-L41-dash-cenc', 'hevc-hdr-main10-L30-dash-cenc-prk', 'hevc-hdr-main10-L31-dash-cenc-prk', 'hevc-hdr-main10-L40-dash-cenc-prk', 'hevc-hdr-main10-L41-dash-cenc-prk', 'hevc-hdr-main10-L30-dash-cenc-tl', 'hevc-hdr-main10-L31-dash-cenc-tl', 'hevc-hdr-main10-L40-dash-cenc-tl', 'hevc-hdr-main10-L41-dash-cenc-tl']
        hevc = ['BIF240', 'BIF320', 'webvtt-lssdh-ios8', 'dfxp-ls-sdh', 'ddplus-2.0-dash', 'dd-5.1-dash', 'ddplus-5.1-dash', 'ddplus-5.1hq-dash', 'ddplus-atmos-dash', 'hevc-main10-L30-dash-cenc', 'hevc-main10-L31-dash-cenc', 'hevc-main10-L40-dash-cenc', 'hevc-main10-L41-dash-cenc', 'hevc-main10-L30-dash-cenc-prk', 'hevc-main10-L31-dash-cenc-prk', 'hevc-main10-L40-dash-cenc-prk', 'hevc-main10-L41-dash-cenc-prk', 'hevc-main10-L30-dash-cenc-tl', 'hevc-main10-L31-dash-cenc-tl', 'hevc-main10-L40-dash-cenc-tl', 'hevc-main10-L41-dash-cenc-tl']
        hpl = ['BIF240', 'BIF320', 'webvtt-lssdh-ios8', 'dfxp-ls-sdh', 'ddplus-2.0-dash', 'dd-5.1-dash', 'ddplus-5.1-dash', 'ddplus-5.1hq-dash', 'ddplus-atmos-dash', 'playready-h264hpl22-dash', 'playready-h264hpl30-dash', 'playready-h264hpl31-dash']

        if self.profile == "HIGH":
            LICENSE_PROFILES = hpl
        elif self.profile == "HEVC":
            LICENSE_PROFILES = hevc
        elif self.profile == "HDR":
            LICENSE_PROFILES = hdr
        elif self.profile == "DOLBY_VISION":
            LICENSE_PROFILES = dv

        # print(LICENSE_PROFILES)
        # print(MSL["device"])

        MSL.update({"profiles": list(set(LICENSE_PROFILES))})

        client = MSLClient(MSL)

        try:
            response = client.load_playlist(int(self.netflixId))
        except Exception as e:
            self.logger.info("Manifest Error: {}".format(e))
            return KEYS

        if not self.check_response(response):
            return KEYS

        init_data_b64, cert_data_b64 = self.get_widevine_params(response)

        if not any([init_data_b64, cert_data_b64]):
            return KEYS

        wvdecrypt = WvDecrypt(
            init_data_b64=init_data_b64, cert_data_b64=None, device=MSL["device"],
        )
        challenge = wvdecrypt.get_challenge()
        data = client.get_license(challenge)
        license_b64 = self.licenseResponseBase64(data)
        if license_b64:
            wvdecrypt.update_license(license_b64)
            Correct, keyswvdecrypt = wvdecrypt.start_process()
            KEYS = keyswvdecrypt

        return KEYS

    def get_keys_chrome(self, netflixid, securenetflixid):

        from helpers.Parsers.netflix.pymsl_chrome import MslClient

        KEYS = []
        self.logger.info(f"\nGetting {self.profile} (Chrome CDM)...")

        BASE = ["heaac-2-dash", "heaac-2hq-dash"] + ["BIF240", "BIF320", "dfxp-ls-sdh"]

        BASE += ["playready-h264hpl22-dash",
                "playready-h264hpl30-dash",
                "playready-h264hpl31-dash",
                "playready-h264hpl40-dash"]

        HEVC = ['hevc-main10-L30-dash-cenc', 'hevc-main10-L30-dash-cenc-prk', 'hevc-main10-L30-dash-cenc-tl', 'hevc-main10-L31-dash-cenc', 'hevc-main10-L31-dash-cenc-prk', 'hevc-main10-L31-dash-cenc-tl', 'hevc-main10-L40-dash-cenc', 'hevc-main10-L40-dash-cenc-prk', 'hevc-main10-L40-dash-cenc-tl', 'hevc-main10-L41-dash-cenc', 'hevc-main10-L41-dash-cenc-prk', 'hevc-main10-L41-dash-cenc-tl']
        HEVC_DO = ['hevc-main10-L30-dash-cenc', 'hevc-main10-L30-dash-cenc-prk-do', 'hevc-main10-L30-dash-cenc-tl', 'hevc-main10-L31-dash-cenc', 'hevc-main10-L31-dash-cenc-prk-do', 'hevc-main10-L31-dash-cenc-tl', 'hevc-main10-L40-dash-cenc', 'hevc-main10-L40-dash-cenc-prk-do', 'hevc-main10-L40-dash-cenc-tl', 'hevc-main10-L41-dash-cenc', 'hevc-main10-L41-dash-cenc-prk-do', 'hevc-main10-L41-dash-cenc-tl']
        HDR = ['hevc-hdr-main10-L30-dash-cenc', 'hevc-hdr-main10-L30-dash-cenc-prk', 'hevc-hdr-main10-L31-dash-cenc', 'hevc-hdr-main10-L31-dash-cenc-prk', 'hevc-hdr-main10-L40-dash-cenc', 'hevc-hdr-main10-L40-dash-cenc-prk', 'hevc-hdr-main10-L41-dash-cenc', 'hevc-hdr-main10-L41-dash-cenc-prk']
        DV = ['hevc-dv5-main10-L30-dash-cenc', 'hevc-dv5-main10-L30-dash-cenc-prk', 'hevc-dv5-main10-L31-dash-cenc', 'hevc-dv5-main10-L31-dash-cenc-prk', 'hevc-dv5-main10-L40-dash-cenc', 'hevc-dv5-main10-L40-dash-cenc-prk', 'hevc-dv5-main10-L41-dash-cenc', 'hevc-dv5-main10-L41-dash-cenc-prk']

        if self.profile == "HIGH":
            profiles = BASE
        elif self.profile == "HEVC":
            profiles = HEVC + BASE
        elif self.profile == "HDR":
            profiles = HDR + BASE
        elif self.profile == "DOLBY_VISION":
            profiles = DV + BASE

        user_auth_data = {
            "scheme": "NETFLIXID",
            "authdata": {"netflixid": netflixid, "securenetflixid": securenetflixid},
        }

        client = MslClient(user_auth_data, profiles=profiles)

        try:
            response = client.load_manifest(int(self.netflixId))
        except Exception as e:
            self.logger.info("Manifest Error: {}".format(e))
            return KEYS

        # CorrectManifest = False

        # while CorrectManifest is False:

        #     client = MslClient(user_auth_data, profiles=profiles)

        #     try:
        #         response = client.load_manifest(int(self.netflixId))
        #     except Exception as e:
        #         self.logger.info("Manifest Error: {}".format(e))
        #         return KEYS

        #     CorrectManifest = self.check_response(response)
        #     if CorrectManifest is False and self.profile != "HEVC":
        #         return KEYS

        #     self.logger.info(f"Trying HEVC DO PROFILES...")
        #     profiles = HEVC_DO + BASE
        #     time.sleep(2)


        if not self.check_response(response):
            return KEYS

        init_data_b64, cert_data_b64 = self.get_widevine_params(response)

        if not any([init_data_b64, cert_data_b64]):
            return KEYS

        wvdecrypt = WvDecrypt(
            init_data_b64=init_data_b64, cert_data_b64=cert_data_b64, device=device,
        )

        challenge = wvdecrypt.get_challenge()

        session_id = str(time.time()).replace(".", "")[0:-2]

        try:
            data = client.get_license(challenge, session_id)
        except Exception as e:
            self.logger.info("License Error: {}".format(e))
            return KEYS

        license_b64 = self.licenseResponseBase64(data)

        if license_b64:
            wvdecrypt.update_license(license_b64)
            Correct, keyswvdecrypt = wvdecrypt.start_process()
            KEYS = keyswvdecrypt

        return KEYS
