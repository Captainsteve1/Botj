import contextlib
import glob
import json
import logging
import os
import re
import subprocess
import sys

from pymediainfo import MediaInfo

from configs.config import wvripper_config
from utils.modules.pymkverge.exceptions import (
    UnknownLanguage,
    mediainfoError,
    mkvmergeError,
)

class utils:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()

    def muxer_config(self):
        return self.config.MUXER, self.config.BIN.mkvmerge

    def Binaries(self):
        return self.config.BIN

    def mediainfo(self, file: str):
        return [track for track in MediaInfo.parse(file)]

    def parse_extra_params(self, cmd, separator_tag="*"):
        if not cmd:
            return []
        return [x.strip() for x in cmd.split(separator_tag) if x.strip() != ""]


class output_headers:
    def __init__(self, inputfile, seasonfolder, media):
        self.logger = logging.getLogger(__name__)
        self.utils = utils()
        self.inputfile = inputfile
        self.seasonfolder = seasonfolder
        self.media = media

    def get_info(self, file):
        mediainfo_output = subprocess.Popen(
            [self.utils.Binaries().MediaInfo, "--Output=JSON", "-f", file],
            stdout=subprocess.PIPE,
        )
        return json.load(mediainfo_output.stdout)

    def is_hdr(self, video_track):
        if video_track.get(
            "HDR_Format"
            ) or video_track.get(
            "HDR_Format_Version"
            ) or video_track.get(
            "color_primaries", "none"
            ) == "BT.2020" or video_track.get(
            "HDR_Format_Compatibility", "none"
            ) == "HDR10" or "hdr10" in [p.strip() for p in video_track.get(
            "encoding_settings", "none").split("/")] or video_track.get(
            "format_profile", "none").lower().__contains__("main 10"):
            return True

        return False

    def resolution(self, w, h):
        res_list = [240, 360, 480, 576, 720, 1080, 1440, 2160]
        res = int(w * (9 / 16))
        resolution = res_list[min(range(len(res_list)),
            key=lambda i: abs(res_list[i]-res))]

        if resolution >= 720:
            return resolution


        # if h in [720, 1080, 1440, 2160]: return h
        # if w >= 3840: return 2160
        # if w == 1920 or h == 1080: return 1080
        # if  w == 1280 or h == 720: return 720
        # if w > 1920:
        #     if h > 1440: return 2160
        #     return 1440
        # if w < 1400 and w >= 1100: return 720
        # if h >= 800: return 1080
        # if h < 800 and h >= 600: return 720

        # if w >= 3840:
        #     return "2160p"

        # if w >= 2560:
        #     return "1440p"

        # if w == 1920 or h == 1080:
        #     return "1080p"

        # if  w == 1280 or h == 720:
        #     return "720p"

        # if w > 1920:
        #     if h > 1440:
        #         return "2160p"
        #     return "1440p"

        # if w < 1400 and w >= 1100:
        #     return "720p"

        # if h >= 800:
        #     return "1080p"

        # if h < 800 and h >= 600:
        #     return "720p"

        return ""

    def get_highest_audio_available(self):
        if self.media["audios"] == []:
            raise mediainfoError("No audio tracks loaded.")

        files_list = []
        for file in self.media["audios"]:
            file = file["audiofile"]
            size = os.path.getsize(file)
            files_list.append({"file": file, "size": size})

        return sorted(files_list, key=lambda k: int(k["size"]))[-1]["file"]

    def audio_codec_parse(self):
        audiofile = self.get_highest_audio_available()
        data = self.get_info(audiofile)
        audio_track = [x for x in data["media"]["track"] if x["@type"] == "Audio"]

        if audio_track == []:
            raise mediainfoError(
                "Error getting track info for this file: {}".format(audiofile)
            )

        audio_track = audio_track[0]

        if audio_track["Format"] == "E-AC-3":
            codec = "DDP"
        elif audio_track["Format"] == "AC-3":
            codec = "DD"
        elif audio_track["Format"] == "AAC":
            codec = "AAC"
        elif audio_track["Format"] == "DTS":
            codec = "DTS"
        elif "DTS" in audio_track["Format"]:
            codec = "DTS"
        else:
            codec = "DDP"

        if int(audio_track["Channels"]) == 8:
            ch = "7.1"
        elif int(audio_track["Channels"]) == 6:
            ch = "5.1"
        elif int(audio_track["Channels"]) == 2:
            ch = "2.0"
        elif int(audio_track["Channels"]) == 1:
            ch = "1.0"
        else:
            ch = "5.1"

        if "Dolby Atmos" in str(audio_track):
            ac = "{}{}.{}".format(codec, ch, "Atmos")
        else:
            ac = "{}{}".format(codec, ch)

        return ac

    def video_codec_parse(self, video_track):

        if "avc" in (codec := video_track["Format"].lower()):
            if video_track.get("Encoded_Library_Name") or video_track.get("Encoded_Library_Settings"):
                return "x264"
            return "H.264"
        elif "hev" in codec or "hvc" in codec:
            if self.is_hdr(video_track):
                return "HDR.HEVC"
            return "HEVC"
        else:
            raise mediainfoError("Unknown Codec: {}".format(codec) )
        # codec = video_track.get("CodecID")
        # if not codec: codec = video_track.get("Format")
        # codec = codec.lower()

        # if "avc" in codec:
        #     if video_track.get("Encoded_Library_Name") or video_track.get("Encoded_Library_Settings"):
        #         return "x264"
        #     return "H.264"

        # elif "hev" in codec or "hvc" in codec:
        #     if self.is_hdr(video_track):
        #         return "HDR HEVC"
        #     return "HEVC"
        # else:
        #     raise mediainfoError(
        #         "Unknown Codec: {}".format(codec)
        #     )

        return None

    def get_headers(self):
        data = self.get_info(self.inputfile)
        video_track = [x for x in data["media"]["track"] if x["@type"] == "Video"]
        if video_track == []:
            raise mediainfoError(
                "Error getting track info for this file: {}".format(self.inputfile)
            )
        else:
            video_track = video_track[0]

        r = str(self.resolution(int(video_track["Width"]), int(video_track["Height"])))
        r = r + "p" if r else r

        return {
            "w": video_track["Width"],
            "h": video_track["Height"],
            "r": r,
            "vc": self.video_codec_parse(video_track),
            "ac": self.audio_codec_parse(),
            "folder": self.seasonfolder,
        }


