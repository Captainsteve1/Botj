import json
import logging
import os
import random
import re
import sys
from http.cookiejar import MozillaCookieJar

import requests
from bs4 import BeautifulSoup


class WebLoginUtils:
    def __init__(self,):
        """login helper"""
        self.logger = logging.getLogger(__name__)
        self.JSON_REGEX = r"netflix\.{}\s*=\s*(.*?);\s*</script>"
        self.context = {}

    def ParseRecaptchaToken(self, response):
        text = re.sub(r"\)]}'", "", response)
        try:
            js = json.loads(text)
            return js[1]
        except Exception:
            raise ValueError("Invalid recaptcha json response: {}".format(response))

        return

    def ParseVersionQuery(self, response):
        VERSION_REGEX = r"src=.+recaptcha/releases/(.+?)/"

        if not re.search(VERSION_REGEX, response):
            raise ValueError("Invalid recaptcha response: {}".format(response))

        return re.search(VERSION_REGEX, response).group(1)

    def recaptchaResponseTime(self,):
        return "".join([str(x) for x in random.sample(range(4, 8), 3)])

    def dump_content(self, content):
        with open("content.html", "wb") as f:
            f.write(content)

    def extract_json(self, content):
        compiler = re.compile(self.JSON_REGEX.format("reactContext"), re.DOTALL)
        json_array = compiler.findall(content.decode("utf-8"))
        if not json_array:
            self.dump_content(content)
            raise ValueError("Invalid login web response")

        js = json_array[0]
        js = js.replace('\\"', '\\\\"')
        js = js.replace("\\s", "\\\\s")
        js = js.replace("\\n", "\\\\n")
        js = js.replace("\\t", "\\\\t")
        js = js.encode().decode("unicode_escape")
        js = re.sub(r'\\(?!["])', r"\\\\", js)
        js = json.loads(js)
        self.context = js
        return

    def _get_accept_language_string(self, user_data):
        supported_locales = user_data["supportedLocales"]

        try:
            locale = next(
                dict_item
                for dict_item in supported_locales
                if dict_item["default"] is True
            )["locale"]
        except StopIteration:
            locale = ""
        locale_fallback = "en-US"
        if locale and locale != locale_fallback:
            return "{loc},{loc_l};q=0.9,{loc_fb};q=0.8,{loc_fb_l};q=0.7".format(
                loc=locale,
                loc_l=locale[:2],
                loc_fb=locale_fallback,
                loc_fb_l=locale_fallback[:2],
            )
        return "{loc},{loc_l};q=0.9".format(
            loc=locale_fallback, loc_l=locale_fallback[:2]
        )

    def assert_valid_auth_url(self, user_data):
        """Raise an exception if user_data does not contain a valid authURL"""
        if len(user_data.get("authURL")) != 42:
            raise ValueError(
                "authURL is not valid: {}".format(user_data.get("authURL"))
            )
        return user_data

    def extract_values(self):
        X_Netflix_uiVersion = (
            self.context.get("models", {})
            .get("serverDefs", {})
            .get("data", {})
            .get("BUILD_IDENTIFIER", None)
        )
        BUILD_IDENTIFIER = (
            self.context.get("models", {})
            .get("abContext", {})
            .get("data", {})
            .get("headers", {})
            .get("X-Netflix.uiVersion", None)
        )
        requestCountry = (
            self.context.get("models", {})
            .get("loginContext", {})
            .get("data", {})
            .get("geo", {})
            .get("requestCountry", {})
            .get("id", None)
        )
        countryCodes = (
            self.context.get("models", {})
            .get("countryCodes", {})
            .get("data", {})
            .get("codes", None)
        )
        supportedLocales = (
            self.context.get("models", {})
            .get("loginContext", {})
            .get("data", {})
            .get("geo", {})
            .get("supportedLocales", None)
        )
        authURL = (
            self.context.get("models", {})
            .get("userInfo", {})
            .get("data", {})
            .get("authURL", None)
        )
        recaptchaSitekey = (
            self.context.get("models", {})
            .get("loginContext", {})
            .get("data", {})
            .get("flow", {})
            .get("fields", {})
            .get("recaptchaSitekey", {})
            .get("value", None)
        )

        if not any(
            [
                X_Netflix_uiVersion,
                BUILD_IDENTIFIER,
                requestCountry,
                countryCodes,
                supportedLocales,
                authURL,
                recaptchaSitekey,
            ]
        ):
            raise ValueError("Your current IP is banned.")

        return self.assert_valid_auth_url(
            {
                "X_Netflix_uiVersion": X_Netflix_uiVersion,
                "BUILD_IDENTIFIER": BUILD_IDENTIFIER,
                "requestCountry": requestCountry,
                "countryCodes": countryCodes,
                "supportedLocales": supportedLocales,
                "authURL": authURL,
                "recaptchaSitekey": recaptchaSitekey,
            }
        )


