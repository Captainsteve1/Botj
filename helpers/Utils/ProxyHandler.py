import json
import logging
import os
import random
import sys

import requests

from configs.config import wvripper_config
from helpers.Utils.vpn import connect


class hold_proxy(object):
    def __init__(self):
        self.proxy = os.environ.get("http_proxy")
        self.logger = logging.getLogger(__name__)

    def disable(self):
        os.environ["http_proxy"] = ""
        os.environ["HTTP_PROXY"] = ""
        os.environ["https_proxy"] = ""
        os.environ["HTTPS_PROXY"] = ""

    def enable(self):
        if self.proxy:
            os.environ["http_proxy"] = self.proxy
            os.environ["HTTP_PROXY"] = self.proxy
            os.environ["https_proxy"] = self.proxy
            os.environ["HTTPS_PROXY"] = self.proxy


class proxy_env(object):
    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.args = args
        self.config = wvripper_config().config()
        self.VPN = self.config.VPN

    def Load(self):
        proxies = None
        proxy = {}
        aria2c_proxy = []
        proxy_status = "OFF"

        if self.args.proxy:
            proxies = self.args.proxy
            aria2c_proxy = {
                "proxy_url": proxies,
                "type": "http",
                # "localhost": self.args.nordvpn_host
            }

        if self.VPN.proxies and not self.args.proxy:
            proxies = self.VPN.proxies
            aria2c_proxy = {
                "proxy_url": proxies,
                "type": "http",
                # "localhost": self.args.nordvpn_host
            }

        if not self.VPN.proxies and not self.args.proxy:
            if self.args.privtvpn:
                # self.logger.info("Activated-PrivateVpn")
                proxy_status = "PrivateVpn"
                proxy.update({"port": str(self.VPN.private.port)})
                proxy.update({"user": self.VPN.private.email})
                proxy.update({"pass": self.VPN.private.passwd})

                if "pvdata.host" in self.args.privtvpn:
                    proxy.update({"host": self.args.privtvpn})
                else:
                    proxy.update(
                        {"host": connect(code=self.args.privtvpn).privateVPN()}
                    )

                proxies = self.VPN.private.http.format(
                    email=proxy["user"],
                    passwd=proxy["pass"],
                    ip=proxy["host"],
                    port=proxy["port"],
                )
            else:
                if self.args.nordvpn:
                    # self.logger.info("NordVpn")
                    proxy_status = "NordVpn"
                    proxy.update({"port": str(self.VPN.nordvpn.port)})
                    proxy.update({"user": self.VPN.nordvpn.email})
                    proxy.update({"pass": self.VPN.nordvpn.passwd})

                    if "nordvpn.com" in self.args.nordvpn:
                        proxy.update({"host": self.args.nordvpn})
                    else:
                        proxy.update(
                            {"host": connect(code=self.args.nordvpn).nordVPN()}
                        )

                    proxies = self.VPN.nordvpn.http.format(
                        email=proxy["user"],
                        passwd=proxy["pass"],
                        ip=proxy["host"],
                        port=proxy["port"],
                    )
                    print(proxies)
                else:
                    if self.args.torguardvpn:
                        # self.logger.info("Proxy Status: TorGuardVPN")
                        proxy_status = "TorGuardVPN"
                        proxy.update({"port": str(self.VPN.torguard.port)})
                        proxy.update({"user": self.VPN.torguard.email})
                        proxy.update({"pass": self.VPN.torguard.passwd})

                        if "torguard.com" in self.args.torguardvpn:
                            proxy.update({"host": self.args.torguardvpn})
                        else:
                            proxy.update(
                                {
                                    "host": connect(
                                        code=self.args.torguardvpn
                                    ).torguardVPN()
                                }
                            )

                        proxies = self.VPN.torguard.http.format(
                            email=proxy["user"],
                            passwd=proxy["pass"],
                            ip=proxy["host"],
                            port=proxy["port"],
                        )
                    # else:
                    #     self.logger.info("Off")

            if proxy.get("host"):
                aria2c_proxy = {
                    "email": proxy.get("user"),
                    "password": proxy.get("pass"),
                    "host": proxy.get("host"),
                    "port": proxy.get("port"),
                    "type": "https" if "nordvpn.com" in proxy.get("host") else "http",
                    "localhost": self.args.nordvpn_host
                }

        if proxies:
            os.environ["http_proxy"] = proxies
            os.environ["HTTP_PROXY"] = proxies
            os.environ["https_proxy"] = proxies
            os.environ["HTTPS_PROXY"] = proxies

        ip = None

        try:
            self.logger.info("Getting IP...")
            r = requests.get("https://ipinfo.io/json", timeout=5)
            data = r.json()
            ip = "{} ({})".format(data["ip"], data["country"].upper())
        except Exception as e:
            # self.logger.info(f"({e.__class__.__name__}: {e})")
            # sys.exit(1)
            ip = ":"

        return aria2c_proxy, ip, proxy_status