class other_media_files:
    def __init__(
        self, title, language_code_file,
    ):
        self.logger = logging.getLogger(__name__)
        self.title = title
        self.language_code_file = language_code_file
        self.Languages_Json = self.Languages_Json_File_Reader()
        self.allowed_extensions = [
            "eac3",
            "ac3",
            "aac",
            "m4a",
            "dts",
            "ogg",
            "mp4",
            "srt",
            "ass",
        ]

    def Languages_Json_File_Reader(self):
        with open(self.language_code_file, "r") as f:
            Languages_Json = json.loads(f.read())

        # return codes["ISO 639-2"] + codes["ISO 639-1"]
        return Languages_Json

    def get_files(self):
        files = glob.glob("*.*")
        wanted = []
        added = set()

        for extension in self.allowed_extensions:
            for file in files:
                if file.startswith(self.title) and file.endswith(extension):
                    if not file in added:
                        wanted.append(file)
                        added.add(file)

        return wanted

    def get_extension(self, file: str):
        return file.split(".")[-1]

    def is_exist(self, file: str):
        if os.path.isfile(file):
            return True
        return False

    def get_trackname_tag(self, name, Type):
        if self.Languages_Json["Tags"][Type].strip() == "":
            return name

        return "{} {}".format(name, self.Languages_Json["Tags"][Type])

    def format_sub_file(self, subfile):

        SUBTITLE = "{} {}-subtitle.srt"
        FORCED = "{} {}-forced.srt"
        CC = "{} {}-cc.srt"
        SDH = "{} {}-sdh.srt"

        for _, lang, iso, title, in self.Languages_Json["Languages"]["ISO 639-1"] + self.Languages_Json["Languages"]["ISO 639-2"]:
            if subfile == SUBTITLE.format(self.title, lang):
                language = iso
                trackname = self.get_trackname_tag(title, Type="SUBTITLE")
                subtitle_dict = {
                    "track_language_name": lang,
                    "subfile": subfile,
                    "trackname": trackname,
                    "language": language,
                    "forced": False,
                    "default": False,
                }

                return subtitle_dict
            elif subfile == FORCED.format(self.title, lang):
                language = iso
                trackname = self.get_trackname_tag(title, Type="FORCED")
                subtitle_dict = {
                    "track_language_name": lang,
                    "subfile": subfile,
                    "trackname": trackname,
                    "language": language,
                    "forced": True,
                    "default": False,
                }

                return subtitle_dict
            elif subfile == CC.format(self.title, lang):
                language = iso
                trackname = self.get_trackname_tag(title, Type="CC")
                subtitle_dict = {
                    "track_language_name": lang,
                    "subfile": subfile,
                    "trackname": trackname,
                    "language": language,
                    "forced": False,
                    "default": False,
                }

                return subtitle_dict
            elif subfile == SDH.format(self.title, lang):
                language = iso
                trackname = self.get_trackname_tag(title, Type="SDH")
                subtitle_dict = {
                    "track_language_name": lang,
                    "subfile": subfile,
                    "trackname": trackname,
                    "language": language,
                    "forced": False,
                    "default": False,
                }

                return subtitle_dict
                self.logger.info

        self.logger.info("MuxerWarning [Unknown language] {}".format(subfile))

        # raise UnknownLanguage("Unknown language {}.".format(subfile))

    def format_audio_file(self, audiofile):

        DIALOG = "{} {}-dialog.{}"
        COMMENTARY = "{} {}-commentary.{}"
        DESCRIPTIVE = "{} {}-descriptive.{}"

        for extension in ["eac3", "ac3", "aac", "m4a", "dts", "ogg", ""]:
            for _, lang, iso, title, in self.Languages_Json["Languages"]["ISO 639-1"] + self.Languages_Json["Languages"]["ISO 639-2"]:
                if audiofile == DIALOG.format(self.title, lang, extension):
                    language = iso
                    trackname = self.get_trackname_tag(title, Type="DIALOG")
                    audio_dict = {
                        "track_language_name": lang,
                        "audiofile": audiofile,
                        "trackname": trackname,
                        "language": language,
                        "forced": False,
                        "default": False,
                    }

                    return audio_dict
                elif audiofile == COMMENTARY.format(self.title, lang, extension):
                    language = iso
                    trackname = self.get_trackname_tag(title, Type="COMMENTARY")
                    audio_dict = {
                        "track_language_name": lang,
                        "audiofile": audiofile,
                        "trackname": trackname,
                        "language": language,
                        "forced": False,
                        "default": False,
                    }

                    return audio_dict
                elif audiofile == DESCRIPTIVE.format(self.title, lang, extension):
                    language = iso
                    trackname = self.get_trackname_tag(title, Type="DESCRIPTIVE")
                    audio_dict = {
                        "track_language_name": lang,
                        "audiofile": audiofile,
                        "trackname": trackname,
                        "language": language,
                        "forced": False,
                        "default": False,
                    }

                    return audio_dict

        self.logger.info("MuxerWarning [Unknown language] {}".format(audiofile))
        # raise UnknownLanguage("Unknown language {}.".format(audiofile))

    def collect_audio_subtitle_files(self):
        self.files = self.get_files()
        self.videos = []
        self.audios = []
        self.subtitles = []

        for file in self.files:
            if self.get_extension(file) in ["mp4"]:
                self.videos.append(file)
            if self.get_extension(file) in ["eac3", "ac3", "aac", "m4a", "dts", "ogg"]:
                self.audios.append(self.format_audio_file(file))
            if self.get_extension(file) in ["srt", "ass"]:
                self.subtitles.append(self.format_sub_file(file))

        return {
            "files": self.files,
            "videos": self.videos,
            "audios": self.audios,
            "subtitles": self.subtitles,
        }