class WebLogin:
    def __init__(self,):
        """Perform account login"""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.WebLoginUtils = WebLoginUtils()
        self.PCBrowserUA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
        self.endpoint = {
            "login": "https://www.netflix.com/login",
            "Origin": "https://www.netflix.com",
            "enterprise": "https://www.google.com/recaptcha/enterprise.js?render={}",
            "anchor": "https://www.google.com/recaptcha/api2/anchor?ar={}&k={}&co={}&hl={}&v={}&size={}",
            "reload": "https://www.google.com/recaptcha/api2/reload?k={}",
        }

    def _login_payload(self, email, password, authURL, USER, recaptchaResponseToken):
        countryIsoCode = USER["requestCountry"]
        countryCodes = USER["countryCodes"]

        try:
            countryCode = (
                "+"
                + next(item for item in countryCodes if item["id"] == countryIsoCode)[
                    "code"
                ]
            )
        except StopIteration:
            countryCode = ""

        return {
            "userLoginId": email,
            "password": password,
            "rememberMe": "true",
            "flow": "websiteSignUp",
            "mode": "login",
            "action": "loginAction",
            "withFields": "rememberMe,nextPage,userLoginId,password,countryCode,countryIsoCode,recaptchaResponseToken,recaptchaError,recaptchaResponseTime",
            "authURL": authURL,
            "nextPage": "",
            "showPassword": "",
            "countryCode": countryCode,
            "countryIsoCode": countryIsoCode,
            "recaptchaResponseToken": recaptchaResponseToken,
            "recaptchaResponseTime": self.WebLoginUtils.recaptchaResponseTime(),
        }

    def recaptcha_enterprise(self, USER):
        r = self.session.get(
            url=self.endpoint["enterprise"].format(USER["recaptchaSitekey"]),
            headers={"User-Agent": self.PCBrowserUA},
        )

        return {
            "size": "invisible",
            "hl": "en",
            "co": "aHR0cHM6Ly93d3cubmV0ZmxpeC5jb206NDQz",
            "ar": 1,
            "k": USER["recaptchaSitekey"],
            "v": self.WebLoginUtils.ParseVersionQuery(r.text),
        }

    def recaptcha_anchor(self, QUERIES):

        r = self.session.get(
            url=self.endpoint["anchor"].format(
                QUERIES.get("ar"),
                QUERIES.get("k"),
                QUERIES.get("co"),
                QUERIES.get("hl"),
                QUERIES.get("v"),
                QUERIES.get("size"),
            ),
            headers={"User-Agent": self.PCBrowserUA},
        )

        soup = BeautifulSoup(r.content, "html.parser")
        token = soup.find("input", {"id": "recaptcha-token"})

        if not token:
            raise ValueError("Invalid recaptcha-token response: {}".format(r.text))

        return token.get("value")

    def recaptcha_reload(self, TOKEN, USER):
        r = self.session.post(
            url=self.endpoint["reload"].format(USER["recaptchaSitekey"]),
            headers={"User-Agent": self.PCBrowserUA},
            data={"reason": "q", "c": TOKEN},
        )

        return self.WebLoginUtils.ParseRecaptchaToken(r.text)

    def recaptchaResponseToken(self, USER):
        QUERIES = self.recaptcha_enterprise(USER)
        TOKEN = self.recaptcha_anchor(QUERIES)
        RECAPTCHA_TOKEN = self.recaptcha_reload(TOKEN, USER)
        return RECAPTCHA_TOKEN

    def validate_login(self, response):
        if response.status_code != 200:
            self.WebLoginUtils.dump_content(response.content)
            raise ValueError(
                "Login Failed: Response Status {}".format(response.status_code)
            )

        if "Incorrect password" in str(response.text):
            self.WebLoginUtils.dump_content(response.content)
            raise ValueError("Login Failed: Incorrect password")

        return

    def COOKIES(self, session):
        return {
            "COOKIE": "; ".join(
                [f"{cookie.name}={cookie.value}" for cookie in session.cookies]
            ),
            "DICT": {cookie.name: cookie.value for cookie in session.cookies},
        }

    def login(self, email, password):
        self.logger.info("\nLogging in...")
        r = self.session.get(self.endpoint["login"])
        self.WebLoginUtils.extract_json(r.content)
        USER = self.WebLoginUtils.extract_values()
        LOCATION_LOGIN_ENDPOINT = r.url

        LOGIN_RESPONSE = self.session.post(
            LOCATION_LOGIN_ENDPOINT,
            headers={
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1",
                "Origin": self.endpoint["Origin"],
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self.PCBrowserUA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Referer": LOCATION_LOGIN_ENDPOINT,
                "Accept-Language": self.WebLoginUtils._get_accept_language_string(USER),
            },
            data=self._login_payload(
                email,
                password,
                USER["authURL"],
                USER,
                self.recaptchaResponseToken(USER),
            ),
        )

        self.validate_login(LOGIN_RESPONSE)
        BUILD_IDENTIFIER = USER.get("X_Netflix_uiVersion")
        COOKIES = self.COOKIES(self.session)["DICT"]
        self.logger.info("Login successful")
        return COOKIES, BUILD_IDENTIFIER


