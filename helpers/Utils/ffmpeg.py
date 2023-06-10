import json
import os
import re
import subprocess
import sys

import ffmpy


class clean_audio:
    def __init__(self, ffmpeg: str, Input: str) -> str:
        self.ffmpeg = ffmpeg
        self.Input = Input

    def mediainfo_(self, MediaInfo):
        mediainfo_output = subprocess.Popen(
            [MediaInfo, "--Output=JSON", "-f", self.Input], stdout=subprocess.PIPE,
        )
        mediainfo_json = json.load(mediainfo_output.stdout)
        return mediainfo_json

    def set_Output(self, mediainfo):
        ext = ".ac3"

        for m in mediainfo["media"]["track"]:
            if m["@type"] == "Audio":
                if m["Format"] == "AAC":
                    ext = ".m4a"
                elif m["Format"] == "E-AC-3":
                    ext = ".eac3"
                elif m["Format"] == "AC-3":
                    ext = ".ac3"
                elif m["Format"] == "DTS":
                    ext = ".dts"

        Output = self.Input
        Output = re.sub(r"-encrypted\.mp4", ext, Output)
        Output = re.sub(r"-decrypted\.mp4", ext, Output)
        Output = re.sub(r"-cleaned\.mp4", ext, Output)
        return Output

    def start_cleaning(self, Output):

        ff = ffmpy.FFmpeg(
            executable=self.ffmpeg,
            inputs={self.Input: None},
            outputs={Output: "-c:a copy"},
            global_options="-vn -sn -y -hide_banner -loglevel panic",
        )
        ff.run()

        return


class clean_mp4:
    def __init__(self, ffmpeg: str, Input: str, Output: str) -> str:
        self.ffmpeg = ffmpeg
        self.Input = Input
        self.Output = Output

    def convert_time(self, time_str):
        time_str = time_str[: time_str.index(".")] if "." in time_str else time_str
        return sum(
            x * int(t) for x, t in zip([1, 60, 3600], reversed(time_str.split(":")))
        )

    def current_time(self, stdout: str):
        data = re.search(r"time=(.+)bitrate=(.+)", stdout)
        if data:
            return self.convert_time(re.sub(",", "", data.group(1).strip()))

        return None

    def full_time(self, stdout: str):
        data = re.search(r"Duration:(.+)start:(.+)", stdout)
        if data:
            return self.convert_time(re.sub(",", "", data.group(1).strip()))
        return None

    def commands(self):
        return [self.ffmpeg, "-y", "-i", self.Input, "-c", "copy", self.Output]

    def updt(self, total, progress):
        barLength, status = 80, ""
        progress = float(progress) / float(total)
        if progress >= 1.0:
            progress, status = 1, "\r\n"
        block = int(round(barLength * progress))
        # text = "\r-> {} | {:.0f}% {}".format(
        #     "█" * block + "" * (barLength - block), round(progress * 100, 0), status,
        # )

        text = "\r{:.0f}% {}".format(round(progress * 100, 0), status,)
        sys.stdout.write(text)
        sys.stdout.flush()

    def start_cleaning(self):
        if os.environ["THREAD_MODE"] == "YES":
            subprocess.call(self.commands(), stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            return

        proc = subprocess.Popen(
            self.commands(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        self.video_lenght = None
        for line in getattr(proc, "stdout"):
            if not self.video_lenght:
                self.video_lenght = self.full_time(line)
                continue

            current = self.current_time(line)
            if current:
                self.updt(int(self.video_lenght), int(current))


# ffmpeg.exe -err_detect ignore_err -hide_banner -y -i "2.mp4" -vcodec copy "_2.mp4"