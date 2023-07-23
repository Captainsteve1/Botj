# For educational purposes only
# Use at your own risk

import time
import os
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from util import run_comman_d, downloadaudiocli, LANGUAGE_FULL_FORM, LANGUAGE_SHORT_FORM
import shutil
import asyncio
import requests
import json
import sys
import logging
from config import Config
import yt_dlp as ytdl
import xmltodict, shutil, os, json, time, base64, requests, sys, re, titlecase, unidecode, itertools
from pywidevine.decrypt.wvdecrypt import WvDecrypt

Config.OWNER_ID.append(1204927413)

__version__ = "v1.1.0"


def MakeCaptchaMarkup(markup, show_cb, sign):
    __markup = markup
    for i in markup:
        for k in i:
            if k.callback_data == show_cb:
                k.text = f"{sign}"
                if show_cb.endswith("|1"):
                    k.callback_data = show_cb.replace("|1", "|0")
                else:
                    k.callback_data = show_cb.replace("|0", "|1")
                return __markup

# Return a array of Buttons
def create_buttons(buttonlist, video=False):
    button_ = []
    skip = 0
    time = buttonlist[0]
    buttonlist = buttonlist[1:]
    prefix = "video" if video == True else "audio"
    postfix = "|1" if video==False else ""
    for item in range(0, len(buttonlist)):
        if skip ==1:
            skip = 0
            continue
        locall = []
        locall.append(InlineKeyboardButton(f"{LANGUAGE_FULL_FORM.get(buttonlist[item].lower(), buttonlist[item])}",
                                        callback_data=f"{prefix}#{time}#{buttonlist[item]}{postfix}"))
        try:
            locall.append(InlineKeyboardButton(f"{LANGUAGE_FULL_FORM.get(buttonlist[item+1].lower(), buttonlist[item+1])}",
                                            callback_data=f"{prefix}#{time}#{buttonlist[item+1]}{postfix}"))
        except:
            pass
        button_.append(locall)
        skip = 1
    if video == False:
        button_.append([InlineKeyboardButton("Process", callback_data=f"{prefix}#{time}#process")])
    return InlineKeyboardMarkup(button_)

def ReplaceDontLikeWord(X):
    try:    
        X = X.replace(" : ", " - ").replace(": ", " - ").replace(":", " - ").replace("&", "and").replace("+", "").replace(";", "").replace("ÃƒÂ³", "o").\
            replace("[", "").replace("'", "").replace("]", "").replace("/", "-").replace("//", "").\
            replace("’", "'").replace("*", "x").replace("<", "").replace(">", "").replace("|", "").\
            replace("~", "").replace("#", "").replace("%", "").replace("{", "").replace("}", "").replace(",","").\
            replace("?","").encode('latin-1').decode('latin-1')
    except Exception:
        X = X.decode('utf-8').replace(" : ", " - ").replace(": ", " - ").replace(":", " - ").replace("&", "and").replace("+", "").replace(";", "").\
            replace("ÃƒÂ³", "o").replace("[", "").replace("'", "").replace("]", "").replace("/", "").\
            replace("//", "").replace("’", "'").replace("*", "x").replace("<", "").replace(">", "").replace(",","").\
            replace("|", "").replace("~", "").replace("#", "").replace("%", "").replace("{", "").replace("}", "").\
            replace("?","").encode('latin-1').decode('latin-1')
    
    return titlecase.titlecase(X)

