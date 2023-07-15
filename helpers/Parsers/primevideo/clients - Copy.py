import base64
import hashlib
import json
import logging
import os
import re
import string
import sys
import time
import urllib.parse
import webbrowser
from os.path import isfile
from pprint import pprint
from random import choices

import requests

from helpers.Parsers.primevideo.utils import RANDOM_SERIAL

PV_REGION = "ps"  # ps=EU, ps-na + ps-fe + ps-ca

ANDROID_REGISTRATION = {
    "domain": "Device",
    "app_name": "AIV",
    "app_version": "3.12.0",
    "device_model": "SHIELD Android TV",
    "os_version": "28",
    "device_type": "A1KAXIG6VXSG8Y",
    "device_serial": RANDOM_SERIAL(),
    "device_name": "%FIRST_NAME%'s%DUPE_STRATEGY_1ST% Shield TV",
    "software_version": "248",
}

ENDPOINT = {
    "codepair": "https://api.amazon.com/auth/create/codepair",
    "register": "https://api.amazon.{domain}/auth/register",
    "token": "https://api.amazon.{domain}/auth/token",
    "cookies": "https://api.amazon.{domain}/ap/exchangetoken/cookies",
    "GetAppStartupConfig": "https://na.api.amazonvideo.com/cdp/usage/v3/GetAppStartupConfig",
    "primevideo_register_device": "https://www.primevideo.{domain}/region/na/ontv/code",
    "amazon_register_device": "https://www.amazon.{domain}/gp/video/ontv/code",
    "manifest": "https://{video_base_url}/cdp/catalog/GetPlaybackResources",
}

UA = "Dalvik/2.1.0 (Linux; U; Android 9; SHIELD Android TV Build/PPR1.180610.011)"

HEADERS = {
    "Accept-Language": "en_US",
    "User-Agent": UA,
    "Authorization": "",
}

NON_PV = ["uk", "us", "jp", "de"]

