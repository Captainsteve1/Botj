from prettytable import PrettyTable
from colorama import init
from termcolor import colored
init()

class colorPicker:
    YELLOW = "yellow"
    RED = "red"
    BLUE = "blue"
    WHITE = "white"
    GREEN = "green"
    MAGENTA = "magenta"
    CYAN = "cyan"

class colorText:
    def Text(text, color_name):
        return colored(str(text), color_name)

class tracks_colored:
    def stdout_subtitle(Subtitles):
        SUBTITLE_FIELD = ["Track"]

        for track in Subtitles:
            if track.Type:
                SUBTITLE_FIELD.append("Type")
            if track.Profile:
                SUBTITLE_FIELD.append("Profile")
            if track.Name and track.Language:
                SUBTITLE_FIELD.append("Language")

        SUBTITLE_FIELD = list(dict.fromkeys(SUBTITLE_FIELD))
        SubtitleTable = PrettyTable(SUBTITLE_FIELD)

        for track in Subtitles:
            SUBTITLE_ROW = [colorText.Text("SUBTITLE", colorPicker.YELLOW)]

            if track.Type:
                SUBTITLE_ROW += [colorText.Text(track.Type, colorPicker.GREEN)]
            if track.Profile:
                SUBTITLE_ROW += [colorText.Text(track.Profile, colorPicker.MAGENTA)]
            if track.Name and track.Language:
                SUBTITLE_ROW += [colorText.Text("{} - [{}]".format(track.Name, track.Language), colorPicker.CYAN)]

            if len(SUBTITLE_FIELD) == len(SUBTITLE_ROW):
                SubtitleTable.add_row(SUBTITLE_ROW)

        print(SubtitleTable)
        return

    def stdout_audio(Audios):
        AUDIO_FIELD = ["Track"]

        for track in Audios:
            if track.Type:
                AUDIO_FIELD.append("Type")
            if track.Drm:
                AUDIO_FIELD.append("Drm")
            if track.Channels:
                AUDIO_FIELD.append("Channels")
            if track.Codec:
                AUDIO_FIELD.append("Codec")
            if track.Profile:
                AUDIO_FIELD.append("Profile")
            if track.Bitrate:
                AUDIO_FIELD.append("Bitrate")
            if track.Size:
                AUDIO_FIELD.append("Size")
            if track.Name and track.Language:
                AUDIO_FIELD.append("Language")

        AUDIO_FIELD.append("Original")
        AUDIO_FIELD = list(dict.fromkeys(AUDIO_FIELD))
        AudioTable = PrettyTable(AUDIO_FIELD)

        for track in Audios:
            AUDIO_ROW = [colorText.Text("AUDIO", colorPicker.YELLOW)]

            if track.Type:
                AUDIO_ROW += [colorText.Text(track.Type, colorPicker.GREEN)]
            if track.Drm:
                AUDIO_ROW += [colorText.Text(track.Drm, colorPicker.RED)]
            if track.Channels:
                AUDIO_ROW += [colorText.Text(track.Channels, colorPicker.BLUE)]
            if track.Codec:
                AUDIO_ROW += [colorText.Text(track.Codec, colorPicker.CYAN)]
            if track.Profile:
                AUDIO_ROW += [colorText.Text(track.Profile, colorPicker.MAGENTA)]
            if track.Bitrate:
                AUDIO_ROW += [colorText.Text(track.Bitrate, colorPicker.YELLOW)]
            if track.Size:
                AUDIO_ROW += [colorText.Text(f"{track.Size/1048576:0.2f} MiB" if track.Size < 1073741824 else f"{track.Size/1073741824:0.2f} GiB", colorPicker.GREEN)]
            if track.Name and track.Language:
                AUDIO_ROW += [colorText.Text("{} [{}]".format(track.Name, track.Language), colorPicker.CYAN)]

            AUDIO_ROW += [colorText.Text(track.Original, colorPicker.RED)]

            if len(AUDIO_FIELD) == len(AUDIO_ROW):
                AudioTable.add_row(AUDIO_ROW)

        print(AudioTable)
        return

    def stdout_video(Videos):
        ADDED = set()
        VIDEO_FIELD = ["Track"]

        for track in Videos:
            if track.Type:
                VIDEO_FIELD.append("Type")
            if track.Drm:
                VIDEO_FIELD.append("Drm")
            if track.FrameRate:
                VIDEO_FIELD.append("FrameRate")
            if track.Codec:
                VIDEO_FIELD.append("Codec")
            if track.Profile:
                VIDEO_FIELD.append("Profile")
            if track.Bitrate:
                VIDEO_FIELD.append("Bitrate")
            if track.Size:
                VIDEO_FIELD.append("Size")
            if track.Height and track.Width:
                VIDEO_FIELD.append("Resolution")

        VIDEO_FIELD = list(dict.fromkeys(VIDEO_FIELD))
        VideoTable = PrettyTable(VIDEO_FIELD)

        for track in Videos:
            VIDEO_ROW = [colorText.Text("VIDEO", colorPicker.YELLOW)]

            if track.Type:
                VIDEO_ROW += [colorText.Text(track.Type, colorPicker.GREEN)]
            if track.Drm:
                VIDEO_ROW += [colorText.Text(track.Drm, colorPicker.RED)]
            if track.FrameRate:
                VIDEO_ROW += [colorText.Text(track.FrameRate, colorPicker.BLUE)]
            if track.Codec:
                VIDEO_ROW += [colorText.Text(track.Codec, colorPicker.CYAN)]
            if track.Profile:
                VIDEO_ROW += [colorText.Text(track.Profile, colorPicker.MAGENTA)]
            if track.Bitrate:
                VIDEO_ROW += [colorText.Text(track.Bitrate, colorPicker.YELLOW)]
            if track.Size:
                VIDEO_ROW += [colorText.Text(f"{track.Size/1048576:0.2f} MiB" if track.Size < 1073741824 else f"{track.Size/1073741824:0.2f} GiB", colorPicker.GREEN)]
            if track.Height and track.Width:
                VIDEO_ROW += [colorText.Text("{}x{}".format(track.Width, track.Height), colorPicker.CYAN)]

            if len(VIDEO_FIELD) == len(VIDEO_ROW):
                VideoTable.add_row(VIDEO_ROW)

        print(VideoTable)
        return

    def stdout_title_info(Title, Id):
        InfoTable = PrettyTable(["Title", "Id"])
        InfoTable.add_row([colorText.Text(Title, colorPicker.GREEN), colorText.Text(Id, colorPicker.RED)])
        print(InfoTable)
        return

