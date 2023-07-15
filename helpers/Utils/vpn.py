import logging
import os
import random
import sys, json
from pprint import pprint

import requests
from bs4 import BeautifulSoup

class connect(object):
    def __init__(self, code):
        self.code = code.lower()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        })
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
        }

    def nordVPN(self):
        host = self.code
        country_id = [h.get("id") for h in self.session.get(
            "https://nordvpn.com/wp-admin/admin-ajax.php?action=servers_countries").json(
            ) if h.get("code").lower() == host.lower()]
        country_id, = country_id
        host = sorted(self.session.get("https://nordvpn.com/wp-admin/admin-ajax.php", params={ "action": "servers_recommendations",
                                                                                               "filters": json.dumps({"country_id": country_id})}
            ).json(), key=lambda k: int(k["load"]), reverse=True)[-1]["hostname"]
        return host


        # nordvpn_codes = dict()
        # url = 'https://nordvpn.com/wp-admin/admin-ajax.php'
        # headers = {
        #     'authority': 'nordvpn.com',
        #     'accept': '*/*',
        #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        #     'x-requested-with': 'XMLHttpRequest',
        #     'sec-fetch-site': 'same-origin',
        #     'sec-fetch-mode': 'cors',
        #     'sec-fetch-dest': 'empty',
        #     'referer': 'https://nordvpn.com/servers/tools/',
        #     'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        # }

        # params = (
        #     ('action', 'servers_countries'),
        # )

        # servers_countries = requests.get(url=url, headers=headers, params=params).json()

        # for c in servers_countries:
        #     id, code, name = c.get("id"), c.get("code").lower(), c.get("name"),
        #     nordvpn_codes[code] = {
        #         "id": id,
        #         "code": code,
        #         "name": name,
        #     }

        # if nordvpn_codes.get(self.code, None) is None:
        #     self.logger.info(self.code + " : not listed in country codes")
        #     pprint(", ".join([(c)[0] for c in nordvpn_codes.items()]))
        #     return

        # servers_recommendations = requests.get("{}{}".format(url, "?action=servers_recommendations&filters={%22country_id%22:" + str(nordvpn_codes.get(self.code).get("id")) + "}"), headers=headers).json()
        # server = sorted(servers_recommendations, key=lambda k: int(k["load"]), reverse=True)[-1]
        # return server["hostname"]

    def load_privatevpn(self):
        html_file = "html.html"
        hosts = []
        resp = requests.get(
            "https://privatevpn.com/serverlist/", stream=True, headers=self.headers
        )
        resp = str(resp.text)
        resp = resp.replace("<br>", "")

        with open(html_file, "w", encoding="utf8") as file:
            file.write(resp)

        with open(html_file, "r") as file:
            text = file.readlines()

        if os.path.exists(html_file):
            os.remove(html_file)

        for p in text:
            if ".pvdata.host" in p:
                hosts.append(p.strip())

        return hosts

    def privateVPN(self):
        private_proxy = {}
        private_hosts = self.load_privatevpn()
        self.logger.debug("private_hosts: {}".format(private_hosts))
        search_host = [host for host in private_hosts if host[:2] == self.code]
        if not search_host == []:
            self.logger.info(f"\nFounded {str(len(search_host))} Proxies")
            for n, p in enumerate(search_host):
                n = str(n + 1).zfill(2)
                self.logger.info(f"[{n}] {p}")
            inp = input("\nEnter Proxy Number, or Hit Enter for random one: ").strip()
            if inp == "":
                return random.choice(search_host)
            private_proxy = search_host[int(inp) - 1]
        else:
            self.logger.info(
                f"no Proxies Found, you may entered wrong code, or search failed!..."
            )

        return private_proxy

    def convert_host_name(self, host):
        host = host.split(".secureconnect")[0]
        host = host[: host.index("-")] if "-" in host else host
        return host

    def parse_torguard_html(self):
        url = "https://torguard.net/network/"
        html = requests.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"
            },
        )
        soup = BeautifulSoup(html.content, "html.parser")
        countries = soup.findAll("td", {"": ""})
        items = list()
        added = set()
        for i, c in enumerate(countries):
            if "torguard.com" in c.text:
                country = countries[i - 2].text.strip()
                state = countries[i - 1].text.strip()
                host = c.text.strip()
                if not host in added:
                    if country == "":
                        items.append(
                            {
                                "country": state,
                                "host": host,
                                "code": self.convert_host_name(host),
                            }
                        )
                    else:
                        items.append(
                            {
                                "country": country,
                                "state": state,
                                "host": host,
                                "code": self.convert_host_name(host),
                            }
                        )
                    added.add(host)
        return items

    def torguardVPN(self):
        _ = {}
        tor_hosts = self.parse_torguard_html()
        self.logger.debug("tor_hosts: {}".format(tor_hosts))
        tor_loaded = [x for x in tor_hosts if x["code"].startswith(self.code)]

        if tor_loaded != []:
            self.logger.info("\nFounded {} Proxies".format(len(tor_loaded)))
            for n, p in enumerate(tor_loaded):
                c = p["host"]
                n = str(n + 1).zfill(2)
                self.logger.info(f"[{n}] {c}")
            num = input("\nEnter Proxy Number, or Hit Enter for random one: ").strip()
            if num == "":
                return random.choice([x["host"] for x in tor_loaded])
            return tor_loaded[int(num) - 1]["host"]
        else:
            self.logger.info(f"no Proxies Found, you may entered wrong code, or search failed!...")
            for n, p in enumerate(tor_hosts):
                c = p["host"]
                n = str(n + 1).zfill(2)
                self.logger.info(f"[{n}] {c}")
            num = input("\nEnter Proxy Number, or Hit Enter for random one: ").strip()
            if num == "":
                return random.choice([x["host"] for x in tor_hosts])
            return tor_hosts[int(num) - 1]["host"]

        return None
