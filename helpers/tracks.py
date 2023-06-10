import logging
import re
from collections import namedtuple
from helpers.tracks_colored import tracks_colored
import inquirer


class selected_track(object):
    def __init__(self):
        return


class show_tracks:
    def __init__(self, tracks, selected, title=(), selected_only=False):
        """---"""
        self.logger = logging.getLogger(__name__)
        self.tracks = tracks
        self.selected = selected
        self.selected_only = selected_only
        self.title = title
        self.show()

    def getLine(self, infos):
        return "".join(["_" for x in range(1, len(max(infos, key=len)) + 1)])

    def show(self):
        if not self.selected_only:
            self.logger.info("\nAvailables Tracks")
            for t in self.tracks.Videos:
                self.logger.info(t.Info)
            print()
            for t in self.tracks.Audios:
                if t.Type == "DIALOG":
                    self.logger.info(t.Info)
            for t in self.tracks.Audios:
                if t.Type == "DESCRIPTIVE":
                    self.logger.info(t.Info)
            print()
            for t in self.tracks.TimedText:
                if t.Type == "SUBTITLE":
                    self.logger.info(t.Info)
            for t in self.tracks.TimedText:
                if t.Type == "CC":
                    self.logger.info(t.Info)
            for t in self.tracks.TimedText:
                if t.Type == "SDH":
                    self.logger.info(t.Info)
            for t in self.tracks.TimedText:
                if t.Type == "FORCED":
                    self.logger.info(t.Info)

        self.logger.info("\nSelected Tracks")

        if not self.selected.Videos == []:
            print()
            tracks_colored.stdout_video(self.selected.Videos)

        if not self.selected.Audios == []:
            print()
            tracks_colored.stdout_audio(self.selected.Audios)

        if not self.selected.TimedText == []:
            print()
            tracks_colored.stdout_subtitle(self.selected.TimedText)

        if len(self.title) == 1:
            print()
            tracks_colored.stdout_title_info(Title=self.title[0], Id=None)

        if len(self.title) == 2:
            print()
            tracks_colored.stdout_title_info(Title=self.title[0], Id=self.title[1])

        # if not self.selected.Videos == []:
        #     print()
        #     for t in self.selected.Videos:
        #         self.logger.info(t.Info)

        # if not self.selected.Audios == []:
        #     print()
        #     for t in self.selected.Audios:
        #         if t.Type == "DIALOG":
        #             self.logger.info(t.Info)
        #     for t in self.selected.Audios:
        #         if t.Type == "DESCRIPTIVE":
        #             self.logger.info(t.Info)

        # if not self.selected.TimedText == []:
        #     print()
        #     for t in self.selected.TimedText:
        #         if t.Type == "SUBTITLE":
        #             self.logger.info(t.Info)
        #     for t in self.selected.TimedText:
        #         if t.Type == "CC":
        #             self.logger.info(t.Info)
        #     for t in self.selected.TimedText:
        #         if t.Type == "SDH":
        #             self.logger.info(t.Info)
        #     for t in self.selected.TimedText:
        #         if t.Type == "FORCED":
        #             self.logger.info(t.Info)

        return