class Metadata:
    def __init__(self, email, password, cookies_file):
        """CLASS FOR NETFLIX METADATA"""
        self.logger = logging.getLogger(__name__)
        self.email, self.password, self.cookies_file = email, password, cookies_file
        self.WebLogin = WebLogin()  # LOGIN

    def get_build(self, cookies):
        BUILD_REGEX = r'"BUILD_IDENTIFIER":"([a-z0-9]+)"'

        session = requests.Session()
        session.headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en,en-US;q=0.9",
        }

        r = session.get("https://www.netflix.com/browse", cookies=cookies)

        if not re.search(BUILD_REGEX, r.text):
            raise ValueError(
                "cannot get BUILD_IDENTIFIER from the cookies you saved from the browser..."
            )

        return re.search(BUILD_REGEX, r.text).group(1)

    def MozillaCookieJar(self, cookies_file):
        try:
            cj = MozillaCookieJar(cookies_file)
            cj.load()
        except Exception:
            raise ValueError("invalid netscape format cookies file")

        cookies = dict()
        for cookie in cj:
            cookies[cookie.name] = cookie.value

        return cookies

    def _get(self, NFID, COOKIES, BUILD_IDENTIFIER, METADATA_LANGUAGE):

        counter = 0
        times = 5

        while counter <= times:
            success, data = self.shakti_api(
                NFID, COOKIES, BUILD_IDENTIFIER, METADATA_LANGUAGE
            )
            if success:
                return data

            COOKIES, BUILD_IDENTIFIER = self.WebLogin.login(self.email, self.password)
            self.DumpCookiesAsJsonFile(COOKIES, BUILD_IDENTIFIER)
            counter += 1

        return None

    def shakti_api(self, NFID, COOKIES, BUILD_IDENTIFIER, METADATA_LANGUAGE):

        HEADERS = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "es,ca;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "www.netflix.com",
            "Pragma": "no-cache",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
            "X-Netflix.browserName": "Chrome",
            "X-Netflix.browserVersion": "79",
            "X-Netflix.clientType": "akira",
            "X-Netflix.esnPrefix": "NFCDCH-02-",
            "X-Netflix.osFullName": "Windows 10",
            "X-Netflix.osName": "Windows",
            "X-Netflix.osVersion": "10.0",
            "X-Netflix.playerThroughput": "1706",
            "X-Netflix.uiVersion": BUILD_IDENTIFIER,
        }

        PARAMS = {
            "movieid": NFID,
            "drmSystem": "widevine",
            "isWatchlistEnabled": "false",
            "isShortformEnabled": "false",
            "isVolatileBillboardsEnabled": "false",
            "languages": METADATA_LANGUAGE,
        }

        response = requests.get(
            url=f"https://www.netflix.com/nq/website/memberapi/{BUILD_IDENTIFIER}/metadata",
            headers=HEADERS,
            params=PARAMS,
            cookies=COOKIES,
        )

        if response.status_code == 500:
            self.logger.info("401 Unauthorized, cookies is invalid")
            return False, None
        elif response.status_code == 200 and response.text.strip() == "":
            raise ValueError(f"{NFID} not available yet/in your Netflix region")

        try:
            response.json()["video"]["type"]
            return True, response.json()
        except Exception:
            raise ValueError(f"Returned Invaid Json... Update cookies...")
            self.logger.info("Returned Invaid Json... LOGGING...")
            return False, None

        return False, None

    def DumpCookiesAsJsonFile(self, COOKIES, BUILD_IDENTIFIER):
        with open(self.cookies_file, "w") as f:
            f.write(
                json.dumps(
                    {"COOKIES": COOKIES, "BUILD_IDENTIFIER": BUILD_IDENTIFIER}, indent=4
                )
            )

        return

    def CleanCookies(self, cookies):
        cleaned = dict()

        for name, value in cookies.items():
            if not name == "flwssn":
                cleaned[name] = value

        return cleaned

    def LoadDumpedCookies(self,):

        COOKIES, BUILD_IDENTIFIER = None, None

        try:
            data = json.load(open(self.cookies_file, "r"))
            COOKIES = data["COOKIES"]
            COOKIES = data["BUILD_IDENTIFIER"]
            return data["COOKIES"], data["BUILD_IDENTIFIER"]
        except Exception:
            COOKIES = self.MozillaCookieJar(self.cookies_file)
            BUILD_IDENTIFIER = self.get_build(COOKIES)
            self.DumpCookiesAsJsonFile(
                COOKIES, BUILD_IDENTIFIER
            )  # avoiding next time getting build...

        return COOKIES, BUILD_IDENTIFIER

    def DoubleCheckCookies(self, cookies):
        if "NetflixId" not in str(cookies):
            self.logger.info("(Some) cookies expired, renew...")
            return False

        return True

    def client(self):

        if os.path.isfile(self.cookies_file):
            COOKIES, BUILD_IDENTIFIER = self.LoadDumpedCookies()
        else:
            raise SystemError(
                f"Currently Login does not work, save cookies from browser using: cookies.txt Addon\n"
                + "https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg"
            )
            COOKIES, BUILD_IDENTIFIER = self.WebLogin.login(self.email, self.password)
            self.DumpCookiesAsJsonFile(COOKIES, BUILD_IDENTIFIER)

        COOKIES = self.CleanCookies(COOKIES)

        if not self.DoubleCheckCookies(COOKIES):
            COOKIES, BUILD_IDENTIFIER = self.WebLogin.login(self.email, self.password)
            self.DumpCookiesAsJsonFile(COOKIES, BUILD_IDENTIFIER)

        return COOKIES, BUILD_IDENTIFIER
