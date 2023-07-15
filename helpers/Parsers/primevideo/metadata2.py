import html
import json
import os
import re
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

session = requests.Session()
getDetailPage = "https://{netloc}/gp/video/api/getDetailPage"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"

def get_region(url, cookie) -> str:
    netloc = urlparse(url).netloc
    r = "none"
    if netloc.__contains__("amazon.de"): r = "de"
    if netloc.__contains__("amazon.co.uk"): r = "uk"
    if netloc.__contains__("amazon.com"): r = "us"
    if netloc.__contains__("amazon.co.jp"): r = "jp"
    if netloc.__contains__("primevideo.com"): r = "ps"
    if r != "ps": return r

    response = session.get("https://www.primevideo.com", headers={"user-agent": UA, "cookie": cookie})
    match = re.search(r'ue_furl *= *([\'"])fls-(na|eu|fe)\.amazon\.[a-z.]+\1', response.text)
    if not match:
        print("Failed to get PrimeVideo Region")
    region = match.group(2).lower()
    return region
    # _REGION_REGEX = re.compile(r'ue_furl *= *([\'"])fls-(na|eu|fe)\.amazon\.[a-z.]+\1')
    # headers = {
    #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    #     'upgrade-insecure-requests': '1',
    #     'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    #     'sec-fetch-site': 'same-origin',
    #     'sec-fetch-mode': 'same-origin',
    #     'sec-fetch-dest': 'empty',
    #     'accept-language': 'en,en-US;q=0.9',
    #     'cookie': cookie,
    # }

    # response = session.get(url=url, headers=headers, allow_redirects=False)
    # while response.headers.__contains__("location"):
    #     url = response.headers["location"]
    #     response = session.get(url=url, headers=headers, allow_redirects=False)

    # if not (psr := _REGION_REGEX.search(response.content.decode("utf-8"))):
    #     print("Cannot find primevideo region from cookies")

    # return psr.group(2) if psr else "eu"

def correct_season_n(season_n: str):
    if re.search(r"(\d0\d)", str(season_n)):
        return int(re.sub(r"(0\d)", "", str(season_n)))

    return int(season_n)

def get_title_id(url: str) -> str:
    if (_id := [i for i in urlparse(url).path.split("/") if i.isupper()]):
        return _id[0]
    if not (title_id := re.search("[A-Z0-9]+$", re.sub(r"/ref.+", "", urlparse(url).path).removesuffix("/"))):
        raise ValueError("Please make sure url end with asin (UPPER CASE WORDS AND DIGITS)")
    return title_id.group()

def get_metadata_seasons(url: str, data: str) -> List[Dict[str, Any]]:
    try:
        seasons = [{"title_id": get_title_id(item.get("link")), "season_number": correct_season_n(item.get("sequenceNumber")
            )} for temp in [data for data in [json.loads(text.encode("utf-8"
                ).decode("ascii", "ignore")
                ) for script in BeautifulSoup(data, "lxml-html"
                ).find_all("script", type="text/template"
                ) for text in script.contents] if data.get("props", {}).get("state"
                )] for _, item in temp.get("props", {}).get("state", {}).get("self", []
                ).items() if item.get("titleType") == "season"]
        if seasons: return seasons
        return [{"title_id": get_title_id(url), "season_number": 0}]
    except Exception:
        return [{"title_id": get_title_id(url), "season_number": 0}]

def metadata_parser(data: Dict[str, Any]) -> Dict[str, Any]:

    if (_type := data[0]["widgets"]["productDetails"]["detail"]["titleType"]) == "movie":
        data, = data
        return {
            "type": _type,
            "asin": data["widgets"]["productDetails"]["detail"]["catalogId"],
            "title": html.unescape(data["widgets"]["productDetails"]["detail"]["title"]),
            "year": int(data["widgets"]["productDetails"]["detail"]["releaseYear"])}

    if _type == "season":
        episodes = []
        for _data in data:
            # print(_data["widgets"]["titleContent"])
            episodes_cards = [x for x in _data["widgets"]["titleContent"] if x["collectionType"] == "Episodes"]
            if not episodes_cards:
                continue
            # print(len(episodes_cards))
            episodes_cards = episodes_cards[0]["cards"]
            # # ["cards"]
            episodes += [{
                "asin": episode["detail"]["catalogId"],
                "tv_title": html.unescape(_data["widgets"]["productDetails"]["detail"]["parentTitle"]),
                "title": html.unescape(episode["detail"]["title"]),
                "season_number": correct_season_n(_data["widgets"]["productDetails"]["detail"]["seasonNumber"]),
                "episode_number": int(episode["detail"]["episodeNumber"])
            } for episode in episodes_cards]
        episodes = sorted(episodes, key=lambda episode: (episode["season_number"], episode["episode_number"]))

        return {"type": "tv_show", "episodes": episodes}

def get_metadata(url: str, cookie: str):
    region = get_region(url, cookie)
    response = session.get(url, headers={"user-agent": UA, "cookie": cookie})
    seasons = get_metadata_seasons(url, response.content.decode("utf-8"))
    data = []

    for season in seasons:
        title_id = season.get("title_id")
        # season_number = season.get("season_number")
        if os.path.isfile((cached := f"{title_id}.json")):
            data.append(json.load(open(cached)))
            continue

        print("Getting Movie or Season metadata ID = %s" % title_id)
        response = session.get(
                getDetailPage.format(netloc=urlparse(url).netloc),
                headers={
                    "authority": urlparse(url).netloc,
                    "user-agent": UA,
                    "x-requested-with": "XMLHttpRequest",
                    "cookie": cookie},
                params={
                    "titleID": title_id,
                    "isElcano": "0",
                    "sections": "Btf"})
        if response.status_code != 200:
            raise ValueError("%d Unauthorized, cookies is invalid" % response.status_code)

        _data = response.json()
        data.append(_data)
        with open(cached, "w") as c:
            json.dump(_data, c, indent=4, sort_keys=True)

    return {
        "region": region,
        **metadata_parser(data)
    }
