import html
import re
import string
import isodate
import urllib.parse
from http.cookiejar import MozillaCookieJar
from random import choices

#@addCookies
_COOKIES_REGEX = r"(lc-.+)=([a-z]{2}_[A-Z]{2})"


#@ METADATA LANGUAGE
_LANGUAGES = [
    "en_US",
    "da_DK",
    "de_DE",
    "es_ES",
    "fi_FI",
    "fr_FR",
    "id_ID",
    "it_IT",
    "ko_KR",
    "nl_NL",
    "nb_NO",
    "pl_PL",
    "pt_BR",
    "ru_RU",
    "sv_SE",
    "hi_IN",
    "ta_IN",
    "te_IN",
    "th_TH",
    "tr_TR",
    "zh_CN",
    "zh_TW",
]

_LANGUAGE = _LANGUAGES[0]

_MPD_REGEX = r"(https?://.*/)d.{0,1}/.*~/(.*)"

_CHAPTERS_TERTIARY = re.compile(r"(?:[A-Z]*)(?:[A-Za-z_ -=]*)( )")
_CHAPTERS_PRIMARY = re.compile(r"(\d+)(\.)( )")

_AVC = re.compile("avc")
_HEVC = re.compile(r"hev1\.1\.")
_HDR = re.compile(r"hev1\.2\.")
_AAC = re.compile("mp4")
_TTML = re.compile("TTMLv2")

def profile_detector(codec):
    if _AVC.search(codec):
        return "AVC"
    elif _HEVC.search(codec):
        return "HEVC"
    elif _HDR.search(codec):
        return "HDR"
    elif _AAC.search(codec):
        return "AAC"
    elif _TTML.search(codec):
        return "SRT"
    
    return codec

def mpd_duration_extractor(data):
    
    try:
        return isodate.parse_duration(data.MPD.Period["duration"]).total_seconds()
    except Exception:
        try:
            return isodate.parse_duration(data.MPD["mediaPresentationDuration"]).total_seconds()
        except Exception:
            return None

def chapters_generator(xray: dict):
    ChapterList = []
    
    try:
        for x in xray["page"]["sections"]["center"]["widgets"]["widgetList"]:
            if x["tabType"] == "scenesTab":
                for y in x["widgets"]["widgetList"]:
                    if (
                        y["items"]["itemList"][0]["blueprint"]["id"]
                        == "XraySceneItem"
                    ):
                        count = 1
                        for z in y["items"]["itemList"]:
                            ChapterNumber = str(count).zfill(2)
                            ChapterName = _CHAPTERS_PRIMARY.sub("", z["textMap"]["PRIMARY"])
                            ChapterTime = _CHAPTERS_TERTIARY.sub("", z["textMap"]["TERTIARY"] + ".000")
                            ChapterDict = {
                                "ChapterNumber": ChapterNumber,
                                "ChapterName": ChapterName,
                                "ChapterTime": ChapterTime,
                                "ChapterTXT": "CHAPTER{}={}\nCHAPTER{}NAME={}\n".format(
                                    ChapterNumber,
                                    ChapterTime,
                                    ChapterNumber,
                                    ChapterName,
                                )
                            }
                            ChapterList.append(ChapterDict)
                            count += 1
    except Exception:
        pass

    if ChapterList == []:
        return None

    return ChapterList

def RANDOM_SERIAL():
    return "".join(choices(string.ascii_uppercase + string.digits, k=40))