class smart_select:
    def __init__(self, tracks, resolution=None):
        """CLASS FOR SMART SELECT VIDEO, AUDIO, SUBTITLES, BASED ON WVTRACKS.PY"""
        self.logger = logging.getLogger(__name__)
        self.resolution = resolution
        self.tracks = tracks
        self.selected = namedtuple(
            "_", "selected Videos Audios TimedText"
        )  # selected_track()
        self.selected.Videos = []
        self.selected.Audios = []
        self.selected.TimedText = []

    def select_video(self,):
        if self.resolution and self.tracks.Videos != []:
            while self.tracks.Videos[-1].Height > self.resolution:
                self.tracks.Videos.pop(-1)

            self.selected.Videos.append(self.tracks.Videos[-1])
            return

        if self.tracks.Videos != []:
            self.selected.Videos.append(self.tracks.Videos[-1])

        return

    def select_audio(self):
        # -> select Original Audio
        for track in self.tracks.Audios:
            if track.Type == "DIALOG" and track.Original:
                OriginalLanguage = track.Language
                self.selected.Audios.append(track)

                for track in self.tracks.TimedText:
                    if track.Type == "FORCED":
                        if track.Language.lower() == OriginalLanguage.lower():
                            self.selected.TimedText.append(track)

        # -> if only 1 audio then select it.
        if self.selected.Audios == [] and len(self.tracks.Audios) == 1:
            for track in self.tracks.Audios:
                if track.Type == "DIALOG":
                    OriginalLanguage = track.Language
                    self.selected.Audios.append(track)

                    for track in self.tracks.TimedText:
                        if track.Type == "FORCED":
                            if track.Language.lower() == OriginalLanguage.lower():
                                self.selected.TimedText.append(track)

        # -> select eng audio as original audio.
        if self.selected.Audios == []:
            for track in self.tracks.Audios:
                if (
                    track.Type == "DIALOG"
                    and track.Language in ["eng", "en"]
                ):
                    OriginalLanguage = track.Language
                    self.selected.Audios.append(track)

                    for track in self.tracks.TimedText:
                        if track.Type == "FORCED":
                            if track.Language.lower() == OriginalLanguage.lower():
                                self.selected.TimedText.append(track)
        return None

    def select_subtitle(self):
        for track in self.tracks.TimedText:
            if track.Type == "SUBTITLE" or track.Type == "SDH" or track.Type == "CC":
                self.selected.TimedText.append(track)

    def select(self):
        self.select_video()
        self.select_audio()
        self.select_subtitle()
        return self.selected


class select_by_arguments:
    def __init__(self, tracks, args):
        """CLASS FOR SELECT VIDEO, AUDIO, SUBTITLES, BASED ON WVTRACKS.PY"""
        self.logger = logging.getLogger(__name__)
        self.tracks = tracks
        self.args = args
        self.selected = namedtuple(
            "_", "selected Videos Audios TimedText"
        )  # selected_track()
        self.selected.Videos = []
        self.selected.Audios = []
        self.selected.TimedText = []

    def select_video(self,):
        if self.tracks.Videos != []:
            while self.tracks.Videos[-1].Height > self.args.resolution:
                self.tracks.Videos.pop(-1)

            self.selected.Videos.append(self.tracks.Videos[-1])

        return None

    def select_audio(self):
        AudioLanguages = list(map(lambda x: x.lower().strip(), self.args.AudioLanguage.split(",")))
        AudioDescriptionLanguage = list(map(lambda x: x.lower().strip(), self.args.AudioDescriptionLanguage.split(",")))

        for track in self.tracks.Audios:
            if track.Type == "DESCRIPTIVE":
                if track.Language.lower() in AudioDescriptionLanguage:
                    self.selected.Audios.append(track)
            if track.Type == "DIALOG":
                if track.Language.lower() in AudioLanguages:
                    self.selected.Audios.append(track)

        for audio in AudioLanguages:
            if audio.upper() == "ORIGINAL":
                for track in self.tracks.Audios:
                    if track.Type == "DIALOG" and track.Original:
                        self.selected.Audios.append(track)
                        break

        for audio in AudioDescriptionLanguage:
            if audio.upper() == "ORIGINAL":
                for track in self.tracks.Audios:
                    if track.Type == "DESCRIPTIVE" and track.Original:
                        self.selected.Audios.append(track)
                        break

        for audio in AudioLanguages:
            if audio.upper() == "ALL":
                for track in self.tracks.Audios:
                    if track.Type == "DIALOG":
                        self.selected.Audios.append(track)

        for audio in AudioDescriptionLanguage:
            if audio.upper() == "ALL":
                for track in self.tracks.Audios:
                    if track.Type == "DESCRIPTIVE":
                        self.selected.Audios.append(track)

        return

    def select_subtitle(self):
        SubtitleLanguages = list(map(lambda x: x.lower().strip(), self.args.SubtitleLanguage.split(",")))
        ForcedSubtitleLanguage = list(map(lambda x: x.lower().strip(), self.args.ForcedSubtitleLanguage.split(",")))

        for track in self.tracks.TimedText:
            if track.Type == "SUBTITLE" or track.Type == "SDH" or track.Type == "CC":
                if track.Language.lower() in SubtitleLanguages:
                    self.selected.TimedText.append(track)
            elif track.Type == "FORCED":
                if track.Language.lower() in ForcedSubtitleLanguage:
                    self.selected.TimedText.append(track)

        for subtitle in SubtitleLanguages:
            if subtitle.upper() == "ALL":
                for track in self.tracks.TimedText:
                    if (
                        track.Type == "SUBTITLE"
                        or track.Type == "SDH"
                        or track.Type == "CC"
                    ):
                        self.selected.TimedText.append(track)

        for subtitle in ForcedSubtitleLanguage:
            if subtitle.upper() == "ALL":
                for track in self.tracks.TimedText:
                    if track.Type == "FORCED":
                        self.selected.TimedText.append(track)

        if not self.selected.Audios == []:
            selectedAudioLanguages = [x.Language for x in self.selected.Audios]
            for subtitle in ForcedSubtitleLanguage:
                if subtitle.upper() == "based":
                    for track in self.tracks.TimedText:
                        if track.Type == "FORCED" and track.Language.lower() in selectedAudioLanguages:
                            self.selected.TimedText.append(track)
                            
        return

    def select(self):
        self.select_video()
        self.select_audio()
        self.select_subtitle()
        return self.selected


