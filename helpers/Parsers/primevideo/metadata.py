import html
import json
import re
import urllib.parse
from urllib.parse import urljoin

import requests
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup as Soup
from bs4 import Tag

from helpers.Parsers.primevideo.utils import _LANGUAGE

#@Region
_DE = r".amazon.de"
_UK = r".amazon.co.uk"
_US = r".amazon.com"
_JP = r".amazon.co.jp"
_PV = r".primevideo.com"

#@ExtractUrlAsin
_REF = r"/ref.+"
_URL_ASIN = re.compile(r"/detail/(.+)|/([A-Z0-9]+)")

#@requests
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
HTML_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'upgrade-insecure-requests': '1',
    'user-agent': UA,
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'same-origin',
    'sec-fetch-dest': 'empty',
    'accept-language': 'en,en-US;q=0.9',
    'cookie': '',
}

#@addCookies
_COOKIES_REGEX = r"(lc-.+)=([a-z]{2}_[A-Z]{2})"

#@ExtractUrlCanonical
_canonical = r'rel="canonical" href="(.+?)"'

#@
_REGION_REGEX = re.compile(r'ue_furl *= *([\'"])fls-(na|eu|fe)\.amazon\.[a-z.]+\1')

class metadata:
    def __init__(self):
        """CLASS FOR AMZN HTML PARSING"""
        self.session = requests.Session()
        self.headers = HTML_HEADERS

    def AccountRegion(self, Url):
        
        r = self.session.get(url=Url, headers=self.headers, allow_redirects=False)

        while r.headers.__contains__("location"):
            Url = r.headers["location"]
            r = self.session.get(url=Url, headers=self.headers, allow_redirects=False)

        if not _REGION_REGEX.search(r.content.decode("utf-8")):
            print("Cannot find AccountRegion")

        return _REGION_REGEX.search(r.content.decode("utf-8")).group(2)

    def Region(self, Url):
        """Detect Region From Url"""
        if urllib.parse.urlparse(Url).netloc.endswith(_DE):
            return "de"
        elif urllib.parse.urlparse(Url).netloc.endswith(_UK):
            return "uk"
        elif urllib.parse.urlparse(Url).netloc.endswith(_US):
            return "us"
        elif urllib.parse.urlparse(Url).netloc.endswith(_JP):
            return "jp"
        elif urllib.parse.urlparse(Url).netloc.endswith(_PV):
            return "ps"
        else:
            raise ValueError(
                f"Input does not appear to be an amazon/primevideo Url: {Url}"
            )

        return

    def NoReference(self, Url):
        """NoReference From Url"""
        return re.sub(_REF, "", Url)

    def addCookies(self, cookie):
        self.headers.update({"cookie": cookie})
        return 

    def addLanguage(self, Url):
        """set language for Url metadta html response"""
        return '{}?language={}'.format(Url, _LANGUAGE)

    def ExtractUrlCanonical(self, soup, html):
        """ExtractUrlCanonical From Url"""
        if soup.find("link", rel="canonical"):
            return soup.find("link", rel="canonical").get("href")

        if re.search(_canonical, html):
            return re.search(_canonical, html).group(1)

        return None

    def getTextTemplates(self, soup):
        templates = []
        for template in soup.find_all("script", type="text/template"):
            for js in template.contents:
                templates.append({"text/template": json.loads(js)})

        # for template in soup.find_all("script", type="text/template"):
        #     templates.append({"text/template": json.loads(template.text)})

        return templates

    def GetBaseUrl(self, Url):
        Url = urlsplit(Url)
        return f"{Url.scheme}://{Url.netloc}"

    def RequestHtml(self, Url):
        global BaseUrl
        Url = self.NoReference(Url)
        Region = self.Region(Url)
        AccountRegion = Region

        if Region == "ps" and len(self.headers["cookie"]) > 0:
            AccountRegion = self.AccountRegion(Url)

        response = self.session.get(url=Url, headers=self.headers)
        html = response.content.decode("utf-8")
        soup = Soup(html, "lxml-html")

        if self.ExtractUrlCanonical(soup, html):
            Url = self.ExtractUrlCanonical(soup, html)
            response = self.session.get(url=Url, headers=self.headers)
            html = response.content.decode("utf-8")
            soup = Soup(html, "lxml-html")

        BaseUrl, Url = self.GetBaseUrl(Url), self.addLanguage(Url)
        TextTemplates = self.getTextTemplates(soup)
        ParentTitle = self.GetParentTitle(TextTemplates)
        seasonsList, CurrentSeason = self.GetSeasons(TextTemplates, Url)
        episodesList = self.GetEpisodes(TextTemplates, CurrentSeason, ParentTitle)

        if not episodesList == []:
            return {
                "Region": Region,
                "AccountRegion": AccountRegion,
                "Type": "SHOW",
                "Seasons": sorted(seasonsList, key=lambda k: int(k["SeasonNumber"])),
                "Episodes": sorted(episodesList, key=lambda k: int(k["EpisodeNumber"])),
                "CurrentSeason": CurrentSeason,
            }

        ASIN, YEAR, TITLE = self.DetectMovie(TextTemplates)

        if [x for x in (ASIN, YEAR, TITLE) if x is None]:
            return {
                "Error": "Parser Failed",
                "TextTemplates": TextTemplates,
                "status_code": response.status_code,
            }

        return {
            "Region": Region,
            "AccountRegion": AccountRegion,
            "Type": "MOVIE",
            "Asin": ASIN,
            "Title": TITLE,
            "Year": YEAR,
        }

    def DetectMovie(self, TextTemplates):
        ASIN = YEAR = TITLE = None

        for template in TextTemplates:
            try:
                state = template["text/template"]["props"]["state"]
                pageTitleId = state["pageTitleId"]
                headerDetail = state["detail"]["headerDetail"][pageTitleId]
                if headerDetail["titleType"] == "movie": 
                    ASIN = pageTitleId
                    YEAR = headerDetail["releaseYear"]
                    TITLE = html.unescape(headerDetail["title"])
            except KeyError:
                pass

        return ASIN, YEAR, TITLE

    def GetParentTitle(self, TextTemplates):
        for template in TextTemplates:
            try:
                detail = template["text/template"]["props"]["state"]["detail"]["detail"]
            except KeyError:
                continue

            for _, value in detail.items():
                if value["titleType"] == "season":
                    if int(value["seasonNumber"]) >= 0: # just checking if @key: seasonNumber is exist.
                        return html.unescape(value["parentTitle"])

        return None

    def GetEpisodes(self, TextTemplates, CurrentSeason, ParentTitle):
        episodesList = []

        for template in TextTemplates:
            try:
                detail = template["text/template"]["props"]["state"]["detail"]["detail"]
            except KeyError:
                continue

            for Asin, episode in detail.items():
                if episode["titleType"] == "episode":
                    if int(episode["episodeNumber"]) >= 0:
                        Type = "EPISODE"
                        Asin = Asin
                        EpisodeNumber = int(episode["episodeNumber"])
                        SeasonNumber = CurrentSeason
                        Title = html.unescape(episode["title"])
                        ShowTitle = ParentTitle
                        Year = episode.get("releaseYear")

                        episodesList.append(
                            {
                                "Asin": Asin,
                                "EpisodeNumber": EpisodeNumber,
                                "SeasonNumber": SeasonNumber,
                                "Title": Title,
                                "ShowTitle": ShowTitle,
                                "Year": Year,
                                "Type": Type,
                                "Bonus": True if EpisodeNumber == 0 else False
                            }
                        )

            if episodesList != []:
                return episodesList

        return episodesList

    def GetSeasons(self, TextTemplates, Url):
        seasonsList = []
        added = set()
        CurrentSeason = None

        for template in TextTemplates:
            try:
                for _, value in template["text/template"]["props"]["state"]["self"].items():
                    if value["titleType"] == "season":
                        SeasonNumber = self.SeaonNumberFixer(value["sequenceNumber"])
                        SeasonUrl = value["link"]
                        compactGTI = value["compactGTI"]
                        seasonASIN = value["gti"]

                        if Url.__contains__(SeasonUrl):
                            CurrentSeason = SeasonNumber

                        if not SeasonUrl in added:
                            added.add(SeasonUrl)
                            seasonsList.append(
                                {
                                    "SeasonNumber": SeasonNumber,
                                    "compactGTI": compactGTI,
                                    "seasonASIN": seasonASIN,
                                    "Url": self.NoReference(urljoin(BaseUrl, SeasonUrl)),
                                    "Type": "SEASON",
                                }
                            )

                break
            except Exception:
                pass

        if not CurrentSeason:
            CurrentSeason = self.GetCurrentSeason(TextTemplates)

        return seasonsList, CurrentSeason

    def SeaonNumberFixer(self, number):
        _REGEX = r"(\d0\d)"
        _RESUB = r"(0\d)"

        if re.search(_REGEX, str(number)):
            number = re.sub(_RESUB, "", str(number))

        return int(number)

    def GetCurrentSeason(self, TextTemplates):
        Id = None
        CurrentSeason = None

        for template in TextTemplates:
            try:
                Id = template["text/template"]["props"]["state"]["pageTitleId"]
            except KeyError:
                pass

        if Id:
            for template in TextTemplates:
                try:
                    CurrentSeason = self.SeaonNumberFixer(template["text/template"]["props"]["state"]["detail"]["detail"][Id]["seasonNumber"])
                    return CurrentSeason
                except Exception:
                    pass

        return CurrentSeason