class PlayBackParser:
    """docstring for ClassName"""
    def __init__(self):
        """"""
    def recommended(self,):
        return sorted(self.data["audioVideoUrls"]["avCdnUrlSets"], key=lambda x: int(x["cdnWeightsRank"]), reverse=True)[-1]["cdn"]

    def basempd(self, Url):
        mpd = re.match(_MPD_REGEX, Url)
        return "{}{}".format(mpd.group(1), mpd.group(2))

    def audioVideoUrls(self):
        recommended = self.recommended()
        data = dict()
        duration = None

        #@duration
        for item in self.data["playbackUrls"]["urlSets"]:
            item = self.data["playbackUrls"]["urlSets"][item]["urls"]["manifest"]
            duration = item["duration"]
            break

        for item in self.data["audioVideoUrls"]["avCdnUrlSets"]:
            if item.get("drm", "None") != "CENC" or item.get("streamingTechnology", "None") != "DASH" or item.get("url", "None").__contains__(".ism") or item.get("url", "None").__contains__(".m3u8"):
                continue

            cdn = item["cdn"]
            for url in item["avUrlInfoList"]:
                manifest_url = url["url"]
                manifest_full = self.basempd(url["url"])
                break

            if not data.get(cdn,  None):
                data[cdn] = {
                    "cdn": cdn,
                    "duration": duration,
                    "manifest_url": manifest_url,
                    "manifest_full": manifest_full,
                    "recommended": True if item["cdn"] == recommended else False,
                }

        if data == {}:
            raise ValueError("No widevine DASH mpd found...")

        for _, value in data.items():
            if value["recommended"] is True:
                base = dict({
                    "cdn": value["cdn"],
                    "duration": duration,
                    "manifest_url": value["manifest_url"],
                    "manifest_full": value["manifest_full"],
                    "recommended": value["recommended"],
                    "manifest_cdns": data,
                })

                return base

        return dict({
            "cdn": None,
            "duration": None,
            "manifest_url": None,
            "manifest_full": None,
            "recommended": None,
            "manifest_cdns": data,
        })


    def playback(self):
        recommended = self.recommended()
        data = dict()
        for item in self.data["playbackUrls"]["urlSets"]:
            item = self.data["playbackUrls"]["urlSets"][item]["urls"]["manifest"]
            # check if url is not widevine dash type...
            if item.get("drm", "None") != "CENC" or item.get("streamingTechnology", "None") != "DASH" or item.get("url", "None").__contains__(".ism") or item.get("url", "None").__contains__(".m3u8"):
                return self.audioVideoUrls()

            cdn = item["cdn"]
            duration = item["duration"]
            manifest_url = item["url"]
            manifest_full = self.basempd(item["url"])
            if not data.get(cdn,  None):
                data[cdn] = {
                    "cdn": cdn,
                    "duration": duration,
                    "manifest_url": manifest_url,
                    "manifest_full": manifest_full,
                    "recommended": True if item["cdn"] == recommended else False,
                }

        for _, value in data.items():
            if value["recommended"] is True:
                base = dict({
                    "cdn": value["cdn"],
                    "duration": duration,
                    "manifest_url": value["manifest_url"],
                    "manifest_full": value["manifest_full"],
                    "recommended": value["recommended"],
                    "manifest_cdns": data,
                })

                return base

        return dict({
            "cdn": None,
            "duration": None,
            "manifest_url": None,
            "manifest_full": None,
            "recommended": None,
            "manifest_cdns": data,
        })

    def metadata(self):
        if not self.data.get("catalogMetadata", None):
            return {}

        catalog = self.data["catalogMetadata"]["catalog"]
        Type = catalog["type"]

        if Type == "EPISODE":
            ShowTitle = self.data["catalogMetadata"]["family"]["tvAncestors"][1]["catalog"]["title"]
            SeasonNumber = int(self.data["catalogMetadata"]["family"]["tvAncestors"][0]["catalog"]["seasonNumber"])
            EpisodeNumber = int(catalog["episodeNumber"])
            Title = catalog["title"]
            Asin = catalog["id"]
            return {
                "Asin": Asin,
                "EpisodeNumber": EpisodeNumber,
                "SeasonNumber": SeasonNumber,
                "Title": Title,
                "ShowTitle": ShowTitle,
                "Year": None,
                "Type": Type,
                "Bonus": True if EpisodeNumber == 0 else False
            }

        elif Type == "MOVIE":
            ShowTitle = catalog["title"]
            Asin = catalog["id"]
            return {
                "Type": Type,
                "Asin": Asin,
                "Title": ShowTitle,
                "Year": None,
            }
        else:
            raise ValueError("Unknown Type: {}".format(Type))

        return {}

    def license_url(self, url, params):
        params.update({"desiredResources": "Widevine2License"})
        return str("{}?{}".format(url, urllib.parse.urlencode(params)))

    def Parser(self, url, params, data, profile, chapters, region, license_headers, client, cert, audio_only=False):
        self.data = data
        parsered_data = dict()
        parsered_data["manifest"] = self.playback()
        parsered_data["metadata"] = self.metadata()
        parsered_data["subtitles"] = {"forced": self.data.get("forcedNarratives"), "normal": self.data.get("subtitleUrls")}
        parsered_data["default_audio"] = self.data.get("audioVideoUrls", {}).get("defaultAudioTrackId", None)
        parsered_data["profile"] = profile
        parsered_data["chapters"] = chapters
        parsered_data["client"] = client
        parsered_data["cert"] = cert
        parsered_data["audio_only"] = audio_only
        parsered_data["region"] = region
        parsered_data["license_url"] = self.license_url(url, params)
        parsered_data["license_headers"] = license_headers
        return parsered_data