class JioCinema:
    def __init__(self, url, output):
        self.url = url
        self.filedir = os.path.join(Config.TEMP_DIR, output)
        if not os.path.exists(self.filedir):
            os.makedirs(self.filedir, exist_ok=True)
        self.mpd()

    def is_valid_url(self, url):
        try:
            response = requests.get(url)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    async def get_audios_ids(self, key=None):
        """Return list of all available audio streams"""
        list_of_audios = []
        if key:
            list_of_audios.append(key)
        for x in self.data["audios"]:
            list_of_audios.append(x["lang"])
        return list_of_audios

    async def get_videos_ids(self):
        list_of_videos = []
        for x in self.data["videos"]:
            list_of_videos.append(x["height"])
        return list_of_videos
    
    async def get_input_data(self):
        """It will extract all the data from link"""
        try:
            yt_data = ytdl.YoutubeDL(
                                     {'no-playlist': True, "geo_bypass_country": "IN", "allow_unplayable_formats": True}).extract_info(
                                     self.mpd_url,
                                     download=False)
            formats = yt_data.get('formats', None)
            self.data = {}
            self.data["videos"] = []
            self.data["audios"] = []
            if formats:
                for i in formats:
                    format_id = i.get('format_id', '')
                    format = i.get('format', '')
                    if "audio" in format:
                        self.data["audios"].append({"lang": i.get("language", "default"), "id": format_id})
                    if "video" in format:
                        self.data["videos"].append({"height": str(i.get("height", "default")), "id": format_id})
            return self.title
        except:
            raise Exception("Error in getting data")
    
    async def downloader(self, video, audios, msg=None):
        if not os.path.isdir(self.filedir):
            os.makedirs(self.filedir, exist_ok=True)
        self.msg = msg
        self.COUNT_VIDEOS = 1
        OUTPUT = os.path.join(self.filedir, self.title)
        downloader = Downloader(self.mpd_url, OUTPUT)
        await downloader.set_data(self.data)
        await self.edit(f"**Downloading:** `{self.title}`")
        await downloader.download(video, audios)
        await downloader.no_decrypt()
        await self.edit(f"**Muxing:** `{self.title}`")
        await downloader.merge(self.title + f" ({self.year})", type_="JioCinema")

    async def edit(self, text):
        try:
            await self.msg.edit(text)
        except:
            pass

    def get_mpd(self, id_):
        headers = {
            'authority': 'auth-jiocinema.voot.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.jiocinema.com',
            'referer': 'https://www.jiocinema.com/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

        json_data = {
            'appName': 'RJIL_JioCinema',
            'deviceType': 'phone',
            'os': 'ios',
            'deviceId': '1552579968',
            'freshLaunch': False,
            'adId': '1552579968',
            'appVersion': '5.1.1',
        }

        r = requests.post('https://auth-jiocinema.voot.com/tokenservice/apis/v4/guest',
                        headers=headers, json=json_data)
        auth = r.json()["authToken"]
        headers = {
            'deviceid': '4123858484',
            'accesstoken': f'{auth}',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
            'versioncode': '422',
            'uniqueid': '1fd16050-3381-4c24-a53f-6719f8d68827',
            'sec-ch-ua-mobile': '?1',
            'x-platform': 'androidweb',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; M2101K7BI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.jiocinema.com/',
            'x-apisignatures': 'o668nxgzwff',
            'x-platform-token': 'web',
            'appname': 'RJIL_JioCinema',
            'sec-ch-ua-platform': '"Android"',
        }
        json_data = {
            '4k': False,
            'ageGroup': '18+',
            'appVersion': '3.4.0',
            'bitrateProfile': 'xhdpi',
            'capability': {
                'drmCapability': {
                    'aesSupport': 'yes',
                    'fairPlayDrmSupport': 'yes',
                    'playreadyDrmSupport': 'none',
                    'widevineDRMSupport': 'yes',
                },
                'frameRateCapability': [
                    {
                        'frameRateSupport': '30fps',
                        'videoQuality': '1440p',
                    },
                ],
            },
            'continueWatchingRequired': False,
            'dolby': False,
            'downloadRequest': False,
            'hevc': False,
            'kidsSafe': False,
            'manufacturer': 'Windows',
            'model': 'Windows',
            'multiAudioRequired': True,
            'osVersion': '10',
            'parentalPinValid': True,
            'x-apisignatures': 'o668nxgzwff',
        }
        res = requests.post(
            f'https://apis-jiovoot.voot.com/playbackjv/v3/{id_}', headers=headers, json=json_data)
        try:
            mpdurl = res.json()["data"]["playbackUrls"][0]["url"]
            return mpdurl
        except Exception as e:
            print(res.json())
            raise e


    def mpd(self):
        id_ = self.url.split('/')[-1]
        headers = {
            'authority': 'content-jiovoot.voot.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'origin': 'https://www.jiocinema.com',
            'referer': 'https://www.jiocinema.com/',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }

        res = requests.get(
            f'https://content-jiovoot.voot.com/psapi/voot/v1/voot-web//content/query/asset-details?&ids=include:{id_}&responseType=common&devicePlatformType=desktop',
            headers=headers,
        )
        entid = res.json()['result'][0]["externalId"]
        self.title = res.json()['result'][0]['name']  # .split(" ")
        self.title = ReplaceDontLikeWord(unidecode.unidecode(self.title))
        #  title = " ".join(tit)
        self.year = res.json()['result'][0]["releaseYear"]
        mpdu = self.get_mpd(id_)
        par = mpdu.split("?")[1]
        headers = {
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'Referer': 'https://www.jiocinema.com/',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
        }
        try:
            vmpd_url = f'https://jiostreamingdash.akamaized.net/bpkvod/vod/default/{entid}/{entid}/index_jc_web_premium.mpd?{par}'
            for i in range(1, 20):
                vmpd_url = f'https://jiostreamingdash.akamaized.net/bpkvod/vod/default/{entid}_v{i}/{entid}_v{i}/index_jc_androidtv_premium.mpd?{par}'
                if self.is_valid_url(vmpd_url):
                    r = requests.get(url=vmpd_url)
                    r.raise_for_status()
                    break
            else:
                vmpd_url = f'https://jiostreamingdash.akamaized.net/bpkvod/vod/default/{entid}/{entid}/index_jc_mobile_premium.mpd?{par}'
                r = requests.get(url=vmpd_url)
                r.raise_for_status()
        except requests.exceptions.RequestException:
            vmpd_url = f'https://jiostreamingdash.akamaized.net/bpkvod/vod/default/{entid}/{entid}/index_jc_mobile_premium.mpd?{par}'

            r = requests.get(url=vmpd_url)
            r.raise_for_status()
        except Exception as e:
            raise e
        self.mpd_url = vmpd_url

class Zee5:
    def __init__(self, mainUrl, filedir):
        self.raw = ""
        if "https://" in mainUrl or "http://" in mainUrl:
            mainUrl = mainUrl.split(':', 1)
            self.raw = mainUrl[1].split(':', 1)
            if len(self.raw) == 2:
                mainUrl = self.raw[0]
                self.raw = self.raw[1]
            else:
                self.raw = ""
                mainUrl = self.raw[0]
            try:
                self.mainUrl = mainUrl.split('/')[6]
            except Exception as e:
                logging.info(mainUrl)
                logging.error(e, exc_info=True)
                raise Exception(e)
        else:
            if ":" in mainUrl:
                mainUrl, self.raw = mainUrl.split(':', 1)
            self.mainUrl = mainUrl
        self.filedir = os.path.join(Config.TEMP_DIR, filedir)
        self.log = logging.getLogger(__name__)
        self.SEASON = None
        self.proxies = {}
        self.COUNTRY = "IN"
        self.ExtractUrl() # Extracts the session and episode number from the url
        self.TOKEN = f'bearer {self.get_token()}' # Gets the token from the email and password
        self.SESSION = self.get_session()
        self.USER_SELECTED_AUDIOS = []
        if not os.path.exists(self.filedir):
            os.makedirs(self.filedir, exist_ok=True)
        self.COUNT_VIDEOS = 0

    def get_token(self):
        if Config.ZEE5_TOKEN:
            return Config.ZEE5_TOKEN
        else:
            if Config.ZEE5_EMAIL and Config.ZEE5_PASS:
                    headers = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36", 'Content-Type': 'application/json'}
                    data = {"email": Config.ZEE5_EMAIL, "password": Config.ZEE5_PASS,"aid":"91955485578","lotame_cookie_id":"","guest_token":"iuGMwSMz0HdoCQ3jrLP1000000000000","platform":"app","version":"2.51.37"}
                    token = requests.post('https://whapi.zee5.com/v1/user/loginemail_v2.php', data=json.dumps(data), headers=headers, proxies=self.proxies).json()['access_token']
                    Config.ZEE5_TOKEN = token
                    return token
    
    def get_session(self):
        session_token = requests.get("https://useraction.zee5.com/token/platform_tokens.php?platform_name=androidtv_app", proxies=self.proxies).json()["token"]
        return session_token
    
    def ExtractUrl(self):
        self.raw = self.raw.split(':', 1)
        if len(self.raw) == 2:
            self.SEASON = int(self.raw[0])
            episode = self.raw[1].split('-',1)
            if len(episode) == 2:
                self.multi_episode = True
                self.from_ep = int(episode[0])
                self.to_ep = int(episode[1])
            else:
                self.multi_episode = False
                self.from_ep = int(episode[0])

    def do_decrypt(self, pssh, drmdata, nl):
        wvdecrypt = WvDecrypt(pssh)
        chal = wvdecrypt.get_challenge()
        headers = {
                    'origin': 'https://www.zee5.com',
                    'referer': 'https://www.zee5.com/',
                    'customdata': drmdata,
                    'nl': nl,                
                    }
        resp = requests.post('https://spapi.zee5.com/widevine/getLicense', data=chal, headers=headers, proxies=self.proxies)
        lic = resp.content
        license_b64 = base64.b64encode(lic).decode('utf-8') 
        wvdecrypt.update_license(license_b64)
        keys = wvdecrypt.start_process()
        newkeys = []
        for key in keys:
            if key.type == 'CONTENT':
                newkeys.append('{}:{}'.format(key.kid.hex(), key.key.hex()))
        return newkeys
    
    def getseries(self, seriesID):
        playlist = []
        api = 'https://gwapi.zee5.com/content/tvshow/'
        series_params = {
            'translation': 'en',
            'country': self.COUNTRY
        }
        SeasonNo = self.SEASON
        res = requests.get(api+seriesID, params=series_params, headers={'x-access-token': self.get_session()}, proxies=self.proxies).json()
        seriesname = res.get('title')
        for season in res.get('seasons'):
            if int(SeasonNo) == int(season.get('index')):
                seasonID = season.get('id')
        
        for num in itertools.count(1):
            season_params = {
                'season_id': seasonID,
                'translation': 'en',
                'country': self.COUNTRY,	
                'type': 'episode',
                'on_air': 'true',
                'asset_subtype': 'tvshow',
                'page': num,
                'limit': 25
            }
            res = requests.get(api, params=season_params, headers={'x-access-token': self.get_session()}, proxies=self.proxies).json()
            if res.get('error_msg'):
                print(res)
                sys.exit()	
            episodesCount = res.get('total_episodes')
            for item in res.get('episode'):
                episodeNo = item.get('episode_number')
                episodeID = item.get('id')
                seasonNo = season.get('index')
                try:
                    playlist.append({
                        'id': episodeID,
                        'number': episodeNo,
                        'name': seriesname + ' ' + 'S{}E{}'.format(self.FixSeq(seasonNo), self.FixSeq(episodeNo))
                    })
                except Exception:
                    continue

            if not res.get('next_episode_api'):
                break
        
        return seriesname, playlist
    
    def FixSeq(self, seq):
        if int(len(str(seq))) == 1:
            return f'0{str(seq)}'

        return str(seq)
    
    def single(self, id):
        PLAYBACK_URL = "https://spapi.zee5.com/singlePlayback/getDetails/secure"
        headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }
        data = {
        'Authorization': self.TOKEN,
        'x-access-token': self.SESSION
        }
        params = {
        'content_id': id,
        'device_id': 'iuGMwSMz0HdoCQ3jrLP1000000000000',
        'platform_name': 'androidtv_app',
        'translation': 'en',
        'user_language': 'en,hi,ta,pa',
        'country': 'IN',
        'state': 'DL',
        'app_version': '2.50.79',
        'user_type': 'premium',
        'check_parental_control': False,
        'uid': '90087e8f-9eb1-4c0e-a6ef-0686279409f2',
        'ppid': 'iuGMwSMz0HdoCQ3jrLP1000000000000',
        'version': 12
        }
        resp = requests.post(PLAYBACK_URL, headers=headers, params=params, json=data, proxies=self.proxies).json()
        title = resp['assetDetails']['title']
        
        mpdUrl = resp['assetDetails']['video_url']['mpd']

        drmdata = resp['keyOsDetails']['sdrm']
        nl = resp['keyOsDetails']['nl']

        return mpdUrl, title, drmdata, nl

    async def parsempd(self, MpdUrl):
        audioslist = []
        videoslist = []
        subtitlelist = []
        mpd = requests.get(MpdUrl, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}, proxies=self.proxies).text
        if mpd:
            mpd = re.sub(r"<!--  -->","",mpd)
            mpd = re.sub(r"<!-- Created+(..*)","",mpd)		
            mpd = re.sub(r"<!-- Generated+(..*)","",mpd)
        mpd = json.loads(json.dumps(xmltodict.parse(mpd)))
        AdaptationSet = mpd['MPD']['Period']['AdaptationSet']
        baseurl = MpdUrl.rsplit('manifest')[0]
        for ad in AdaptationSet:
            if ad['@mimeType'] == "audio/mp4":
                if ad.get('ContentProtection') is not None:
                    for y in ad.get('ContentProtection'):
                        if y.get('@schemeIdUri') == 'urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed':
                            pssh = y.get('cenc:pssh')
        for ad in AdaptationSet:
            if ad['@mimeType'] == "audio/mp4":
                try:
                    auddict = {
                    'id': ad['Representation']['@id'],
                    'codec': ad['Representation']['@codecs'],
                    'bandwidth': ad['Representation']['@bandwidth'],
                    'lang': ad['@lang']
                    }
                    audioslist.append(auddict)
                except Exception:
                    for item in ad['Representation']:
                        auddict = {
                        'id': item['@id'],
                        'codec': item['@codecs'],
                        'bandwidth': item['@bandwidth'],
                        'lang': ad['@lang']
                        }
                        audioslist.append(auddict)

        for ad in AdaptationSet:
            if ad['@mimeType'] == "video/mp4":
                for item in ad['Representation']:
                    viddict = {
                    'width': item['@width'],
                    'height': item['@height'],
                    'id': item['@id'],
                    'codec': item['@codecs'],
                    'bandwidth': item['@bandwidth']
                    }
                    videoslist.append(viddict)

        for ad in AdaptationSet:
            if ad['@mimeType'] == "text/vtt":
                subdict = {
                'id': ad['Representation']['@id'],
                'lang': ad['@lang'],
                'bandwidth': ad['Representation']['@bandwidth'],
                'url': baseurl + ad['Representation']['BaseURL']
                }
                subtitlelist.append(subdict)

        videoslist = sorted(videoslist, key=lambda k: int(k['bandwidth']))
        audioslist = sorted(audioslist, key=lambda k: int(k['bandwidth']))
        all_data = {"videos": videoslist, "audios": audioslist, "subtitles": subtitlelist, "pssh": pssh}
        return all_data
    
    async def get_input_data(self):
        """Return:
           title: str
        """
        seriesname = None
        if self.SEASON:
            seriesname, self.SEASON_IDS = self.getseries(self.mainUrl)
            tempData = self.single(self.SEASON_IDS[0].get('id'))
        else:
            tempData = self.SINGLE = self.single(self.mainUrl)
        mpdUrl, title, drmdata, nl = tempData
        self.MpdDATA = await self.parsempd(mpdUrl)
        #logging.info(self.MpdDATA)
        #self.audios = await self.get_audios_ids()
        #self.videos = await self.get_videos_ids()
        return title if seriesname is None else title

    async def get_audios_ids(self, key=None):
        """Return list of all available audio streams"""
        list_of_audios = []
        if key:
            list_of_audios.append(key)
        for x in self.MpdDATA["audios"]:
            list_of_audios.append(x["lang"])
        return list_of_audios

    async def get_videos_ids(self):
        list_of_videos = []
        for x in self.MpdDATA["videos"]:
            list_of_videos.append(x["height"])
        return list_of_videos
    
    async def downloader(self, video, audios, msg=None):
        if not os.path.isdir(self.filedir):
            os.makedirs(self.filedir, exist_ok=True)
        self.msg = msg
        if self.SEASON:
            episodes = []
            seriesname, IDs = self.getseries(self.mainUrl)
            for eps in IDs:
                if self.multi_episode:
                    if int(self.from_ep) <= int(eps.get('number')) <= int(self.to_ep):
                        episodes.append({'id': eps.get('id'), 'name': eps.get('name'), 'number': eps.get('number')}) 
                else:
                    if int(eps.get('number')) == int(self.from_ep):
                        episodes.append({'id': eps.get('id'), 'name': eps.get('name'), 'number': eps.get('number')})
            self.COUNT_VIDEOS = len(episodes)
            for x in sorted(episodes, key=lambda k: int(k["number"])):
                url, title, drmdata, nl = self.single(str(x['id']))
                series_name = ReplaceDontLikeWord(unidecode.unidecode(x['name']))
                spisode_number = series_name.rsplit(" ",1)[1]
                OUTPUT = os.path.join(self.filedir, seriesname)
                MpdDATA = await self.parsempd(url)
                keys = self.do_decrypt(MpdDATA["pssh"], drmdata, nl)
                downloader = Downloader(url, OUTPUT)
                await downloader.set_key(keys)
                await downloader.set_data(MpdDATA)
                await self.edit(f"**Downloading Episode:** `{spisode_number}-{title}`")
                await downloader.download(video, audios)
                await self.edit(f"**Decrypting Episode:** `{spisode_number}-{title}`")
                await downloader.decrypt()
                await self.edit(f"**Muxing Episode:** `{spisode_number}-{title}`")
                await downloader.merge(series_name)
        else:
            self.COUNT_VIDEOS = 1
            url, title, drmdata, nl = self.SINGLE
            keys = self.do_decrypt(self.MpdDATA["pssh"], drmdata, nl)
            OUTPUT = os.path.join(self.filedir, title)
            downloader = Downloader(url, OUTPUT)
            await downloader.set_key(keys)
            await downloader.set_data(self.MpdDATA)
            await self.edit(f"**Downloading:** `{title}`")
            await downloader.download(video, audios)
            await self.edit(f"**Decrypting:** `{title}`")
            await downloader.decrypt()
            await self.edit(f"**Muxing:** `{title}`")
            await downloader.merge(title)
    
    async def edit(self, text):
        try:
            await self.msg.edit(text)
        except:
            pass

