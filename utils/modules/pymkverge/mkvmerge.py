import contextlib
import glob
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from utils.modules.pymkverge.exceptions import (
    UnknownLanguage,
    mediainfoError,
    mkvmergeError,
)
from utils.modules.pymkverge.utils import (
    mkvmerge_command,
    other_media_files,
    output_headers,
    utils,
    clean_filename,
)


class mkvmerge:
    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.kwargs = kwargs
        self.utils = utils()
        self.muxer, self.mkvmerge_exe = self.utils.muxer_config()
        self.language_code_file = self.muxer.LANGUAGE_CODE_LIST
        self.command = []
        self.trackid = str("0")
        self.exit_code = 1

    def options(self, title, default_duration=None):
        self.default_duration = default_duration
        self.title = title
        return

    def load_audio_subtitle_files(self):
        files = other_media_files(self.title, self.language_code_file)
        return files.collect_audio_subtitle_files()

    def get_output_file_path(self):
        return self.outputfile

    def start_muxing(self):
        self.logger.debug("Muxing command: {}".format(self.command))
        if not os.path.isfile(self.outputfile):
            command = mkvmerge_command(self.command)
            command.run()
            self.exit_code = 0
        else:
            self.logger.info("\nFile has been muxed before, muxing skipped.")
            self.exit_code = 0

        return

    def settings(
        self,
        inputfile,
        seasonfolder=None,
        outputfolder=None,
        source=None,
        scheme=None,
        group=None,
        defaults=None,
        extra_mkvmerge_params=None,
        tv_show_name=None
    ):
        self.source = source
        self.outputfolder = outputfolder
        self.tv_show_name = tv_show_name
        self.scheme = scheme if scheme else self.muxer.SCHEME
        self.group = group if group else self.muxer.GROUP
        self.defaults = self.parse_defautls(defaults)

        self.tracks = self.load_audio_subtitle_files()
        headers = output_headers(inputfile, seasonfolder, self.tracks)
        self.configuration = headers.get_headers()
        self.create_input_output_task(inputfile)
        self.append_tracks_to_muxer()
        self.is_any_chapters_file()
        self.add_extra_mkvmerge_params(extra_mkvmerge_params)
        return

    def set_scheme_to_filename(self, title):
        if not self.scheme in self.muxer.SCHEMES:
            raise mkvmergeError("Unknown scheme: {}".format(self.scheme))

        name = self.muxer.SCHEMES[self.scheme]
        name = name.replace("{t}", self.clean_title(title))
        name = name.replace("{r}", self.configuration["r"])
        name = name.replace("{s}", self.source)
        name = name.replace("{ac}", self.configuration["ac"])
        name = name.replace("{vc}", self.configuration["vc"])
        name = name.replace("{gr}", self.group)
        for _ in range(10):
            name = re.sub(" +", ".", name)
            name = re.sub(r"(\.\.)", ".", name)
        return name

    def parse_defautls(self, defaults):
        """
        default_audio|forced_audio|default_subtitle|forced_subtitle\n
        "eng|none|ara|eng"
        """

        try:
            (
                default_audio,
                forced_audio,
                default_subtitle,
                forced_subtitle,
            ) = defaults.split("|")
        except Exception:
            default_audio, forced_audio, default_subtitle, forced_subtitle = (
                "none",
                "none",
                "none",
                "none",
            )

        return {
            "default_audio": default_audio.strip(),
            "forced_audio": forced_audio.strip(),
            "default_subtitle": default_subtitle.strip(),
            "forced_subtitle": forced_subtitle.strip(),
        }

    def delete_episode_title(self, title):
        regex = re.compile("(.*) [S]([0-9]+)[E]([0-9]+)")
        if regex.search(title):
            return regex.search(title).group(0)

        return title

    def create_input_output_task(self, inputfile):

        self.outputfile = self.set_scheme_to_filename(
            self.delete_episode_title(self.title)
            if self.muxer.DELETE_EPISODE_TITLE
            else self.title
        )

        out = Path(self.outputfile)
        if self.outputfolder:
            parent = Path(self.outputfolder)
            if self.tv_show_name:
                parent = parent / self.tv_show_name
            if self.configuration["folder"]:
                parent = parent / self.set_scheme_to_filename(self.configuration["folder"])
            out = parent / out

        if self.configuration["folder"] and not self.outputfolder:
            parent = self.set_scheme_to_filename(self.configuration["folder"])
            parent = Path(parent)
            if self.tv_show_name:
                parent = parent / self.tv_show_name
            out = parent / out

        self.outputfile = str(out)

        if not self.outputfile.endswith(".mkv"):
            self.outputfile = "{}.mkv".format(self.outputfile)

        self.command.append(self.mkvmerge_exe)
        self.command.append("--output")
        self.command.append(self.outputfile)
        if self.default_duration:
            self.command.append("--default-duration")
            self.command.append(self.default_duration)
        self.command.append("--language")
        self.command.append("0:und")
        self.command.append("--default-track")
        self.command.append("0:yes")
        self.command.append("(")
        self.command.append(inputfile)
        self.command.append(")")

    def clean_title(self, title):
        name = clean_filename()
        return name.clean(title)

    def is_any_chapters_file(self):
        chapfile = "%s - Chapters.txt" % self.title
        if os.path.isfile(chapfile):
            self.command.append("--chapter-charset")
            self.command.append("UTF-8")
            self.command.append("--chapters")
            self.command.append(chapfile)

    def add_extra_mkvmerge_params(self, extra_mkvmerge_params):
        if extra_mkvmerge_params:
            params = self.utils.parse_extra_params(extra_mkvmerge_params)
            self.logger.debug("mkvmerge.exe extra params: {}".format(params))
            self.command.extend(params)

    def add_subtitle_file(
        self,
        subfile,
        trackname,
        language,
        forced=False,
        default=False,
        compression="none",
        trackid="0",
    ):

        self.command.append("--language")
        self.command.append(f"{trackid}:{language}")
        self.command.append("--track-name")
        self.command.append(f"{trackid}:{trackname}")
        self.command.append("--forced-track")
        self.command.append(f"{trackid}:yes" if forced else f"{trackid}:no")
        self.command.append("--default-track")
        self.command.append(f"{trackid}:yes" if default else f"{trackid}:no")
        self.command.append("--compression")
        self.command.append(f"{trackid}:{compression}")
        self.command.append("(")
        self.command.append(subfile)
        self.command.append(")")

    def add_audio_file(
        self, audiofile, trackname, language, forced=False, default=False, trackid="0",
    ):

        self.command.append("--language")
        self.command.append(f"{trackid}:{language}")
        self.command.append("--track-name")
        self.command.append(f"{trackid}:{trackname}")
        self.command.append("--forced-track")
        self.command.append(f"{trackid}:yes" if forced else f"{trackid}:no")
        self.command.append("--default-track")
        self.command.append(f"{trackid}:yes" if default else f"{trackid}:no")
        self.command.append("(")
        self.command.append(audiofile)
        self.command.append(")")

    def append_tracks_to_muxer(self):
        for track in sorted(self.tracks["audios"], key=lambda t: t["language"]):
        # for track in self.tracks["audios"]:
            audiofile = track["audiofile"]
            trackname = track["trackname"]
            language = track["language"]
            forced = track["forced"]
            default = track["default"]

            if track["track_language_name"] == self.defaults["default_audio"]:
                default = True

            if track["track_language_name"] == self.defaults["forced_audio"]:
                forced = True

            self.add_audio_file(
                audiofile=audiofile,
                trackname=trackname,
                language=language,
                forced=forced,
                default=default,
            )

        for track in sorted(self.tracks["subtitles"], key=lambda t: t["language"]):
        # for track in self.tracks["subtitles"]:
            subfile = track["subfile"]
            trackname = track["trackname"]
            language = track["language"]
            forced = track["forced"]
            default = track["default"]

            if track["track_language_name"] == self.defaults["default_subtitle"]:
                default = True

            if track["track_language_name"] == self.defaults["forced_subtitle"]:
                forced = True

            self.add_subtitle_file(
                subfile=subfile,
                trackname=trackname,
                language=language,
                forced=forced,
                default=default,
            )
