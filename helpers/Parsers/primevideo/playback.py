import hashlib
import json
import os
import re

import requests

from helpers.Parsers.primevideo.utils import chapters_generator

_REGIONS = dict(
    us=dict(
        site_base_url='www.amazon.com',
        video_base_url='atv-ps.amazon.com',
        marketplace_id='ATVPDKIKX0DER',
        clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
    ),
    uk=dict(
        site_base_url='www.amazon.co.uk',
        video_base_url='atv-ps-eu.amazon.co.uk',
        marketplace_id='A2IR4J4NTCP2M5',
        clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
    ),
    de=dict(
        site_base_url='www.amazon.de',
        video_base_url='atv-ps-eu.amazon.de',
        marketplace_id='A1PA6795UKMFR9',
        clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
    ),
    jp=dict(
        site_base_url='www.amazon.co.jp',
        video_base_url='atv-ps-fe.amazon.co.jp',
        marketplace_id='A1VC38T7YXB528',
        clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
    ),
    ps=dict(
        eu=dict(
            site_base_url='www.primevideo.com',
            video_base_url='atv-ps-eu.primevideo.com',
            marketplace_id='A3K6Y4MI8GDYMT',
            clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
        ),
        na=dict(
            site_base_url='www.primevideo.com',
            video_base_url='atv-ps.primevideo.com',
            marketplace_id='ART4WZ8MWBX2Y',
            clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
        ),
        ca=dict(
            site_base_url='www.primevideo.com',
            video_base_url='atv-ps.primevideo.com',
            marketplace_id='ART4WZ8MWBX2Y',
            clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
        ),
        fe=dict(
            site_base_url='www.primevideo.com',
            video_base_url='atv-ps-fe.primevideo.com',
            marketplace_id='A15PK738MTQHSO',
            clientId='f22dbddb-ef2c-48c5-8876-bed0d47594fd',
        ),
    )
)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
ENDPOINT = "https://{video_base_url}/cdp/catalog/GetPlaybackResources"
CHAPTERS_ENDPOINT = "https://{video_base_url}/swift/page/xray"
NON_PV = ["uk", "us", "jp", "de"]
HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "es,ca;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Pragma": "no-cache",
    "User-Agent": UA,
    "cookie": "",
}

class WebPlayBack:
    def __init__(self,):
        """CLASS FOR AMZN WebPlayBack"""
        self.session = requests.Session()
        self.headers = HEADERS

    def GenerateDeviceID(self,):
        deviceID = hashlib.sha224(("CustomerID" + UA).encode("utf-8"))
        return deviceID.hexdigest()

    def addCookies(self, cookie):
        self.headers.update({"cookie": cookie})
        return

    def PlayBackParams(self, Asin, AccountRegion, Profile, sd=False):

        # print(AccountRegion)
        # AccountRegion = "eu"
        CONFIG = _REGIONS[AccountRegion] if AccountRegion in NON_PV else _REGIONS["ps"][AccountRegion]
        URL = ENDPOINT.format(video_base_url=CONFIG["video_base_url"])

        PARAMS = dict(
            asin=Asin,
            consumptionType="Streaming",
            desiredResources="AudioVideoUrls,PlaybackUrls,CatalogMetadata,ForcedNarratives,SubtitlePresets,SubtitleUrls,TransitionTimecodes,TrickplayUrls,CuepointPlaylist,PlaybackSettings",
            deviceID=self.GenerateDeviceID(),
            deviceTypeID="AOAGZA014O5RE",
            resourceUsage="CacheResources",
            operatingSystemName="Linux" if sd else "Windows",
            operatingSystemVersion="unknown" if sd else "10.0",
            deviceDrmOverride="CENC",
            deviceStreamingTechnologyOverride="DASH",
            deviceProtocolOverride="Https",
            supportedDRMKeyScheme="DUAL_KEY",
            titleDecorationScheme="primary-content",
            subtitleFormat="TTMLv2",
            languageFeature="MLFv2",
            firmware="1",
            playerAttributes='{"frameRate":"HFR"}',
            deviceBitrateAdaptationsOverride="CVBR,CBR",
            videoMaterialType="Feature",
            playerType="html5",
            deviceVideoQualityOverride="SD" if sd else "HD",
            gascEnabled="false" if AccountRegion in NON_PV else "true",
            marketplaceID=CONFIG["marketplace_id"],
            clientId=CONFIG["clientId"],
        )

        PARAMS.update({"audioTrackId": "NO"}) if Profile in ["CBR", "HEVC"] else PARAMS.update({"audioTrackId": "all"})

        if Profile == "CVBR":
            PARAMS.update({"deviceBitrateAdaptationsOverride": "CVBR,CBR"})
        elif Profile == "CBR":
            PARAMS.update({"deviceBitrateAdaptationsOverride": "CBR"})
        elif Profile == "HEVC":
            PARAMS.update({"deviceBitrateAdaptationsOverride": "CVBR,CBR"})
            PARAMS.update({"deviceVideoCodecOverride": "H265"})

        return URL, PARAMS

    def RequestChapters(self, AccountRegion: str, data: dict):
        if data.get("returnedTitleRendition", {}).get("contentId", None):
            vcid = data.get("returnedTitleRendition").get("contentId")

            CONFIG = _REGIONS[AccountRegion] if AccountRegion in NON_PV else _REGIONS["ps"][AccountRegion]
            URL = CHAPTERS_ENDPOINT.format(video_base_url=CONFIG["video_base_url"])

            response = self.session.get(
                url=URL,
                params=dict(
                    firmware="1",
                    format="json",
                    gascEnabled="false" if AccountRegion in NON_PV else "true",
                    deviceID=self.GenerateDeviceID(),
                    deviceTypeID="AOAGZA014O5RE",
                    marketplaceId=CONFIG["marketplace_id"],
                    decorationScheme="none",
                    version="inception-v2",
                    featureScheme="INCEPTION_LITE_FILMO_V2",
                    uxLocale="en-US",
                    pageType="xray",
                    pageId="fullScreen",
                    serviceToken=json.dumps(
                    {
                        "consumptionType": "Streaming",
                        "deviceClass": "normal",
                        "playbackMode": "playback",
                        "vcid": vcid,
                    }
                    ),
                ),
                headers=self.headers,
            )

            if response.status_code == 200:
                return chapters_generator(response.json())

        return None

    def RequestPlayBack(self, url, params):
        response = self.session.get(
            url=url, params=params, headers=self.headers,
        )

        if response.status_code != 200 or response.json().get("errorsByResource") or response.json().get("error") or response.text.__contains__("rightsException"):
            raise ValueError("Amazon return {} when obtaining the Playback Manifest\n{}".format(response.status_code, response.text))

        return response.json()