class Android:
    def __init__(self,):
        """CLASS FOR AMZN Android"""
        self.session = requests.Session()
        self.headers = HEADERS

    def ActiveAndroidClient(self):
        self.manufacturer = "NVIDIA"
        self.device_chipset = "tegra"
        self.software_version = ANDROID_REGISTRATION["software_version"]
        self.device_type = ANDROID_REGISTRATION["device_type"]
        self.device_domain = ANDROID_REGISTRATION["domain"]
        self.app_name = ANDROID_REGISTRATION["app_name"]
        self.app_version = ANDROID_REGISTRATION["app_version"]
        self.device_model = ANDROID_REGISTRATION["device_model"]
        self.os_version = ANDROID_REGISTRATION["os_version"]
        self.device_serial = ANDROID_REGISTRATION["device_serial"]
        self.device_name = ANDROID_REGISTRATION["device_name"]
        self.firmware = f"fmw:{self.os_version}-app:3.0.{self.software_version}.49301"
        self.resourceUsage = "CacheResources"
        self.UA = UA
        self.expire_in = int(time.time())
        return 

    def AmazonRegionConfig(self, region):

        if not region in NON_PV:
            region = "ps"
        
        if region == "us":
            return region, "com"
        elif region == "uk":
            return region, "co.uk"
        elif region == "de":
            return region, "de"
        elif region == "jp":
            return region, "co.jp"
        elif region == "ps":
            return region, "com"

        return 

    def https_to_http(self, Url):
        Url = re.sub("https://", "http://", Url)
        return Url

    def LoadJsonFile(self, File):
        with open(File, "r") as f:
            return json.load(f)
        return

    def DumpToJsonFile(self, File, Data):
        with open(File, "w") as f:
            f.write(json.dumps(Data, indent=4))

        return

    def open_page(self, Url, public_code):
        print(f"\nPlease visit {Url} and enter the code: {public_code}\n")
        webbrowser.open(Url)
        return

    def register(self):

        #@codepair
        response = self.session.post(
            url=ENDPOINT["codepair"],
            data=json.dumps({"code_data": ANDROID_REGISTRATION}),
            headers={"content-type": "application/json; charset=UTF-8"},
        )

        pair_data = response.json()
        public_code = pair_data.get("public_code")
        private_code = pair_data.get("private_code")

        self.open_page(ENDPOINT["amazon_register_device"].format(domain=self.domain), public_code) if self.region in NON_PV else self.open_page(ENDPOINT["primevideo_register_device"].format(domain=self.domain), public_code)

        _ = input("Press ENTER when you done...")

        response = self.session.post(
            url=ENDPOINT["register"].format(domain=self.domain),
            data=json.dumps(
                {
                    "auth_data": {
                        "code_pair": {
                            "public_code": public_code,
                            "private_code": private_code,
                        }
                    },
                    "cookies": {
                        "domain": f".amazon.{self.domain}",
                        "website_cookies": [],
                    },
                    "registration_data": ANDROID_REGISTRATION,
                    "requested_extensions": ["device_info", "customer_info"],
                    "requested_token_type": [
                        "bearer",
                        "mac_dms",
                        "store_authentication_cookie",
                        "website_cookies",
                    ],
                }
            ),
            headers={"content-type": "application/json; charset=UTF-8"},
        )

        try:
            token_data = response.json()["response"]["success"]
            refresh_token = token_data["tokens"]["bearer"]["refresh_token"]
            access_token = token_data["tokens"]["bearer"]["access_token"]
            cookies_path = token_data["tokens"]["website_cookies"]
            device_serial = token_data["extensions"]["device_info"][
                "device_serial_number"
            ]
            device_type = token_data["extensions"]["device_info"]["device_type"]
        except Exception:
            raise ValueError("Error in register: {}".format(response.text))


        cookies = "; ".join(
            ["{}={}".format(cookie["Name"], cookie["Value"]) for cookie in cookies_path]
        )

        data = {
            "refresh_token": refresh_token,
            "access_token": f"bearer {access_token}",
            "cookies": cookies,
            "device_serial": device_serial,
            "device_type": device_type,
            "expire_in": int(time.time()) + 3300,
            "params": {
                "public_code": public_code,
                "private_code": private_code,
                "domain": self.domain,
                "region": self.region,
                "ANDROID_REGISTRATION": ANDROID_REGISTRATION,
            },
            "RESPONSE": response.json(),
        }

        token = open(self.token_file, mode="w")
        token.write(json.dumps(data))
        token.close()
        return

    def do_refresh_token(self, refresh_token):

        refresh = self.session.post(
            url=ENDPOINT["token"].format(domain=self.domain),
            json={
                "domain": self.device_domain,
                "app_name": self.app_name,
                "app_version": self.app_version,
                "device_model": self.device_model,
                "os_version": self.os_version,
                "device_type": self.device_type,
                "device_serial": self.device_serial,
                "device_name": self.device_name,
                "software_version": self.software_version,
                "requested_token_type": "access_token",
                "source_token_type": "refresh_token",
                "source_token": refresh_token,
            },
            headers={"User-Agent": self.UA, "x-gasc-enabled": "true"}
            if not self.region in NON_PV
            else {"User-Agent": self.UA},
        )

        try:
            token_request = refresh.json()
            token_type = token_request["token_type"]
            access_token = token_request["access_token"]
            token = f"{token_type} {access_token}"
        except Exception:
            raise ValueError("Error in getting refresh token: {}".format(refresh.text))

        return token

    def do_refresh_cookies(self, refresh_token):

        payload = (
            f"requested_token_type=auth_cookies&app_name={self.app_name}&app_version={self.app_version}&"
            + f"di.sdk.version={self.software_version}&domain=.amazon.{self.domain}&source_token_type=refres"
            + f"h_token&source_token={refresh_token}&url=https://www.amazon.{self.domain}/ap/signin?_"
            + f"encoding=UTF8&accountStatusPolicy=P1&clientContext=259-2963051-6784519&openid.as"
            + f"soc_handle=deflex&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_"
            + f"select&openid.identity=http://specs.openid.net/auth/2.0/identifier_select&openid"
            + f".mode=checkid_setup&openid.ns=http://specs.openid.net/auth/2.0&openid.ns.pape=ht"
            + f"tp://specs.openid.net/extensions/pape/1.0&openid.pape.max_auth_age=0&openid.retu"
            + f"rn_to=https://www.amazon.{self.domain}/gp/video/settings/devices/ref=dv_web_auth_no_r"
            + f"e_sig?ie=UTF8&language=en_US"
        )

        response_cookies = self.session.post(
            url=ENDPOINT["cookies"].format(domain=self.domain),
            data=payload,
            headers={
                "x-amzn-identity-auth-domain": "api.amazon.com",
                "User-Agent": self.UA,
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": f"api.amazon.{self.domain}",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
            },
        )

        try:
            cookies_path = response_cookies.json()["response"]["tokens"]["cookies"][
                f".amazon.{self.domain}"
            ]
        except Exception:
            raise ValueError(
                "Error in getting refresh cookies: {}".format(response_cookies.text)
            )

        cookies = "; ".join(
            ["{}={}".format(cookie["Name"], cookie["Value"]) for cookie in cookies_path]
        )

        return cookies

    def GetAppStartupConfig(self):

        StartupConfig = self.session.get(
            url=ENDPOINT["GetAppStartupConfig"],
            params={
                "deviceTypeID": self.device_type,
                "deviceID": self.device_serial,
                "firmware": 1,
                "version": 1,
                "format": "json",
            },
            headers=self.headers,
        )

        try:
            data = StartupConfig.json()
            region = data["customerConfig"]["homeRegion"].lower()
            site_base_url = data["territoryConfig"]["defaultVideoWebsite"]
            marketplace_id = data["customerConfig"]["marketplaceId"]
            video_base_url = data["customerConfig"]["baseUrl"]
            api_base_url = data["deviceConfig"]["url"]
            video_base_url = self.https_to_http(video_base_url)
            api_base_url = self.https_to_http(api_base_url)
        except Exception as e:
            raise ValueError(
                "GetAppStartupConfig Error: {}\n{}".format(e, StartupConfig.text)
            )

        return region, site_base_url, marketplace_id, video_base_url, api_base_url

    def refresh_token_cookies(self):

        if self.token_data["expire_in"] <= self.expire_in:
            print("\nRefreshing Token...")
            access_token = self.do_refresh_token(self.token_data["refresh_token"])
            # cookies = self.do_refresh_cookies(self.token_data["refresh_token"])
            self.token_data.update({"access_token": access_token})
            # self.token_data.update({"cookies": cookies})
            self.token_data.update({"expire_in": int(time.time()) + 3600})
        
        print("expire in: {} min".format(int((self.token_data["expire_in"] - self.expire_in) / 60)))

        return

    def client(self, token_file, region):
        self.ActiveAndroidClient()
        self.token_file = token_file
        self.region, self.domain = self.AmazonRegionConfig(region=region)
        if not isfile(self.token_file):
            print("\nRegister Your Compatible TV or Device")
            confirm = input("Do you want to register a device (y,n)? ")
            if confirm.strip().lower().startswith("n"):
                exit(0)

            self.register()

        self.token_data = self.LoadJsonFile(self.token_file)
        self.refresh_token = self.token_data["refresh_token"]
        self.device_serial = self.token_data["device_serial"]
        self.device_type = self.token_data["device_type"]
        self.refresh_token_cookies()
        self.access_token = self.token_data["access_token"]
        self.cookies = self.token_data["cookies"]
        self.DumpToJsonFile(self.token_file, self.token_data)
        self.token_data = self.LoadJsonFile(self.token_file)

        self.headers.update({"Authorization": self.access_token})
        if not self.region in NON_PV:
            self.headers.update({"x-gasc-enabled": "true"})

        (
            _,
            self.site_base_url,
            self.marketplace_id,
            self.video_base_url,
            self.api_base_url,
        ) = self.GetAppStartupConfig()


        if self.region == "us":
            self.video_base_url = "na.api.amazonvideo.com"

        return

    def PlayBackParams(self, Asin, Profile):
        URL = ENDPOINT["manifest"].format(video_base_url=self.video_base_url)

        PARAMS = dict(
            consumptionType="Streaming",
            desiredResources="AudioVideoUrls,PlaybackUrls,CatalogMetadata,ForcedNarratives,SubtitlePresets,SubtitleUrls,TransitionTimecodes,TrickplayUrls,CuepointPlaylist,PlaybackSettings",
            deviceID=self.device_serial,
            deviceTypeID=self.device_type,
            firmware=self.firmware,
            deviceModel=self.device_model,
            manufacturer=self.manufacturer,
            deviceChipset=self.device_chipset,
            resourceUsage=self.resourceUsage,
            softwareVersion=self.software_version,
            format="json",
            osLocale="en_US",
            deviceProtocolOverride="Https",
            version="1",
            videoMaterialType="Feature",
        )

        PARAMS.update({"titleId": Asin} if not self.region in NON_PV else {"asin": Asin})

        if Profile in ["CBR", "HEVC", "UHD", "HDR"]:
            PARAMS.update({"audioTrackId": "NO"})
        else:
            PARAMS.update({"audioTrackId": "all"})

        if Profile == "CVBR":
            PARAMS["deviceBitrateAdaptationsOverride"] = "CVBR,CBR"
            PARAMS["deviceVideoQualityOverride"] = "HD"
            PARAMS["deviceHdrFormatsOverride"] = "None"
            PARAMS["deviceVideoCodecOverride"] = "H264"
            PARAMS["supportedDRMKeyScheme"] = "DUAL_KEY"
            PARAMS["deviceDrmOverride"] = "CENC"
            PARAMS["deviceStreamingTechnologyOverride"] = "DASH"

        elif Profile == "CBR":
            PARAMS["deviceBitrateAdaptationsOverride"] = "CBR"
            PARAMS["deviceVideoQualityOverride"] = "HD"
            PARAMS["deviceHdrFormatsOverride"] = "None"
            PARAMS["deviceVideoCodecOverride"] = "H264"
            PARAMS["supportedDRMKeyScheme"] = "DUAL_KEY"
            PARAMS["deviceDrmOverride"] = "CENC"
            PARAMS["deviceStreamingTechnologyOverride"] = "DASH"

        elif Profile == "HEVC":
            PARAMS["deviceBitrateAdaptationsOverride"] = "CVBR,CBR"
            PARAMS["deviceVideoCodecOverride"] = "H265"
            PARAMS["deviceVideoQualityOverride"] = "HD"
            PARAMS["deviceHdrFormatsOverride"] = "None"
            PARAMS["supportedDRMKeyScheme"] = "DUAL_KEY"
            PARAMS["deviceDrmOverride"] = "CENC"
            PARAMS["deviceStreamingTechnologyOverride"] = "DASH"

        elif Profile == "UHD":
            PARAMS["deviceBitrateAdaptationsOverride"] = "CVBR"
            PARAMS["deviceVideoCodecOverride"] = "H265"
            PARAMS["deviceVideoQualityOverride"] = "UHD"
            PARAMS["deviceHdrFormatsOverride"] = "None"
            PARAMS["deviceFrameRateOverride"] = "High"
            PARAMS["supportedDRMKeyScheme"] = "DUAL_KEY"
            PARAMS["deviceDrmOverride"] = "CENC"
            PARAMS["deviceStreamingTechnologyOverride"] = "DASH"

        elif Profile == "HDR":
            PARAMS["deviceBitrateAdaptationsOverride"] = "CBR"
            PARAMS["deviceVideoCodecOverride"] = "H265"
            PARAMS["deviceVideoQualityOverride"] = "UHD"
            PARAMS["deviceHdrFormatsOverride"] = "Hdr10"
            PARAMS["supportedDRMKeyScheme"] = "DUAL_KEY"
            PARAMS["deviceDrmOverride"] = "CENC"
            PARAMS["deviceStreamingTechnologyOverride"] = "DASH"

        return URL, PARAMS 

    def RequestPlayBack(self, url, params):
        response = self.session.get(
            url=url, params=params, headers=self.headers,
        )

        if response.status_code != 200 or response.text.__contains__("rightsException"):
            raise ValueError(
                "Amazon return {} when obtaining the Playback Manifest\n{}".format(
                    response.status_code, response.text
                )
            )

        return response.json()
