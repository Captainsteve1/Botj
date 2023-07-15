import glob
import os
import random
import re
import shutil
from os.path import dirname

from utils.modules import boxcli


def get_current_dir(file):
    return dirname(dirname(file)).replace("\\", "/")

def msgBox(NAME, INFO, width=10, height=5):
    factory = boxcli.BoxFactory(width, height, boxcli.BoxStyles.CLASSIC)
    box = factory.get_box(NAME, INFO)
    return box

class tuple_(object):
    def __init__(self):
        return

class Services:
    def __init__(self):
        """class to detect url Mode"""
        self._primevideo = re.compile(r"http.+primevideo")
        self._amazon = re.compile(r"http.+amazon")
        self._netflix = re.compile(r"http.+netflix")
        self._apple = re.compile(r"http.+apple")
        self._shahid = re.compile(r"http.+shahid")
        self._disneyplus = re.compile(r"http.+disneyplus")
        self._dcuniverse = re.compile(r"http.+dcuniverse")
        self._hulu = re.compile(r"http.+hulu")
        self._stan = re.compile(r"http.+stan")
        self._peacocktv = re.compile(r"http.+peacocktv")
        self._rakuten = re.compile(r"http.+rakuten")
        self._google = re.compile(r"http.+google")
        self._fandangonow = re.compile(r"http.+fandangonow")
        self._hbomax = re.compile(r"http.+hbomax")
        self._osn = re.compile(r"http.+osn")

    def detect(self, content):
        if self._primevideo.search(content):
            return "AMAZON"
        elif self._amazon.search(content):
            return "AMAZON"
        elif self._apple.search(content):
            return "APPLETV"
        elif self._netflix.search(content):
            return "NETFLIX"
        elif self._shahid.search(content):
            return "SHAHID"
        elif self._disneyplus.search(content):
            return "DISNEYPLUS"
        elif self._dcuniverse.search(content):
            return "DCUNIVERSE"
        elif self._hulu.search(content):
            return "HULU"
        elif self._stan.search(content):
            return "STAN"
        elif self._peacocktv.search(content):
            return "PEACOCKTV"
        elif self._rakuten.search(content):
            return "RAKUTEN"
        elif self._google.search(content):
            return "GOOGLE"
        elif self._fandangonow.search(content):
            return "FANDANGONOW"
        elif self._hbomax.search(content):
            return "HBOMAX"
        elif self._osn.search(content):
            return "OSN"

        return None

class utils:
    """hold some func to help me in dev"""

    def __init__(self):
        self.UT = None

    def random_hex(self, length: int) -> str:
        """return {length} of random string"""
        return "".join(random.choice("0123456789ABCDEF") for _ in range(length))

    def create_dirs_files(self, DIRS: list, FILES: list):
        for dirs in DIRS:
            if not os.path.exists(dirs):
                os.makedirs(dirs)

        for files in FILES:
            if not os.path.isfile(files):
                with open(files, "w") as f:
                    f.write("\n")


class download_dir:
    def __init__(self, arg_output, path_folder="DOWNLOADS", stream_folder="DOWNLOADS"):
        self.path_folder = path_folder
        self.arg_output = arg_output
        self.stream_folder = stream_folder
        self.Dir = None
        self.OriginalDir = os.getcwd()
        self.set_output()

    def make_dirs(self, Dir):
        if not os.path.exists(Dir):
            try:
                os.makedirs(Dir)
            except OSError as e:
                raise OSError("Error Creating Dir: {}".format(e))

        return Dir

    def check_config_dir(self):
        if self.path_folder is not None:
            Dir = os.path.join(self.path_folder, self.stream_folder)
            Dir = self.make_dirs(Dir)
        else:
            Dir = os.path.join(os.getcwd(), self.stream_folder)
            Dir = self.make_dirs(Dir)

        return Dir

    def set_output(self):
        self.Dir = self.make_dirs(os.path.join(os.getcwd(), self.arg_output)) if self.arg_output else self.check_config_dir()
        self.DirTemp = self.make_dirs(os.path.join(self.Dir, "[TEMP]"))
        self.DirOutput = self.make_dirs(os.path.join(self.Dir, "[OUTPUT]"))

    def GoTo_MainDir(self):
        os.chdir(self.OriginalDir)

    def GoTo_MainFolder(self):
        # os.chdir(self.Dir)
        os.chdir(self.DirTemp)

    def GoTo_TitleFolder(self, folder):
        folder = self.make_dirs(os.path.join(self.Dir, folder))
        os.chdir(folder)


class WhenDownloadFinish:
    def __init__(self,):
        """"""

    def TitleFolder(self, outputfile):
        return os.path.dirname(outputfile)

    def do_stuff(self, file, outputfolder):
        ara_subtitle_regex = r"ara-subtitle\.srt|ar-subtitle\.srt|ara-sdh\.srt|ar-sdh\.srt|ara-forced\.srt|ar-forced\.srt|ara-cc\.srt|ar-cc\.srt"

        if re.search(ara_subtitle_regex, file):
            shutil.copy(file, outputfolder)
            
        return 
        
    def onLoad(self, title, outputfile):
        for file in glob.glob(f"{title}*.*"):
            if not file.endswith(".mkv"):
                self.do_stuff(file, self.TitleFolder(outputfile))

        return  