class Utils:
    def __init__(self,):
        """PRIME UTILS"""
        
    def CookieJar(self, filepath):
        try:
            cookies = MozillaCookieJar(filepath)
            cookies.load()
        except Exception:
            raise ValueError("Invalid cookies file (netscape format)")

        return self.addCookies(cookies)

    def addCookies(self, cookies):
        """
        add language for cookies
        @param: cookies -> http.cookiejar.MozillaCookieJar(<cookies file path>)
        """
        HeadersCookies = []
        for cookie in cookies:
            name = cookie.name
            value = urllib.parse.unquote(html.unescape(cookie.value))
            cookie = "{}={}".format(name, value)
            if re.search(_COOKIES_REGEX, cookie):
                cookie = re.sub(r"=(.+)", "={}".format(_LANGUAGE), cookie)

            HeadersCookies.append(cookie)

        return "; ".join(HeadersCookies)


def _language_fixer(lang):
    lang = lang.lower()
    lang = lang.split("_")[0]
    lang = (
        lang.replace("es-es", "es")
        .replace("en-es", "es")
        .replace("kn-in", "kn")
        .replace("gu-in", "gu")
        .replace("ja-jp", "ja")
        .replace("mni-in", "mni")
        .replace("si-in", "si")
        .replace("as-in", "as")
        .replace("ml-in", "ml")
        .replace("sv-se", "sv")
        .replace("hy-hy", "hy")
        .replace("sv-sv", "sv")
        .replace("da-da", "da")
        .replace("fi-fi", "fi")
        .replace("nb-nb", "nb")
        .replace("is-is", "is")
        .replace("uk-uk", "uk")
        .replace("hu-hu", "hu")
        .replace("bg-bg", "bg")
        .replace("hr-hr", "hr")
        .replace("lt-lt", "lt")
        .replace("et-et", "et")
        .replace("el-el", "el")
        .replace("he-he", "he")
        .replace("ar-ar", "ar")
        .replace("fa-fa", "fa")
        .replace("ro-ro", "ro")
        .replace("sr-sr", "sr")
        .replace("cs-cs", "cs")
        .replace("sk-sk", "sk")
        .replace("mk-mk", "mk")
        .replace("hi-hi", "hi")
        .replace("bn-bn", "bn")
        .replace("ur-ur", "ur")
        .replace("pa-pa", "pa")
        .replace("ta-ta", "ta")
        .replace("te-te", "te")
        .replace("mr-mr", "mr")
        .replace("kn-kn", "kn")
        .replace("gu-gu", "gu")
        .replace("ml-ml", "ml")
        .replace("si-si", "si")
        .replace("as-as", "as")
        .replace("mni-mni", "mni")
        .replace("tl-tl", "tl")
        .replace("id-id", "id")
        .replace("ms-ms", "ms")
        .replace("vi-vi", "vi")
        .replace("th-th", "th")
        .replace("km-km", "km")
        .replace("ko-ko", "ko")
        .replace("zh-zh", "zh")
        .replace("ja-ja", "ja")
        .replace("ru-ru", "ru")
        .replace("tr-tr", "tr")
        .replace("it-it", "it")
        .replace("es-mx", "es-la")
        .replace("ar-sa", "ar")
        .replace("zh-cn", "zh")
        .replace("nl-nl", "nl")
        .replace("pl-pl", "pl")
        .replace("pt-pt", "pt")
        .replace("hi-in", "hi")
        .replace("mr-in", "mr")
        .replace("bn-in", "bn")
        .replace("te-in", "te")
        .replace("cmn-hans", "zh-hans")
        .replace("cmn-cn", "zh")
        .replace("cmn-hant", "zh-hant")
        .replace("ko-kr", "ko")
        .replace("en-au", "en")
        .replace("es-419", "es-la")
        .replace("es-us", "es-la")
        .replace("en-us", "en")
        .replace("en-gb", "en")
        .replace("fr-fr", "fr")
        .replace("de-de", "de")
        .replace("las-419", "es-la")
        .replace("ar-ae", "ar")
        .replace("da-dk", "da")
        .replace("yue-hant", "yue")
        .replace("bn-in", "bn")
        .replace("ur-in", "ur")
        .replace("ta-in", "ta")
        .replace("sl-si", "sl")
        .replace("cs-cz", "cs")
        .replace("hi-jp", "hi")
        .replace("-001", "")
        .replace("en-US", "en")
        .replace("deu", "de")
        .replace("eng", "en")
        .replace("ca-es", "cat")
        .replace("fil-ph", "fil")
        .replace("en-ca", "en")
        .replace("eu-es", "eu")
        .replace("ar-eg", "ar")
        .replace("he-il", "he")
        .replace("el-gr", "he")
        .replace("nb-no", "nb")
        .replace("es-ar", "es-la")
        .replace("en-ph", "en")
        .replace("sq-al", "sq")
        .replace("bs-ba", "bs")
        .replace("ms-my", "ms")
        .replace("cmn-tw", "zh-tw")
    )
    
    return lang
