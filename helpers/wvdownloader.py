import codecs
import json
import logging
import os
import re, platform
import subprocess
from datetime import datetime
from os.path import isfile
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union
from pathlib import Path
import requests
import tqdm
from configs.config import wvripper_config

import utils.modules.pycaption as pycaption
from helpers.Utils.aria2 import aria2
from helpers.Utils.ffmpeg import clean_audio, clean_mp4
from helpers.Utils.subtitle import (DFXPConverter, FixSubtitleTimeCodes,
                                    ReverseRtlStartEnd, SDHConverter,
                                    WebVTT2Srt)
from utils.probe import probe


def is_content_encrypted(data: str) -> Optional[bool]:
    for track in data.get("media").get("track"):
        if track.get("Encryption"): return True
        
    return False

class Tqdm:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def DownLoad(self, Url, Output, proxies=None, session=False):
        """Simpt Python downloader Using tqdm for progress bar"""
        s = session if session else requests
        r = s.get(Url, stream=True)
        file_size = int(r.headers["Content-Length"])
        chunk = 1
        chunk_size = 1024
        num_bars = int(file_size / chunk_size)

        with open(Output, "wb") as fp:
            for chunk in tqdm.tqdm(
                r.iter_content(chunk_size=chunk_size),
                total=num_bars,
                unit="KB",
                desc=Output,
                leave=True,
            ):
                fp.write(chunk)

        return

class Aria2c:
    def __init__(self,):
        self.logger = logging.getLogger(__name__)
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()

    def SaldDL(self):
        dir_ = os.getcwd().replace("\\", "/")
        out = self.Output

        command = [
            'saldl', '--resume',
            '--skip-TLS-verification', '--chunk-size=6m',
            '--connections=32', '-o', out # '-D', dir_, '-o', out
        ]

        if (proxies := list({key: value for key, value in os.environ.copy().items() if key in ["http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY"]}.values())):
            command.append(f"--proxy={proxies[0]}")

        command.append(self.Track.Url)

        if platform.system() == "Linux":
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError:
                raise ValueError("Saldl failed too many times, aborting")

        else:
            command = ['wsl'] + command
            batfile = f"{out}.bat"
            with open(batfile, "w") as bf:
                bf.write(" ".join(f"\"{c}\"" for c in command))

            subprocess.call([batfile], shell=False)

        return

    def UrlType(self,):

        if self.noaria2c:
            Tqdm_ = Tqdm()
            Tqdm_.DownLoad(self.Track.Url, self.Output, session=self.tqdm_session)
            return

        if self.saldl:
            self.SaldDL()
            return

        Ar2 = aria2()
        Ar2.Url(self.Track.Url, self.Output, self.extra_commands)

        return

    def DashType(self,):

        if self.noaria2c:
            self.logger.info("<noaria2c> does not works with DASH downloads.")
            confirm_using_aria2c_instead = input(
                "Do you want to use aria2c for downloading?: "
            ).strip()
            if confirm_using_aria2c_instead.startswith("n"):
                return

        Ar2 = aria2()
        Ar2.Dash(self.segments or self.Track.Segments, self.Output, self.extra_commands, self.fixbytes)

        return

    def DownLoad(
        self,
        Output,
        Track,
        noaria2c=False,
        saldl=False,
        fixbytes=False,
        extra_commands=[],
        segments=False,
        tqdm_session=False,
        quiet=False
    ):
        """
        @Output: Output filename.\n
        @Track: Track attributes.\n
        @noaria2c: do not use aria2c as main downloader, use tqdm: only for URL Type.\n
        @fixbytes: fix bytes for appletv atmos audios.\n
        @extra_commands: aria2c extra commands or proxies.\n
        @segments: will force use this segments instead of track.Segments: only for DASH type.\n
        @tqdm_session: add request session for tqdm downloader: only for URL type.\n
        """
        self.Output = Output
        self.Track = Track
        self.noaria2c = noaria2c
        self.saldl = saldl
        self.extra_commands = extra_commands
        self.fixbytes = fixbytes
        self.segments = segments
        self.tqdm_session = tqdm_session

        if isinstance(self.extra_commands, list):
            self.extra_commands = {}

        if isfile(self.Output) and not isfile("%s.aria2" % self.Output):
            return

        self.logger.info(f"\nDownloading: {self.Output}")
        self.logger.info(f"\nDownloading: {self.Track.Url}")

        if self.Track.DownloadType == "URL":
            self.UrlType()
        elif self.Track.DownloadType == "DASH":
            self.DashType()

        return


