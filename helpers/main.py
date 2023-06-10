import json
import logging
import os
import re
import sys
from datetime import datetime

from configs.config import LOG_FILE, PRESETS_FOLDER

from helpers.Utils.ProxyHandler import proxy_env
from helpers.Utils.schedule import schedule
from helpers.Utils.utils import Services, msgBox

NAME = "Widevine Ripper AKA WVRipper:"
VERSION = "2.1.8"
Note = f""

class args_presets:
    def __init__(self):
        """HOLD ARGS Presets FOR WVRIPPER"""
        self.PRESETS_FOLDER = PRESETS_FOLDER

    def _save_presets__(self, args):

        with open(os.path.join(self.PRESETS_FOLDER, f"{args.save_preset}.preset"), 'w') as f:
            json.dump(args.__dict__, f, indent=4)

        return

    def _load_presets__(self, args):
        default_file = os.path.join(self.PRESETS_FOLDER, "default.preset")
        preset_file = os.path.join(self.PRESETS_FOLDER, f"{args.load_preset}.preset")
        preset_args = json.load(open(preset_file, "r"))
        defualt_args = json.load(open(default_file, "r"))

        for name, value in args.__dict__.items():
            if value != defualt_args.get(name):
                preset_args.update({name: value})

        return preset_args

class main:
    def __init__(self, args):
        """HOLD THE ARGS FOR WVRIPPER"""
        self.args = args
        self.logging = logging
        self._enable_logger__()

    def _enable_logger__(self):
        # CREATE HANDLER FOR DEBUGING TO FILE
        FILELOG_Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        FILELOG = logging.FileHandler(LOG_FILE, "w", "utf-8")
        FILELOG.setLevel(logging.DEBUG)
        FILELOG.setFormatter(FILELOG_Formatter)
        # CREATE HANDLER FOR STDOUD INFO TO CONSOLE
        CONSOLELOG_Formatter = logging.Formatter('%(message)s')
        CONSOLELOG = logging.StreamHandler()
        CONSOLELOG.setLevel(logging.INFO)
        CONSOLELOG.setFormatter(CONSOLELOG_Formatter)
        # CREATE CONFIG AND ADD HANDLERS...
        self.logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG, handlers=[CONSOLELOG, FILELOG])
        self.logging.getLogger(__name__)

        return

    def _eta(self, set_start_time=False):
        if set_start_time:
            self.start_time = datetime.now()
            return
        print(
            "\nWVripper took {} Sec".format(
                int(float((datetime.now() - self.start_time).total_seconds()))
            )
        )  # total seconds

    def _arguments_manager__(self,):

        if self.args.save_preset or self.args.load_preset:
            args = args_presets()
            if self.args.save_preset:
                print("Saving arguments {} for later use...".format(self.args.save_preset))
                args._save_presets__(self.args)
                sys.exit(0)
            elif self.args.load_preset:
                print("Loading {} arguments...".format(self.args.save_preset))
                self.args.__dict__ = args._load_presets__(self.args)

        while not self.args.content or self.args.content.strip() == "":
            self.args.content = input("\nEnter URL: ").strip()

        if not self.args.service:
            service = Services()
            Detectedservice = service.detect(self.args.content)
            if not Detectedservice:
                print("Input: {} \ndoes not appear to be a url,\nso please select what service you're going to use. by using --service <name of service>.".format(self.args.content))
                exit(-1)
            self.args.service = Detectedservice

        os.environ["SERVICE_NAME"] = str(self.args.service)
        pack_settings = {
            "upload": self.args.upload,
            "trackers": self.args.trackers,
            "content_type": self.args.content_type,
            "description": self.args.description,
            "seed": self.args.seed,
            "local_seed": self.args.local_seed,
        }

        proxy, ip, proxy_status = proxy_env(self.args).Load()
        commands = {"aria2c_extra_commands": proxy, "pack_settings": pack_settings}
        print(self._get_msg__box(ip, self.args.service, proxy_status))

        if self.args.schedule:
            wait = schedule(self.args.schedule)
            wait.countdown()

        self._eta(set_start_time=True)
        self._check_disabled__services(self.args.service)

        return self.args, commands

    def _start_service(self, args, commands):
        if args.service:
            if args.service == "NETFLIX":
                from services.netflix import netflix
                netflix(args, commands).main()

            elif args.service == "APPLETV":
                from services.appletvplus import appletvplus
                appletvplus(args, commands).main()

            elif args.service == "DISNEYPLUS":
                from services.disneyplus import disneyplus
                disneyplus(args, commands).main()

            elif args.service == "AMAZON":
                from services.primevideo import primevideo
                primevideo(args, commands).main()

            elif args.service == "HULU":
                from services.hulu import hulu
                hulu(args, commands).main()

            elif args.service == "SHAHID":
                from services.shahid import shahid
                shahid(args, commands).main()

            elif args.service == "STAN":
                from services.stan import stan
                stan(args, commands).main()

            elif args.service == "RAKUTEN":
                from services.rakuten import rakuten
                rakuten(args, commands).main()

            elif args.service == "GOOGLE":
                from services.googleplay import googleplay
                googleplay(args, commands).main()

            elif args.service == "FANDANGONOW":
                from services.fandangonow import fandangonow
                fandangonow(args, commands).main()

            elif args.service == "HBOMAX":
                from services.hbomax import hbomax
                hbomax(args, commands).main()

            elif args.service == "OSN":
                from services.osn import osn
                osn(args, commands).main()

            elif args.service == "PEACOCKTV":
                from services.peacock import peacock
                peacock(args, commands).main()

            elif args.service == "ITUNES":
                from services.itunes import itunes
                itunes(args, commands).main()

            elif args.service == "PARAMOUNT":
                from services.paramount import paramount
                paramount(args, commands).main()

            elif args.service == "STARPLUS":
                from services.starplus import starplus
                starplus(args, commands).main()

        return

    def _get_msg__box(self, IP, Service, proxy_status):
        return msgBox(NAME=NAME, INFO=f"VERSION: {VERSION}\nPROXY: {proxy_status}\nIP: {IP}\nSERVICE: {Service}\nNOTE: {Note}",)

    def _check_disabled__services(self, service):
        if service in []:
            raise ValueError(f"This service: {service} is under maintenance ")
