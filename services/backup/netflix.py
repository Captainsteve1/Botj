import argparse
import asyncio
import configparser
import glob
import json
import logging
import multiprocessing
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
from helpers.Parsers.netflix.License import License
from helpers.Parsers.netflix.Manifest import Manifest
from helpers.Parsers.netflix.Metadata import Metadata
from helpers.tracks import (select_by_arguments, select_by_asking, show_tracks,
                            smart_select)
from helpers.Utils.keyloader import keyloader
from helpers.Utils.ripprocess import EpisodesNumbersHandler, ripprocess
from helpers.Utils.utils import WhenDownloadFinish, download_dir
from helpers.Utils.vpn import connect
from helpers.wvdownloader import Aria2c, SubtitleHelper, VideoHelper
# # from pywidevine.cdm import cdm, deviceconfig
from pywidevine.decrypt.wvdecryptcustom import WvDecrypt

try:
    from helpers.Utils.Packer import release

    doPacking = True
except ModuleNotFoundError:
    doPacking = False
    pass


class netflix:
    def __init__(self, args, commands):
        self.logger = logging.getLogger(__name__)
        self.args = args
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.SERVICE = self.config.SERVICES.NETFLIX
        self.device = self.config.DEVICES.NETFLIX
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

        self.key_thread = None
        self.threads_keys = []
        self.tv_show_name = None

    def get_nfid(self, content_id):
        if content_id.isdigit():
            return int(content_id)

        return next((x for x in re.search(r"title/(\d+)|watch/(\d+)|jbv=(\d+)", content_id).groups() if x is not None)) if re.search(r"title/(\d+)|watch/(\d+)|jbv=(\d+)", content_id) else re.search(r"[0-9]{8}$", content_id).group()

    def GetKeys(self, IDNet, profilename):
        self.logger.info("\nGetting KEYS...")
        video_keys = []

        NetflixLicense = License(IDNet, profilename)
        # video_keys = NetflixLicense.get_keys()

        # if profilename in ["HIGH", "HDR", "HEVC"]:
        #     video_keys = NetflixLicense.get_keys_chrome(self.COOKIES["NetflixId"], self.COOKIES["SecureNetflixId"])
        # else:
        #     video_keys = NetflixLicense.get_keys()

        video_keys = NetflixLicense.get_keys()
        video_keys = list(set(video_keys))
        video_keys = [profilename] + video_keys

        return video_keys

    def decryptFile(self, encrypted, decrypted, Codec=None, Track=None, Type="VIDEO"):
        if isfile(decrypted):
            return

        if not isfile(encrypted):
            raise FileNotFoundError(encrypted)

        if self.key_thread is not None:
            self.key_thread.join()

        KID = self.keyloader.generate_kid(encrypted)
        KEYS = self.keyloader.get_key_by_kid(KID)
        KEYS += self.threads_keys

        if KEYS == []:
            if Track.Extras["NFProfile"] in ["MAIN", "HIGH", "HDR", "DOLBY_VISION", "HEVC"]:
                KEYS = self.GetKeys(self.netflixId, Track.Extras["NFProfile"])
            else:
                KEYS = self.manifest.get_keys(self.netflixId, Track.Extras["NFProfile"], None)
            # KEYS = self.manifest.get_keys(self.netflixId, Track.Extras["NFProfile"], Track.PSSH)
            if not KEYS == []:
                KEYS = self.keyloader.add_keys(
                    keys=[key for key in KEYS if ":" in key], pssh=None, name=self.Name
                )

        # if not KEYS == []:
            # if not [x for x in KEYS if x["KID"] == KID] == []:
                # KEYS = [x for x in KEYS if x["KID"] == KID]

            # self.VideoHelper.mp4decryptor(
                # encrypted=encrypted,
                # decrypted=decrypted,
                # keys=KEYS,
                # pandsdecryptor=True,
                # kid=True,
            # )

            # return True

        # return False
        
        if not KEYS == []:
            if self.args.shaka_decrypt and Type.lower() == "video":
                self.VideoHelper.shakadecryptor2(encrypted=encrypted, decrypted=decrypted, keys=KEYS, stream=Type.lower())
                return

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
            if self.args.shaka_decrypt or self.SERVICE.NAME.lower() in list(
                map(lambda x: x.lower(), self.config.SETTINGS.skip_video_demux)
            ):
                os.rename(decrypted, cleaned)
                return

            self.VideoHelper.ffmpegclean(decrypted=decrypted, cleaned=cleaned)

        if Type == "AUDIO":
            self.VideoHelper.ffmpegcleanAudio(Input=decrypted)

        return

    def perform_licensing(self, Name, Folder):

        KEYS = []
        if self.args.video_profile == "HEVC":
            KEYS += self.GetKeys(self.netflixId, "HEVC")
        elif self.args.video_profile == "HDR":
            KEYS += self.GetKeys(self.netflixId, "HDR")
        elif self.args.video_profile == "VP9":
            KEYS += self.GetKeys(self.netflixId, "VP9")
        elif self.args.video_profile == "DOLBY_VISION":
            KEYS += self.GetKeys(self.netflixId, "DOLBY_VISION")
        else:
            for profile in ["MAIN", "HIGH"]:
                KEYS += self.GetKeys(self.netflixId, profile)

        self.logger.info(f"\n{Name} KEYS\n")
        self.logger.info("\n".join(KEYS))
        KEYS = [x for x in KEYS if ":" in x]
        if not KEYS == []:
            KEYS = self.keyloader.add_keys(keys=KEYS, pssh=None, name=Name)

            return

    def SubtitleProcessor(self, Name, Track):
        sub = "{} {}-{}.sub".format(Name, Track.Language, Track.Type.lower())
        srt = "{} {}-{}.srt".format(Name, Track.Language, Track.Type.lower())

        if Track.DownloadType == "URL" and not isfile(srt):
            self.SubtitleHelper.SubtitleDownloader(Url=Track.Url, Output=sub)
            self.SubtitleHelper.SubtitleConverter(Input=sub, Output=srt, Type=Track.Profile)
            self.SubtitleHelper.TimeCodesFix(srt, srt)
            if Track.Language == "ara":
                self.SubtitleHelper.ReverseRtl(Input=srt, Output=srt)

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

    def get_keys_with_thread(self, Track):
        KEYS = self.GetKeys(self.netflixId, Track.Extras["NFProfile"])
        if KEYS != []:
            KEYS = self.keyloader.add_keys(
                keys=[key for key in KEYS if ":" in key], pssh=None, name=self.Name
            )

        self.threads_keys += KEYS
        return

    def downloadItem_thread(self, Name, Folder, Tracks):
        self.key_thread = Thread(target=self.get_keys_with_thread, args=(Tracks.Videos[0], ),)
        self.key_thread.start()

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

                    self.decryptFile(
                        video_encrypted, video_decrypted, Track=Track
                    )
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

                    self.decryptFile(
                        audio_encrypted, audio_decrypted, Track=Track
                    )
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

    def getItem(self, netflixId, Name, Folder):
        self.netflixId = netflixId
        self.Name = Name
        self.Folder = Folder

        if self.args.license:
            self.perform_licensing(self.Name, self.Folder)
            return

        self.manifest = Manifest(
            netflixId=self.netflixId,
            video_profile="M/HPL" if self.args.video_profile == "AVC" else self.args.video_profile,
            audio_profile=self.args.audio_profile,
            resolution=self.args.resolution,
        )

        tracks = self.manifest.getPlayback()

        if self.args.smart_select:
            selected = smart_select(tracks, resolution=self.args.resolution).select()
        elif self.args.select_by_asking:
            selected = select_by_asking(tracks).select(menu_style=self.config.SETTINGS.enable_menu_selection)
        else:
            selected = select_by_arguments(tracks, self.args).select()

        show_tracks(tracks, selected, title=(self.Name, self.netflixId), selected_only=True)
        # self.logger.info(f"\nTitle: {self.Name}")

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
                    show_tracks(tracks, selected, title=(self.Name, self.netflixId), selected_only=True)

        self.downloadItem(self.Name, self.Folder, selected)

        return

    def main(self):
        self.Metadata = Metadata(
            self.SERVICE.email, self.SERVICE.password, self.SERVICE.cookies_file
        )
        self.COOKIES, self.BUILD_IDENTIFIER = self.Metadata.client()
        self.NFID = self.get_nfid(self.args.content)

        self.download_dir.GoTo_MainFolder()  ## changedir

        self.logger.info("Getting Metadata...")
        data = self.Metadata._get(
            str(self.NFID),
            self.COOKIES,
            self.BUILD_IDENTIFIER,
            self.SERVICE.metada_language,
        )

        if data is None:
            raise ValueError("Unknown metadata...")

        if data["video"]["type"] == "movie":
            self.netflixType = "movie"
        else:
            if data["video"]["type"] == "show":
                self.netflixType = "show"
            else:
                if data["video"]["type"] == "supplemental":
                    self.netflixType = "supplemental"
                else:
                    self.logger.info(data["video"]["type"] + " is a unrecognized type!")
                    sys.exit(0)

        self.items = []
        isAEpisode = False

        if self.netflixType == "movie" or self.netflixType == "supplemental":
            mainTitle = "{} {}".format(
                self.ripprocess.RemoveCharcters(data["video"]["title"]),
                self.ripprocess.RemoveCharcters(str(data["video"]["year"])),
            )
        else:
            mainTitle = self.ripprocess.RemoveCharcters(data["video"]["title"])

        self.tv_show_name = mainTitle

        try:
            if (
                str(data["video"]["currentEpisode"]) == str(self.NFID)
                and self.netflixType == "show"
            ):
                isAEpisode = True
        except Exception:
            pass

        if self.netflixType == "movie" or self.netflixType == "supplemental":
            self.getItem(
                self.NFID,
                self.args.title.strip() if self.args.title else mainTitle,
                None,
            )
            return

        elif self.netflixType == "show":
            NfSeasons = []
            for season in data["video"]["seasons"]:
                SeasonNumber = int(season["seq"])
                Episodes = []
                for episode in season["episodes"]:
                    EpisodeNumber = int(episode["seq"])
                    E = {
                        "EpisodeNumber": EpisodeNumber,
                        "SeasonNumber": SeasonNumber,
                        "TitleName": "{} S{}E{} {}".format(
                            self.args.title.strip() if self.args.title else mainTitle,
                            str(SeasonNumber).zfill(2),
                            str(EpisodeNumber).zfill(2),
                            self.ripprocess.RemoveCharcters(episode["title"]),
                        ),
                        "FolderName": "{} S{}".format(
                            self.args.title.strip() if self.args.title else mainTitle,
                            str(SeasonNumber).zfill(2),
                        ),
                        "NetflixID": episode["episodeId"],
                    }
                    Episodes.append(E)
                S = {
                    "SeasonNumber": SeasonNumber,
                    "Episodes": Episodes,
                }
                NfSeasons.append(S)

            NfSeasons = sorted(NfSeasons, key=lambda k: int(k["SeasonNumber"]))

            if isAEpisode:
                self.logger.info("\nID or URL belongs to episode...")
                for season in NfSeasons:
                    for episode in season["Episodes"]:
                        if int(episode["NetflixID"]) == int(self.NFID):
                            self.items.append(episode)

            else:
                seasonMatchNumber = (
                    str(self.args.season).lstrip("0")
                    if self.args.season
                    else str(input("ENTER Season Number: ").strip()).lstrip("0")
                )

                AllowedEpisodesNumbers = (
                    self.EpisodesNumbersHandler.sortNumbers(
                        str(self.args.episodeStart).lstrip("0")
                    )
                    if self.args.episodeStart
                    else self.EpisodesNumbersHandler.sortNumbers("~")
                )

                # if int(seasonMatchNumber) > int(len(NfSeasons)):
                #     self.logger.info(
                #         "Season not found: only {} available.".format(
                #             int(len(NfSeasons))
                #         )
                #     )
                #     return

                for season in NfSeasons:
                    if int(season["SeasonNumber"]) == int(seasonMatchNumber):
                        for episode in season["Episodes"]:
                            if int(episode["EpisodeNumber"]) in AllowedEpisodesNumbers:
                                self.items.append(episode)

        self.logger.info("\nTotal items will be downloaded : {}".format(len(self.items)))
        for idx, episode in enumerate(self.items, start=1):
            self.logger.info("\nRipping : {} of {}".format(str(idx).zfill(2), str(len(self.items)).zfill(2)))
            self.getItem(episode["NetflixID"], self.ripprocess.RemoveCharcters(episode["TitleName"]), episode["FolderName"])