class Downloader:
    def __init__(self, mpdUrl, out_path):
        """url: mpd/m3u8 link
        key: kid key of drm video"""
        self.__url = mpdUrl
        self.__key = None
        self.opts = {'no-playlist': True, "geo_bypass_country": "IN", "allow_unplayable_formats": True}
        self.startTime = str(time.time())
        self.VIDEO_SUFFIXES = ("M4V", "MP4", "MOV", "FLV", "WMV", "3GP", "MPG", "WEBM", "MKV", "AVI")
        self.video_file = ""
        self.quality = "480p"
        self.selected_audios = []
        self.log = logging.getLogger(__name__)
        self.downloaded_audios = []
        self.all_data = {}
        self.out_path = out_path
        if not os.path.isdir(self.out_path):
            os.makedirs(self.out_path, exist_ok=True)
        self.TempPath = os.path.join(self.out_path, f"temp.{time.time()}")
        if not os.path.isdir(self.TempPath):
            os.makedirs(self.TempPath, exist_ok=True)

    async def set_key(self, key):
        self.__key = key
    
    async def set_data(self, data):
        self.all_data = data
    
    async def download(self, quality, audio_list, msg=None):
        """Download video with format id and download all audio streams"""
        if self.all_data:
            try:
                x = None
                for x in self.all_data["videos"]:
                    if x["height"] == quality:
                        x = x["id"]
                        break
                if x == None:
                    raise Exception("Quality not found")
                self.quality = quality
                self.selected_audios = audio_list
                self.video_file = os.path.join(self.TempPath, "jv_drm_video_" + '.mkv')
                video_download_cmd = ["yt-dlp", "--allow-unplayable-formats", "--format", x, self.__url,  "--geo-bypass-country", "IN", "--external-downloader", "aria2c", "-o",  self.video_file]
                await downloadaudiocli(video_download_cmd)
                if audio_list:
                    for audi in audio_list:
                        try:
                            my_audio = os.path.join(self.TempPath, audi + '_drm.m4a')
                            audio_format = None
                            for audio_format in self.all_data["audios"]:
                                if audio_format["lang"] == audi:
                                    audio_format = audio_format["id"]
                                    break
                            if audio_format == None:
                                continue
                            audio_download_cmd = ["yt-dlp", "--allow-unplayable-formats", "--format", audio_format, self.__url,  "--geo-bypass-country", "IN", "--external-downloader", "aria2c", "-o", my_audio]
                            await downloadaudiocli(audio_download_cmd)
                            self.downloaded_audios.append(os.path.basename(my_audio))
                        except Exception as e:
                            self.log.exception(e)
                            continue
                #if "subtitles" in self.all_data:
                #    for sub in self.all_data["subtitles"]:
                #        my_sub = os.path.join(self.TempPath, sub["lang"] + '.vtt')
                #        sub_download_cmd = ["yt-dlp", "--allow-unplayable-formats", "--write-sub", "--sub-lang", sub["lang"], "--skip-download", self.__url,  "--geo-bypass-country", "IN", "-o", my_sub]
                #        await downloadaudiocli(sub_download_cmd) # Download subtitles
                #        os.rename(os.path.join(self.TempPath, f'{sub["lang"]}.vtt' + f'.{sub["lang"]}.vtt'), my_sub)
                return 0
            except Exception as e:
                self.log.exception(e)
                return 1

    async def decrypt(self):
        """Decrypt all downloaded streams"""
        all_files = self.downloaded_audios + [x for x in os.listdir(self.TempPath) if x.upper().endswith(self.VIDEO_SUFFIXES)]
        temp_audios = []
        for my_file in all_files:
            old_path = os.path.join(os.getcwd(), self.TempPath, my_file)
            new_path = os.path.join(os.getcwd(), self.TempPath, my_file.replace(" ", "_").rsplit("_", 1)[0].rsplit(".", 1)[0].replace(".", "_") + "_jv.mp4")
            if old_path.upper().endswith(self.VIDEO_SUFFIXES):
                self.video_file = new_path
            else:
                temp_audios.append(new_path)
            cmd = "mp4decrypt"
            for key in self.__key:
                cmd += f" --key {key}"
            cmd += f''' "{old_path}" "{new_path}"'''
            logging.info(cmd)
            st, stout = await run_comman_d(cmd)
            self.log.info(st + stout)
            os.remove(old_path)
        self.downloaded_audios = temp_audios

    async def no_decrypt(self):
        """set all non-drm downloaded streams"""
        all_files = self.downloaded_audios + [x for x in os.listdir(self.TempPath) if x.upper().endswith(self.VIDEO_SUFFIXES)]
        temp_audios = []
        for my_file in all_files:
            old_path = os.path.join(os.getcwd(), self.TempPath, my_file)
            new_path = os.path.join(os.getcwd(), self.TempPath, my_file.replace(" ", "_").rsplit("_", 1)[0].rsplit(".", 1)[0].replace(".", "_") + "_jv.mp4")
            if old_path.upper().endswith(self.VIDEO_SUFFIXES):
                self.video_file = new_path
            else:
                temp_audios.append(new_path)
            cmd = "mp4decrypt"
            os.rename(old_path, new_path)
        self.downloaded_audios = temp_audios

    async def merge(self, output_filename, type_="ZEE5"):
        """Merge all downloaded stream"""
        if len(self.selected_audios) > 4:
            FORM_DICT = LANGUAGE_FULL_FORM
        else:
            FORM_DICT = LANGUAGE_SHORT_FORM
        out_file = f"{output_filename} {self.quality}p {type_} WEB-DL x264 [{' + '.join(FORM_DICT.get(x.lower(), x.capitalize()) for x in self.selected_audios)} (AAC 2.0)] Esub_ROBOT_.mkv"
        out_path = os.path.join(self.out_path, out_file)
        video_path = self.video_file
        cmd = f'ffmpeg -i "{video_path}" '
        audios = self.downloaded_audios
        for audio in audios:
            cmd += f'-i "{audio}" '
        cmd +="-map 0:v "
        for i in range(1, len(audios)+1):
            cmd+=f"-map {i}:a? "
        step = 0
        for audio in audios:
            cmd += f'-metadata:s:a:{step} title="ROBOT - [(AAC 2.0)]" '
            step += 1
        cmd += f"""-c:v copy -c:a copy "{out_path}"
        """
        self.log.info(f"Executing merge cmd: {cmd}")
        st, stout = await run_comman_d(cmd)
        self.log.info(st + stout)
        try:
            shutil.rmtree(self.TempPath)
        except:
            pass
        return