class mkvmerge_command:
    def __init__(self, command):
        self.logger = logging.getLogger(__name__)
        self.command = command

    def run(self):
        proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )
        self.logger.info("\nStart Muxing...")
        for line in self.unbuffered(proc):
            if "Progress:" in line:
                sys.stdout.write("\r%s" % (line))
                sys.stdout.flush()
            elif "Multiplexing" in line:
                sys.stdout.write("\r%s" % (line.replace("Multiplexing", "Muxing")))
                sys.stdout.flush()
            elif "Error" in line:
                sys.stdout.write("\r%s" % (line))
                sys.stdout.flush()

        self.logger.info("")

    def unbuffered(self, proc, stream="stdout"):
        newlines = ["\n", "\r\n", "\r"]
        stream = getattr(proc, stream)
        with contextlib.closing(stream):
            while True:
                out = []
                last = stream.read(1)
                # Don't loop forever
                if last == "" and proc.poll() is not None:
                    break
                while last not in newlines:
                    # Don't loop forever
                    if last == "" and proc.poll() is not None:
                        break
                    out.append(last)
                    last = stream.read(1)
                out = "".join(out)
                yield out


class clean_filename:
    """"""

    def clean(self, filename: str):
        filename = filename.replace("-cleaned", "")

        # DO NOT EDIT HERE
        filename = re.sub(" +", ".", filename)
        filename = re.sub("-", ".", filename)

        for _ in range(10):
            filename = re.sub(r"(\.\.)", ".", filename)

        return filename
