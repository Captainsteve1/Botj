import argparse
import asyncio
import configparser
import glob
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from os.path import isfile
from threading import Thread
from urllib.parse import urlsplit

import ffmpy
import inquirer
import pycountry
import requests
import tqdm
import utils.modules.pycaption as pycaption
import utils.modules.pymkverge as pymkverge
from bs4 import BeautifulSoup
from configs.config import wvripper_config
from helpers.Parsers.primevideo.prime import prime
from helpers.tracks import (select_by_arguments, select_by_asking, show_tracks,
                            smart_select)
from helpers.Utils.keyloader import keyloader
from helpers.Utils.ripprocess import EpisodesNumbersHandler, ripprocess
from helpers.Utils.utils import WhenDownloadFinish, download_dir
from helpers.Utils.vpn import connect
from helpers.wvdownloader import Aria2c, SubtitleHelper, VideoHelper
from helpers.wvtracks import wvtracks
# from pywidevine.cdm import cdm, deviceconfig
from helpers.Utils.sub_filter import sub_filters
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt
from utils import thr3ad

try:
    from helpers.Utils.Packer import release

    doPacking = True
except ModuleNotFoundError:
    doPacking = False
    pass


class primevideo:
    def __init__(self, args, commands):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.args = args
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.SERVICE = self.config.SERVICES.AMAZON
        self.device = self.config.DEVICES.AMAZON
        self.ripprocess = ripprocess()
        self.EpisodesNumbersHandler = EpisodesNumbersHandler()
        self.commands = commands
        self.keyloader = keyloader(self.SERVICE.keys_file, self.SERVICE.NAME)
        self.SubtitleHelper = SubtitleHelper()
        self.Aria2c = Aria2c()
        self.VideoHelper = VideoHelper()
        self.download_dir = download_dir(
            arg_output=self.args.output,
            path_folder=self.config.PATHS.DL_FOLDER,
            stream_folder=self.SERVICE.NAME,
        )

        self.tv_show_name = None

    def get_token_file(self, region):
        PV_REGIONS = ["eu", "ca", "na", "fe", "ps"]
        token_file = self.SERVICE.token_file.format(region=f"amazon_{region}") if not region in PV_REGIONS else self.SERVICE.token_file.format(region="primevideo")

        # if not os.path.isfile(token_file):
        #     raise FileNotFoundError(token_file)

        return token_file

    def get_cookies_file(self, region):
        PV_REGIONS = ["eu", "ca", "na", "fe", "ps"]
        cookies_file = self.SERVICE.cookies_file.format(region=region) if not region in PV_REGIONS else self.SERVICE.cookies_file.format(region="ps")

        if not os.path.isfile(cookies_file):
            raise FileNotFoundError(cookies_file)

        return cookies_file

    def perform_licensing(self, Tracks, Name, Folder):
        KEYS = []
        added = set()

        self.logger.info("\nGetting KEYS...")

        if not Tracks.Videos == []:
            for track in Tracks.Videos:
                profile = track.Extras.get("profile")
                if not profile in added:
                    PROFILE_KEYS = self.prime.PrimeLicenseRequest(pssh=track.PSSH, config=track.Extras, device=self.device)
                    if not PROFILE_KEYS == []:
                        KEYS += PROFILE_KEYS
                        self.logger.info(f"\n{Name} {profile} KEYS\n")
                        self.logger.info("\n".join(PROFILE_KEYS))
                        self.keyloader.add_keys(keys=PROFILE_KEYS, pssh=track.PSSH, name=Name)
                    added.add(profile)

        return

    def decryptFile(self, encrypted, decrypted, Track=None):
        if isfile(decrypted):
            return

        if not isfile(encrypted):
            raise FileNotFoundError(encrypted)

        KID = self.keyloader.generate_kid(encrypted)
        KEYS = self.keyloader.get_key_by_kid(KID)

        if KEYS == []:
            self.logger.info("\nGetting KEYS...")
            KEYS = self.prime.PrimeLicenseRequest(pssh=Track.PSSH, config=Track.Extras, device=self.device)
            if not KEYS == []:
                KEYS = self.keyloader.add_keys(
                    keys=[key for key in KEYS if ":" in key], pssh=None, name=self.Name
                )

        if not KEYS == []:
            if not [x for x in KEYS if x["KID"] == KID] == []:
                KEYS = [x for x in KEYS if x["KID"] == KID]

            self.VideoHelper.mp4decryptor(
                encrypted=encrypted,
                decrypted=decrypted,
                keys=KEYS,
                pandsdecryptor=True,
                kid=True,
            )

            return True

        return False

    def cleanFile(self, decrypted, cleaned, Type="VIDEO"):
        if isfile(cleaned):
            return

        if not isfile(decrypted):
            raise FileNotFoundError(decrypted)

        if Type == "VIDEO":
            if self.SERVICE.NAME.lower() in list(
                map(lambda x: x.lower(), self.config.SETTINGS.skip_video_demux)
            ):
                os.rename(decrypted, cleaned)
                return

            self.VideoHelper.ffmpegclean(decrypted=decrypted, cleaned=cleaned)

        if Type == "AUDIO":
            self.VideoHelper.ffmpegcleanAudio(Input=decrypted)

        return

    def downloadChapters(self, Name):
        if self.metadata.get("chapters"):
            if not self.metadata.get("chapters") == [] and self.metadata.get("chapters") is not None:
                chapfile = f"{Name} - Chapters.txt"
                if not isfile(chapfile):
                    with open(chapfile, "w", encoding="utf-8") as f:
                        for chapter in self.metadata.get("chapters"):
                            f.write(
                                chapter["ChapterTXT"].encode("utf-8").decode("utf-8")
                            )
        return

    def SubtitleProcessor(self, Name, Track):
        _ = "{} {}-{}.sub".format(Name, Track.Language, Track.Type.lower())
        srt = "{} {}-{}.srt".format(Name, Track.Language, Track.Type.lower())

        if Track.DownloadType == "URL" and not isfile(srt):
            self.SubtitleHelper.SubtitleDownloader(Url=Track.Url, Output=srt, Session=self.session)

            if Track.Language == "ar":
                self.SubtitleHelper.ReverseRtl(srt, srt)

        if Track.DownloadType == "URL" and Track.Language.startswith("en") and Track.Type == "SDH":
            nosdh_srt = nosdh_output = "{} {}-{}.srt".format(Name, Track.Language, "SUBTITLE".lower())
            self.SubtitleHelper.SubtitleDownloader(Url=Track.Url, Output=nosdh_srt, Session=self.session)
            # self.SubtitleHelper.NoSDH(nosdh_srt, nosdh_output)
            with open(nosdh_srt, "r", encoding="utf8") as f:
                text = f.read()
            sub = sub_filters(text)
            sub.remove_sdh(
              remove_font_colours=True,
              remove_asterisks=True,
              remove_music=True,
              # remove_sound_effects=True,
              replace_names=True,
              remove_author=True,
              fix_comma_spaces=True
            )
            with open(nosdh_srt, "w", encoding="utf8") as f:
                f.write(sub.get_text())

        return

    def audio_task(self, Name, Folder, Track):
        audio_encrypted = "{} {}-{}-encrypted.mp4".format(
            Name, Track.Language, Track.Type.lower()
        )
        audio_decrypted = "{} {}-{}-decrypted.mp4".format(
            Name, Track.Language, Track.Type.lower()
        )
        audio_cleaned = "{} {}-{}-cleaned.mp4".format(
            Name, Track.Language, Track.Type.lower()
        )

        if Track.DownloadType == "URL" and not isfile(audio_cleaned):
            self.Aria2c.DownLoad(
                Output=audio_encrypted,
                Track=Track,
                saldl=self.args.saldl,
                noaria2c=self.args.noaria2c,
                extra_commands=[]
                if self.args.no_download_proxy
                else self.commands["aria2c_extra_commands"],
            )
            if not Track.Drm:
                self.cleanFile(audio_encrypted, audio_cleaned, Type="AUDIO")
                return

            self.decryptFile(
                audio_encrypted, audio_decrypted, Track=Track
            )
            self.cleanFile(audio_decrypted, audio_cleaned, Type="AUDIO")

        return

    def video_task(self, Name, Folder, Track):
        video_encrypted = "{} {} [{}]-encrypted.mp4".format(
            Name, Track.Height, Track.Profile
        )
        video_decrypted = "{} {} [{}]-decrypted.mp4".format(
            Name, Track.Height, Track.Profile
        )
        video_cleaned = "{} {} [{}]-cleaned.mp4".format(
            Name, Track.Height, Track.Profile
        )

        if Track.DownloadType == "URL" and not isfile(video_cleaned):
            self.Aria2c.DownLoad(
                Output=video_encrypted,
                Track=Track,
                saldl=self.args.saldl,
                noaria2c=self.args.noaria2c,
                extra_commands=[]
                if self.args.no_download_proxy
                else self.commands["aria2c_extra_commands"],
            )

            print("\nStarting audio/subtitles thread...")
            for job in self.audio_jobs: job.start()
            for job in self.subtitles_jobs: job.start()

            if not Track.Drm:
                self.cleanFile(video_encrypted, video_cleaned)
                self.inputfile = video_cleaned
                return

            self.decryptFile(
                video_encrypted, video_decrypted, Track=Track
            )
            self.cleanFile(video_decrypted, video_cleaned)

        if isfile(video_cleaned):
            self.inputfile = video_cleaned
        return

    def downloadItem_thread(self, Name, Folder, Tracks):
        self.inputfile = None
        jobs = []
        aria2_txt = []

        self.subtitles_jobs = []
        self.audio_jobs = []
        self.video_job = None

        if not self.args.nosubs and Tracks.TimedText != []:
            for Track in Tracks.TimedText:
                self.subtitles_jobs += [Thread(target=self.SubtitleProcessor, args=(Name, Track,),)]

        if not self.args.noaudio and Tracks.Audios != []:
            for Track in Tracks.Audios:
                self.audio_jobs += [Thread(target=self.audio_task, args=(Name, Folder, Track, ),)]

        if not self.args.novideo and Tracks.Videos != []:
            for Track in Tracks.Videos:
                self.video_job = Thread(target=self.video_task, args=(Name, Folder, Track, ),)
                break

        self.video_job.start()
        self.video_job.join()

        for job in self.audio_jobs:
            job.join()

        for job in self.subtitles_jobs:
            job.join()


        if (
            self.inputfile
            and not self.args.novideo
            and Tracks.Videos != []
            and not self.args.noaudio
            and Tracks.Audios != []
            and not self.args.nomux
        ):


            extra_mkvmerge_params = self.args.extra_mkvmerge_params
            defaults = self.args.audio_subtitle_defaults
            group = self.args.muxer_group
            source = self.SERVICE.TAG
            title = Name
            inputfile = self.inputfile
            seasonfolder = Folder
            scheme = self.args.muxer_scheme
            outputfolder = (
                self.args.outputfolder
                if self.args.outputfolder
                else self.download_dir.DirOutput
            )

            tv_show_name = self.tv_show_name if self.args.with_show_title else None
            mkvmerge = pymkverge.mkvmerge()
            mkvmerge.options(title=title)
            mkvmerge.settings(
                inputfile=inputfile,
                seasonfolder=seasonfolder,
                outputfolder=outputfolder,
                source=source,
                scheme=scheme,
                group=group,
                defaults=defaults,
                extra_mkvmerge_params=extra_mkvmerge_params,
                tv_show_name=tv_show_name
            )

            mkvmerge.start_muxing()

            if doPacking and mkvmerge.exit_code == 0:
                packing = release(
                    filename=mkvmerge.outputfile,
                    pack_settings=self.commands["pack_settings"],
                )
                packing.upload()

            if self.args.enable_file_assister and mkvmerge.exit_code == 0:
                WhenDownloadFinish().onLoad(title, mkvmerge.outputfile)

            if not self.args.keep and mkvmerge.exit_code == 0:
                self.ripprocess.clean_dir(title)
            self.logger.info("Done!")

        return

    def downloadItem(self, Name, Folder, Tracks):
        if self.args.thread_tasks:
            self.downloadItem_thread(Name, Folder, Tracks)
            return

        self.inputfile = None

        if not self.args.nochpaters:
            self.downloadChapters(Name)

        if not self.args.novideo and Tracks.Videos != []:
            for Track in Tracks.Videos:
                video_encrypted = "{} {} [{}]-encrypted.mp4".format(
                    Name, Track.Height, Track.Profile
                )
                video_decrypted = "{} {} [{}]-decrypted.mp4".format(
                    Name, Track.Height, Track.Profile
                )
                video_cleaned = "{} {} [{}]-cleaned.mp4".format(
                    Name, Track.Height, Track.Profile
                )

                if Track.DownloadType == "URL" and not isfile(video_cleaned):
                    self.Aria2c.DownLoad(
                        Output=video_encrypted,
                        Track=Track,
                        saldl=self.args.saldl,
                        noaria2c=self.args.noaria2c,
                        extra_commands=[]
                        if self.args.no_download_proxy
                        else self.commands["aria2c_extra_commands"],
                    )
                    if not Track.Drm:
                        self.cleanFile(video_encrypted, video_cleaned)
                        continue

                    self.decryptFile(video_encrypted, video_decrypted, Track=Track)
                    self.cleanFile(video_decrypted, video_cleaned)

                if isfile(video_cleaned):
                    self.inputfile = video_cleaned

        if not self.args.noaudio and Tracks.Audios != []:
            for Track in Tracks.Audios:
                audio_encrypted = "{} {}-{}-encrypted.mp4".format(
                    Name, Track.Language, Track.Type.lower()
                )
                audio_decrypted = "{} {}-{}-decrypted.mp4".format(
                    Name, Track.Language, Track.Type.lower()
                )
                audio_cleaned = "{} {}-{}-cleaned.mp4".format(
                    Name, Track.Language, Track.Type.lower()
                )

                if Track.DownloadType == "URL" and not isfile(audio_cleaned):
                    self.Aria2c.DownLoad(
                        Output=audio_encrypted,
                        Track=Track,
                        saldl=self.args.saldl,
                        noaria2c=self.args.noaria2c,
                        extra_commands=[]
                        if self.args.no_download_proxy
                        else self.commands["aria2c_extra_commands"],
                    )

                    if not Track.Drm:
                        self.cleanFile(audio_encrypted, audio_cleaned, Type="AUDIO")
                        continue

                    self.decryptFile(audio_encrypted, audio_decrypted, Track=Track)
                    self.cleanFile(audio_decrypted, audio_cleaned, Type="AUDIO")

        if not self.args.nosubs and Tracks.TimedText != []:
            print()
            processes = []
            for Track in Tracks.TimedText:
                process = Thread(target=self.SubtitleProcessor, args=(Name, Track,),)
                process.start()
                processes.append(process)

            for process in processes:
                process.join()  # -> gotta wait all subtitles to finish before muxing.

        # ~ pymkvmerge ~

        if (
            self.inputfile
            and not self.args.novideo
            and Tracks.Videos != []
            and not self.args.noaudio
            and Tracks.Audios != []
            and not self.args.nomux
        ):


            extra_mkvmerge_params = self.args.extra_mkvmerge_params
            defaults = self.args.audio_subtitle_defaults
            group = self.args.muxer_group
            source = self.SERVICE.TAG
            title = Name
            inputfile = self.inputfile
            seasonfolder = Folder
            scheme = self.args.muxer_scheme
            outputfolder = (
                self.args.outputfolder
                if self.args.outputfolder
                else self.download_dir.DirOutput
            )

            tv_show_name = self.tv_show_name if self.args.with_show_title else None
            mkvmerge = pymkverge.mkvmerge()
            mkvmerge.options(title=title)
            mkvmerge.settings(
                inputfile=inputfile,
                seasonfolder=seasonfolder,
                outputfolder=outputfolder,
                source=source,
                scheme=scheme,
                group=group,
                defaults=defaults,
                extra_mkvmerge_params=extra_mkvmerge_params,
                tv_show_name=tv_show_name,
            )

            mkvmerge.start_muxing()

            if doPacking and mkvmerge.exit_code == 0:
                packing = release(
                    filename=mkvmerge.outputfile,
                    pack_settings=self.commands["pack_settings"],
                )
                packing.upload()

            if self.args.enable_file_assister and mkvmerge.exit_code == 0:
                WhenDownloadFinish().onLoad(title, mkvmerge.outputfile)

            if not self.args.keep and mkvmerge.exit_code == 0:
                self.ripprocess.clean_dir(title)
            self.logger.info("Done!")

        return

    @thr3ad.asyncthread
    def palybacks_dl(self, p, wvtracks):
        return self.prime.PlayBacksExtractor(p, wvtracks)

    def getItem(self, asin, metadata, palybacks, Name, Folder):
        self.Name = Name
        self.Folder = Folder
        self.metadata = metadata

        self.tracks = wvtracks()
        parsers = [self.palybacks_dl([p], self.tracks) for p in palybacks]

        for t in thr3ad.processor_asynced(parsers, len(parsers)):
            if t.exc:
                self.logger.info(t.exc)

        tracks = self.tracks.filtering()

        if self.args.smart_select:
            selected = smart_select(tracks, resolution=self.args.resolution).select()
        elif self.args.select_by_asking:
            selected = select_by_asking(tracks).select(menu_style=self.config.SETTINGS.enable_menu_selection)
        else:
            selected = select_by_arguments(tracks, self.args).select()

        if self.args.license:
            self.perform_licensing(selected, Name, Folder)
            return

        # show_tracks(tracks, selected, selected_only=True)
        # self.logger.info(f"\nTitle: {self.Name}")
        show_tracks(tracks, selected, title=(self.Name, asin), selected_only=True)

        if self.args.prompt:
            while True:
                print()
                prompts = [
                    inquirer.List('answer', message="Are you satisfied with your selected tracks?",
                    choices=["YES", "SELECT_ALL", "SELECT_VIDEO", "SELECT_AUDIO", "SELECT_SUBTITLE", "SKIP"],
                    ),
                ]

                answer = inquirer.prompt(prompts)

                if answer.get("answer") == "YES":
                    self.downloadItem(self.Name, self.Folder, selected)
                    return
                elif answer.get("answer") == "SKIP":
                    self.logger.info(f"\nSkippin download...")
                    return
                else:
                    selected = select_by_asking(tracks).select(menu_style=self.config.SETTINGS.enable_menu_selection,
                                                            previous_selection=selected,
                                                            select_by=answer.get("answer"))
                    show_tracks(tracks, selected, title=(self.Name, asin), selected_only=True)

        self.downloadItem(self.Name, self.Folder, selected)

        return

    def asin_metadata(self, asin, region):
        metadata = {}

        metadata_filename = f"{asin}-{region}.metadata"

        if not os.path.isfile(metadata_filename):
            metadata = self.prime.RequestPlayBackWeb(asin, region, "CVBR", chpaters=True)
            with open(metadata_filename, "w") as f:
                f.write(json.dumps(metadata, indent=4))

        return json.load(open(metadata_filename, "r"))

    def asin_download(self, asin, region):
        playbacks = []
        metadata = self.asin_metadata(asin, region)

        if self.args.android_mode:
            if self.args.primevideo_sd:
                raise ValueError("Do not use argument `--sd` with android mode...")

            token_file = self.get_token_file(region)
            playbacks.append(self.prime.RequestPlayBackAndroid(asin, region, self.args.video_profile, token_file))
            playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "CVBR", sd=False, audio_only=True))
            playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "HEVC", sd=False, audio_only=True))

            return metadata, playbacks

        elif self.args.video_profile in ["AVC", "HEVC", "CBR", "CVBR"]:
            if self.args.video_profile == "AVC":
                playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "CBR", sd=self.args.primevideo_sd))
                playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "CVBR", sd=self.args.primevideo_sd))
                playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "HEVC", sd=False, audio_only=True))
            else:
                playbacks.append(self.prime.RequestPlayBackWeb(asin, region, self.args.video_profile, sd=self.args.primevideo_sd))
                if not self.args.video_profile == "CVBR":
                    playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "CVBR", sd=False, audio_only=True))
                    playbacks.append(self.prime.RequestPlayBackWeb(asin, region, "HEVC", sd=False, audio_only=True))

            return metadata, playbacks

        return None, None

    def main(self):
        self.prime = prime()
        self.download_dir.GoTo_MainFolder()

        if self.args.android_mode and self.args.video_profile in ["AVC", "HEVC", "CBR", "CVBR"]:
            raise ValueError(f"please request UHD + HDR only with android mode...")

        if self.args.video_profile and self.args.video_profile not in ["AVC", "HEVC", "HDR", "UHD", "CBR", "CVBR", "DOLBY_VISION"]:
            raise ValueError(f"argument `--video-profile` {self.args.video_profile} not supported...")

        if self.args.asin and not self.args.region:
            raise ValueError("argument `--region` needed when you download with asin...")

        if self.args.asin:
            asin_regions = ["uk", "de", "us", "jp", "eu", "ca", "na", "fe"]
            if not self.args.region in asin_regions:
                self.logger.info("\ncountry region needed for `prime` when you download with asin")
                self.logger.info("\nprobably your country is: eu")
                while self.args.region not in asin_regions:
                    self.args.region = input("Please select your current region from -> {} : ".format(", ".join(asin_regions)))

            cookies_file = self.get_cookies_file(self.args.region)
            self.prime.CookieJar(cookies_file)

            metadata, palybacks = self.asin_download(self.args.asin, self.args.region)

            if not metadata or not palybacks:
                raise ValueError("This can't be true...")

            if metadata["metadata"]["Type"] == "MOVIE":
                Name, Folder = self.args.title.strip() if self.args.title else self.ripprocess.RemoveCharcters(metadata["metadata"]["Title"]), None
                self.getItem(self.args.asin, metadata, palybacks, Name, Folder)
                return

            elif metadata["metadata"]["Type"] == "EPISODE":
                Name = "{} S{}E{} {}".format(
                    self.args.title.strip() if self.args.title else self.ripprocess.RemoveCharcters(metadata["metadata"]["ShowTitle"]),
                    str(metadata["metadata"]["SeasonNumber"]).zfill(2),
                    str(metadata["metadata"]["EpisodeNumber"]).zfill(2),
                    self.ripprocess.RemoveCharcters(metadata["metadata"]["Title"]),
                )
                Folder = "{} S{}".format(
                    self.args.title.strip() if self.args.title else self.ripprocess.RemoveCharcters(metadata["metadata"]["ShowTitle"]),
                    str(metadata["metadata"]["SeasonNumber"]).zfill(2),
                )
                self.getItem(self.args.asin, metadata, palybacks, Name, Folder)
                return

            return

        if self.args.content and self.args.content.startswith("http"):
            self.logger.info("\nGetting Metadata (API)")
            Url = self.args.content
            region = self.prime.metadata.Region(Url)
            cookies_file = self.get_cookies_file(region)
            self.prime.CookieJar(cookies_file)

            metadata_ = self.prime.RequestMeta(Url)

            if self.args.show_asin:
                if metadata_["type"] == "movie":
                    title = "{} {}".format(self.ripprocess.RemoveCharcters(metadata_["title"]), metadata_["year"])
                    print(f"python3.9 --asin \"{metadata_['asin']}\" -r \"{metadata_['region']}\" --out \"{title}\"")
                    return

                for e in metadata_["episodes"]:
                    title = "{} S{}E{} {}".format(
                        self.ripprocess.RemoveCharcters(e["tv_title"]),
                        str(e["season_number"]).zfill(2),
                        str(e["episode_number"]).zfill(2),
                        self.ripprocess.RemoveCharcters(e["title"]),
                    )
                    print(f"python3.9 --asin \"{e['asin']}\" -r \"{metadata_['region']}\" --out \"{title}\"")

                return

            if metadata_["type"] == "movie":
                Name, Folder = self.args.title.strip() if self.args.title else "{} {}".format(self.ripprocess.RemoveCharcters(metadata_["title"]), metadata_["year"]), None
                metadata, palybacks = self.asin_download(metadata_["asin"], metadata_["region"])
                self.getItem(metadata_["asin"], metadata, palybacks, Name, Folder)
                return

            self.items = list()

            seasonMatchNumber = (
                self.EpisodesNumbersHandler.sortNumbers(str(self.args.season).lstrip("0"))
                if self.args.season
                else self.EpisodesNumbersHandler.sortNumbers(str(input("ENTER Season Number: ").strip()).lstrip("0"))
            )

            AllowedEpisodesNumbers = (
                self.EpisodesNumbersHandler.sortNumbers(
                    str(self.args.episodeStart).lstrip("0")
                )
                if self.args.episodeStart
                else self.EpisodesNumbersHandler.sortNumbers("~")
            )

            for e in metadata_["episodes"]:
                if e["season_number"] in seasonMatchNumber and e["episode_number"] in AllowedEpisodesNumbers:
                    self.items.append(e)

            self.logger.info("\nTotal items will be downloaded : {}".format(len(self.items)))

            for idx, Episode in enumerate(self.items, start=1):
                self.logger.info("\nRipping : {} of {}".format(str(idx).zfill(2), str(len(self.items)).zfill(2)))
                metadata, palybacks = self.asin_download(Episode["asin"], metadata_["region"])
                self.tv_show_name = self.ripprocess.RemoveCharcters(metadata["metadata"]["ShowTitle"])
                Name = "{} S{}E{} {}".format(
                    self.args.title.strip() if self.args.title else self.ripprocess.RemoveCharcters(metadata["metadata"]["ShowTitle"]),
                    str(metadata["metadata"]["SeasonNumber"]).zfill(2),
                    str(metadata["metadata"]["EpisodeNumber"]).zfill(2),
                    self.ripprocess.RemoveCharcters(metadata["metadata"]["Title"]),
                )
                Folder = "{} S{}".format(
                    self.args.title.strip() if self.args.title else self.ripprocess.RemoveCharcters(metadata["metadata"]["ShowTitle"]),
                    str(metadata["metadata"]["SeasonNumber"]).zfill(2),
                )
                self.getItem(Episode["asin"], metadata, palybacks, Name, Folder)


        return
