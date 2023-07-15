from http.cookiejar import MozillaCookieJar
from pprint import pprint

from helpers.Parsers.primevideo.clients import Android
from helpers.Parsers.primevideo.extractor import extractor
from helpers.Parsers.primevideo.license_request import license_request
from helpers.Parsers.primevideo.metadata import metadata
from helpers.Parsers.primevideo.metadata2 import get_metadata
from helpers.Parsers.primevideo.playback import WebPlayBack
from helpers.Parsers.primevideo.utils import PlayBackParser, Utils


class prime:
    def __init__(self,):
        """CLASS FOR HOLDING THE CLASSES FOR PRIME PY"""
        self.cookie = None
        self.Utils = Utils()
        self.metadata = metadata()
        self.license_request = license_request()
        self.Android = Android()
        self.WebPlayBack = WebPlayBack()
        self.PlayBackParser = PlayBackParser()
        self.extractor = extractor()

    def CookieJar(self, filepath):
        self.cookie = self.Utils.CookieJar(filepath)
        self.metadata.addCookies(self.cookie)
        self.WebPlayBack.addCookies(self.cookie)
        return

    def RequestPlayBackWeb(self, asin, region, profile, chpaters=False, sd=False, audio_only=False):
        print("Requesting: [CHROME] - [{}] [{}]{}{}".format(profile.upper(), region.upper(), " [SD]" if sd is True else "", " [CHAPTERS]" if chpaters is True else ""))
        url, params = self.WebPlayBack.PlayBackParams(asin, region, profile, sd=sd)
        data = self.WebPlayBack.RequestPlayBack(url, params)
        return self.PlayBackParser.Parser(
            url=url,
            params=params,
            data=data,
            profile=profile,
            chapters=None if chpaters is False else self.WebPlayBack.RequestChapters(region, data),
            region=region,
            license_headers=self.WebPlayBack.headers,
            client="chrome",
            cert=True,
            audio_only=audio_only
        )

    def RequestPlayBackAndroid(self, asin, region, profile, token_file, audio_only=False):
        self.Android.client(token_file, region)
        print("Requesting: [ANDROID] - [{}] [{}]".format(profile.upper(), region.upper()))
        url, params = self.Android.PlayBackParams(asin, profile)
        data = self.Android.RequestPlayBack(url, params)
        return self.PlayBackParser.Parser(
            url=url,
            params=params,
            data=data,
            profile=profile,
            chapters=None,
            region=region,
            license_headers=self.Android.headers,
            client="android",
            cert=False,
            audio_only=audio_only
        )

    def PrimeLicenseRequest(self, pssh, config, device):
        return self.license_request._license(
            url=config.get("license_url"),
            headers=config.get("license_headers"),
            pssh=pssh,
            cert=config.get("cert"),
            device=device
        )

    def RequestHtml(self, Url, cookies=None):
        return self.metadata.RequestHtml(Url)

    def RequestMeta(self, Url, cookies=None):
        return get_metadata(Url, self.cookie)

    def PlayBacksExtractor(self, playbacks, wvtracks):
        return self.extractor.PlayBacksExtractor(playbacks, wvtracks)