class VideoHelper:
    def __init__(self,):
        """VideoHelper: Hold the functions for decrypt/clean/demux videos."""
        self.logger = logging.getLogger(__name__)
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()

    def mediainfo(
        self,
        infile: Optional[str],
    ) -> Dict[str, Any]:
        args = [self.config.BIN.MediaInfo, "--Output=JSON", "-f", infile]
        stdout = subprocess.check_output(args, encoding="utf-8")
        return json.loads(stdout)

    def is_encrypted(self, file: str):
        if is_content_encrypted(self.mediainfo(file)):
            self.logger.info(f"File is Encrypted: {file}")
        return

    def getKeysMp4(self, decryptionKeys, kid=True):
        keys = []

        for key in decryptionKeys:
            keys.append("--key")
            keys.append("{}:{}".format(key["KID"] if kid else key["ID"], key["KEY"]))

        return keys

    def getKeysShaka(self, decryptionKeys):
        keys = []

        for key in decryptionKeys:
            keys.append("--keys")
            keys.append(
                "key={}:key_id={}".format(
                    key["KEY"], "00000000000000000000000000000000"
                )
            )

        return keys
        
    def getKeysShaka2(self, decryptionKeys):
        keys = []

        for key in decryptionKeys:
            keys.append("--keys")
            keys.append(
                "key={}:key_id={}".format(
                    key["KEY"], key["KID"]
                )
            )

        return keys

    def shakadecryptor(self, encrypted, decrypted, keys, stream):
        self.logger.info("\nDecrypting: {}".format(encrypted))
        self.logger.info("\n".join(["{}:{}".format(x["KID"], x["KEY"]) for x in keys]))
        wvdecrypt_process = subprocess.Popen(
            [
                self.config.BIN.shaka_packager,
                "--enable_raw_key_decryption",
                "-quiet",
                "input={},stream={},output={}".format(encrypted, stream, decrypted),
            ]
            + self.getKeysShaka(keys)
        )

        stdoutdata, stderrdata = wvdecrypt_process.communicate()
        wvdecrypt_process.wait()
        self.logger.info("Done!")

        return
        
    def shakadecryptor2(self, encrypted, decrypted, keys, stream):
        self.logger.info("\nDecrypting: {}".format(encrypted))
        self.logger.info("\n".join(["{}:{}".format(x["KID"], x["KEY"]) for x in keys]))
        wvdecrypt_process = subprocess.Popen(
            [
                self.config.BIN.shaka_packager,
                "--enable_raw_key_decryption",
                "-quiet",
                "input={},stream={},output={}".format(encrypted, stream, decrypted),
            ]
            + self.getKeysShaka2(keys)
        )

        stdoutdata, stderrdata = wvdecrypt_process.communicate()
        wvdecrypt_process.wait()
        self.logger.info("Done!")

        return

    def runpandsdecryptor(self, command):
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        Decrypted_successfully = False
        Decrypted_took = None

        for line in getattr(proc, "stdout"):
            line = line.strip()
            if "Starting Decryption" in line:
                print(line)
            elif "=" in line:
                print(line, flush=True, end="\r")
            elif "Decrypted successfully" in line:
                Decrypted_successfully = True
            elif "Decryption took" in line:
                Decrypted_took = line
        print()
        if Decrypted_successfully:
            print("Decrypted successfully")
        if Decrypted_took:
            print(Decrypted_took)

        return

    def get_matched_key(self, encrypted, keys):
        header_data = probe(encrypted, self.config.BIN.mp4dump)
        output = {"kid": header_data.kid, "pssh": header_data.raw_pssh}
        if (proper_keys := [k for k in keys if output["kid"] == k["KID"]]) != []:
            return proper_keys

        return keys

    def mp4decryptor(self, encrypted, decrypted, keys, pandsdecryptor=True, kid=True):
        self.logger.info("\nDecrypting: {}".format(encrypted))
        self.logger.info("\n".join(["{}:{}".format(x["KID"], x["KEY"]) for x in keys]))
        print()
        matched_keys = self.get_matched_key(encrypted, keys)
        if matched_keys:
            self.logger.info("Using Matched Keys according to encrypted file KID")
            self.logger.info("\n".join(["{}:{}".format(x["KID"], x["KEY"]) for x in matched_keys]))
            keys = matched_keys

        decrypt_command = (
            [
                self.config.BIN.pandsdecryptor
                if pandsdecryptor
                else self.config.BIN.mp4decrypt
            ]
            + self.getKeysMp4(keys, kid=kid)
            + ["--show-progress", encrypted, decrypted]
        )

        if os.environ["THREAD_MODE"] == "YES":
            subprocess.call(decrypt_command, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            return self.is_encrypted(decrypted)

        if pandsdecryptor:
            self.runpandsdecryptor(decrypt_command)
            self.logger.info("Done!")
            return self.is_encrypted(decrypted)

        wvdecrypt_process = subprocess.Popen(decrypt_command)
        stdoutdata, stderrdata = wvdecrypt_process.communicate()
        wvdecrypt_process.wait()
        self.logger.info("Done!")

        return self.is_encrypted(decrypted)

    def ffmpegclean(self, decrypted, cleaned):
        self.logger.info("\nCleaning: {}".format(decrypted))
        ffmpeg = clean_mp4(self.config.BIN.ffmpeg, decrypted, cleaned)
        ffmpeg.start_cleaning()
        self.logger.info("Done!")

    def mp4boxegclean(self, decrypted, cleaned):
        self.logger.info("\nCleaning: {}".format(decrypted))
        subprocess.call(
            [self.config.BIN.mp4box, "-quiet", "-raw", "1", "-out", cleaned, decrypted,]
        )
        self.logger.info("Done!")

    def ffmpegcleanAudio(self, Input):
        ffmpeg = clean_audio(self.config.BIN.ffmpeg, Input)
        mediainfo = ffmpeg.mediainfo_(self.config.BIN.MediaInfo)
        Output = ffmpeg.set_Output(mediainfo)
        if isfile(Output):
            return
        self.logger.info("\nCleaning: {}".format(Input))
        ffmpeg.start_cleaning(Output)

        self.logger.info("Done!")

        return


class SubtitleHelper:
    def __init__(self,):
        """SubtitleHelper -> Hold the functions for convert XML/DFXP/WEBVTT subtitles."""
        self.logger = logging.getLogger(__name__)
        self.wvripper_config = wvripper_config()
        self.config = self.wvripper_config.config()
        self.session = requests.Session()
        self.adapter = requests.adapters.HTTPAdapter(
            pool_connections=150, pool_maxsize=150, max_retries=5
        )
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)

    def CCExtractor(self, Input: str, Output: str):

        out_path = Path(Output)

        try:
            subprocess.run([
                self.config.BIN.CCExtractor,
                "-trim", "-noru", "-ru1",
                Input, "-o", str(out_path)
            ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as e:
            if e.returncode == 10:  # No captions found
                if out_path.exists():
                    out_path.unlink(missing_ok=True)
                return None
            raise

        if out_path.exists():
            if out_path.stat().st_size <= 3:
                out_path.unlink(missing_ok=True)
                return None

        return

    def ReadSubtitle(self, File, encoding="utf-8"):
        with codecs.open(File, "r+", encoding=encoding) as opened:
            content = opened.read()

        return content

    def SaveSubtitle(self, File, content, encoding="utf-8"):
        with codecs.open(File, "w+", encoding=encoding) as writer:
            writer.write(content)

        return

    def SubtitleDownloader(
        self, Url, Output, Session=None, proxies={}, cookies={}, headers={}
    ):
        if isfile(Output):
            return

        self.logger.info(f"Downloading: {Output}")
        r = self.session.get(Url, proxies=proxies, cookies=cookies, headers=headers)
        with open(Output, "wb") as opened:
            opened.write(r.content)

        return

    def NetflixConverter(self, Input: str, Output: str, Type="WEBVTT"):
        if isfile(Output):
            return
        WebVTTReader = WebVTT2Srt()
        content = self.ReadSubtitle(Input)
        content = WebVTTReader.SimpleConverter(content)
        self.SaveSubtitle(Output, content)
        return

    def SubtitleConverter(self, Input: str, Output: str, Type="WEBVTT"):
        if isfile(Output):
            return

        if Type == "WEBVTT":
            self.SaveSubtitle(Output, self.WevVttConverter(self.ReadSubtitle(Input)))
        elif Type == "DFXP":
            self.SaveSubtitle(Output, self.DfxpConverter(self.ReadSubtitle(Input)))
        elif Type == "XML":
            self.SaveSubtitle(Output, self.XmlConverter(self.ReadSubtitle(Input)))
        elif Type == "TTML":
            self.SaveSubtitle(Output, self.TtmlConverter(self.ReadSubtitle(Input)))
        else:
            raise ValueError(f"Unknown Type: {Type}")

        return

    def NoSDH(self, Input: str, Output: str, encoding="utf-8"):
        nsdh = SDHConverter()
        nsdh.Convert(Input=Input, Output=Output, encoding=encoding)
        return

    def ReverseRtl(self, Input: str, Output: str, encoding="utf-8"):
        rtl = ReverseRtlStartEnd()
        rtl.Reverse(Input=Input, Output=Output, encoding=encoding)
        return

    def TimeCodesFix(self, Input: str, Output: str, encoding="utf-8"):
        tc = FixSubtitleTimeCodes()
        tc.Merge(Input=Input, Output=Output, encoding=encoding)
        return

    def WevVttConverter(self, content):
        try:
            WebVTTReader = pycaption.WebVTTReader().read(content)
            content = pycaption.SRTWriter().write(WebVTTReader)
        except Exception:
            WebVTTReader = WebVTT2Srt()
            content = WebVTTReader.SimpleConverter(content)

        return content

    def DfxpConverter(self, content):
        try:
            DFXPReader = pycaption.DFXPReader().read(content)
            content = pycaption.SRTWriter().write(DFXPReader)
        except Exception:
            DFXPReader = DFXPConverter()
            content = DFXPReader.Convert(content)

        return content

    def XmlConverter(self, content):
        try:
            SAMIReader = pycaption.SAMIReader().read(content)
            content = pycaption.SRTWriter().write(SAMIReader)
        except Exception:
            SAMIReader = DFXPConverter()
            content = SAMIReader.Convert(content)

        return content

    def TtmlConverter(self, content):
        try:
            DFXPReader = pycaption.DFXPReader().read(content)
            content = pycaption.SRTWriter().write(DFXPReader)
        except Exception:
            DFXPReader = DFXPConverter()
            content = DFXPReader.Convert(content)

        return content