class select_by_asking:
    def __init__(self, tracks):
        """CLASS FOR SELECT VIDEO, AUDIO, SUBTITLES, BASED ON WVTRACKS.PY"""
        self.logger = logging.getLogger(__name__)
        self.tracks = tracks
       
    def numbers_proccessor(self, number):
        N = []

        if number.isdigit():
            return [int(number)]

        try:
            start, end = number.split("-")
        except Exception:
            return N

        for n in range(int(start), int(int(end) + 1)):
            N.append(n)

        return N

    def get_valid_numbers(self, numbers, tracks_length):
        valid = []
        numbers = [x.strip() for x in numbers.split("+")]
        for n in numbers:
            valid += self.numbers_proccessor(n)

        valid = [x for x in valid if x >= 0 and x <= tracks_length]
        return valid

    def check_inputs(self, number, tracks_length):
        try:
            number = int(number)
        except Exception:
            self.logger.info("Input is not an integer: {}".format(number))
            return False

        if number < 1:
            self.logger.info("Input is lower than 1: {}".format(number))
            return False

        if number > tracks_length:
            self.logger.info("Input is bigger than Tracks length, FFS: {}".format(number))
            return False

        return number


    def select_video_by_rack_number_style(self):
        self.logger.info("\nVideo Selector")
        print()

        for idx, track in enumerate(self.tracks.Videos, start=1):
            number = str(idx).zfill(2)
            print("{} - {}".format(number, track.Info))

        right_input = False

        while not right_input:
            number = input("\nENTER VIDEO TRACK NUMBER: ").strip()
            right_input = self.check_inputs(number, int(len(self.tracks.Videos)))
            if right_input:
                self.selected.Videos.append(self.tracks.Videos[right_input - 1])

        return 

    def select_audio_by_rack_number_style(self):
        self.logger.info("\nAudios Selector")
        self.logger.info("\nWARNING -> You can pick multiplate tracks by split track numbers. use + or -")
        print()

        for idx, track in enumerate(self.tracks.Audios, start=1):
            number = str(idx).zfill(2)
            print("{} - {}".format(number, track.Info))

        numbers = input("\nENTER AUDIO TRACK NUMBERS: ").strip()
        numbers = self.get_valid_numbers(numbers, int(len(self.tracks.Audios)))
        for n in numbers:
            if n > 0:
                self.selected.Audios.append(self.tracks.Audios[n - 1])

        return 

    def select_subtitle_by_rack_number_style(self):
        self.logger.info("\nSubtitle Selector")
        self.logger.info("\nWARNING -> You can pick multiplate tracks by split track numbers. use + or -")
        print()

        for idx, track in enumerate(self.tracks.TimedText, start=1):
            number = str(idx).zfill(2)
            print("{} - {}".format(number, track.Info))

        numbers = input("\nENTER SUBTITLE TRACK NUMBERS: ").strip()
        numbers = self.get_valid_numbers(numbers, int(len(self.tracks.TimedText)))
        for n in numbers:
            if n > 0:
                self.selected.TimedText.append(self.tracks.TimedText[n - 1])

        return

    def select_video_by_drop_menu_style(self):
        video_tracks = self.tracks.Videos
        video_tracks = sorted(video_tracks, key=lambda k: (k.Profile, int(k.Height), int(k.Bitrate)))

        VideoSelector = [
            inquirer.Checkbox('selected',
                message="Select Video Track?",
                choices=["[{}] {}".format(str(idx).zfill(2), track.Info) for idx, track in enumerate(video_tracks, start=1)],
            ),
        ]

        answers = inquirer.prompt(VideoSelector)
        if not answers["selected"] == []:
            for idx, track in enumerate(video_tracks, start=1):
                trackId = "[{}] {}".format(str(idx).zfill(2), track.Info)
                if trackId in answers["selected"]:
                    self.selected.Videos.append(track)
                    return

        return

    def select_audio_by_drop_menu_style(self):
        audio_tracks = self.tracks.Audios
        audio_tracks = sorted(audio_tracks, key=lambda k: (k.Profile, int(k.Bitrate)))

        AudioSelector = [
            inquirer.Checkbox('selected',
                message="Select Audio Track?",
                choices=["[{}] {}".format(str(idx).zfill(2), track.Info) for idx, track in enumerate(audio_tracks, start=1)],
            ),
        ]

        answers = inquirer.prompt(AudioSelector)

        if not answers["selected"] == []:
            for idx, track in enumerate(audio_tracks, start=1):
                trackId = "[{}] {}".format(str(idx).zfill(2), track.Info)
                if trackId in answers["selected"]:
                    self.selected.Audios.append(track)

        return

    def select_subtitle_by_drop_menu_style(self):
        SubtitleSelector = [
            inquirer.Checkbox('selected',
                message="Select Subtitle Track?",
                choices=["[{}] {}".format(str(idx).zfill(2), track.Info) for idx, track in enumerate(self.tracks.TimedText, start=1)],
            ),
        ]

        answers = inquirer.prompt(SubtitleSelector)

        if not answers["selected"] == []:
            for idx, track in enumerate(self.tracks.TimedText, start=1):
                trackId = "[{}] {}".format(str(idx).zfill(2), track.Info)
                if trackId in answers["selected"]:
                    self.selected.TimedText.append(track)

        return

    def generate_select_task(self, previous_selection, select_by):
        if previous_selection is False:
            selected = namedtuple("_", "selected Videos Audios TimedText")
            selected.Videos = []
            selected.Audios = []
            selected.TimedText = []
            return selected

        selected = previous_selection

        if select_by == "SELECT_ALL":
            selected.Videos = []
            selected.Audios = []
            selected.TimedText = []
            return selected
        elif select_by == "SELECT_VIDEO":
            selected.Videos = []
            return selected
        elif select_by == "SELECT_AUDIO":
            selected.Audios = []
            return selected
        elif select_by == "SELECT_SUBTITLE":
            selected.TimedText = []
            return selected

        return 

    def select(self, menu_style=False, previous_selection=False, select_by="SELECT_ALL"):
        self.selected = self.generate_select_task(previous_selection, select_by)
        print()

        if menu_style:
            if select_by == "SELECT_ALL":
                self.select_video_by_drop_menu_style()
                self.select_audio_by_drop_menu_style()
                self.select_subtitle_by_drop_menu_style()
                return self.selected 
            elif select_by == "SELECT_VIDEO":
                self.select_video_by_drop_menu_style()
                return self.selected 
            elif select_by == "SELECT_AUDIO":
                self.select_audio_by_drop_menu_style()
                return self.selected 
            elif select_by == "SELECT_SUBTITLE":
                self.select_subtitle_by_drop_menu_style()
                return self.selected 
        else:
            if select_by == "SELECT_ALL":
                self.select_video_by_rack_number_style()
                self.select_audio_by_rack_number_style()
                self.select_subtitle_by_rack_number_style()
                return self.selected 
            elif select_by == "SELECT_VIDEO":
                self.select_video_by_rack_number_style()
                return self.selected 
            elif select_by == "SELECT_AUDIO":
                self.select_audio_by_rack_number_style()
                return self.selected 
            elif select_by == "SELECT_SUBTITLE":
                self.select_subtitle_by_rack_number_style()
                return self.selected

        return
