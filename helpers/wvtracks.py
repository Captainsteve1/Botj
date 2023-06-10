import re
from collections import namedtuple

import requests


class track(object):
    def __init__(self):
        return


class wvtracks:
    def __init__(self):
        """CLASS FOR ORDER AND SERIALIZE VIDEO, AUDIO, SUBTITLES"""
        self.tracks = namedtuple("_", "selected Videos Audios TimedText") # track()
        self.tracks.Videos = []
        self.tracks.Audios = []
        self.tracks.TimedText = []

    def filtering(self, video_order="HIGHEST"):
        self.tracks.Videos = self.video_filter_by_high_for_each(self.tracks.Videos) if self.tracks.Videos != [] else []
        self.tracks.Audios = self.audio_language_filter(self.tracks.Audios) if self.tracks.Audios != [] else []
        self.tracks.TimedText = self.subtitle_language_filter(self.tracks.TimedText) if self.tracks.TimedText != [] else []
        return self.tracks

    def subtitle_language_filter(self, media: list):
        forced = set()
        sdh = set()
        normal = set()
        cc = set()
        filtered_media = []

        for track in media:
            if track.Type == "SUBTITLE":
                if not track.Language in normal:
                    filtered_media.append(track)
                    normal.add(track.Language)

        for track in media:
            if track.Type == "CC":
                if not track.Language in cc:
                    filtered_media.append(track)
                    cc.add(track.Language)

        for track in media:
            if track.Type == "SDH":
                if not track.Language in sdh:
                    filtered_media.append(track)
                    sdh.add(track.Language)

        for track in media:
            if track.Type == "FORCED":
                if not track.Language in forced:
                    filtered_media.append(track)
                    forced.add(track.Language)

        return filtered_media

    def video_filter(self, videos: list, video_order="HIGHEST"):
        videos = self.video_filter_by_high_for_each(videos)
        by_resolution = self.resolution(videos, video_order)

        if by_resolution:
            return by_resolution
        elif video_order == "BITRATE":
            return sorted(videos, key=lambda k: int(k.Bitrate))[-1]
        elif video_order == "LARGEST_OVERALL":
            return (
                sorted(videos, key=lambda k: int(k.Size))[-1]
                if videos[0].Size
                else sorted(videos, key=lambda k: int(k.Bitrate))[-1]
            )
        elif video_order == "HIGHEST":
            return sorted(videos, key=lambda k: (int(k.Height), int(k.Bitrate)))[-1]
        else:
            return sorted(videos, key=lambda k: (int(k.Height), int(k.Bitrate)))[-1]

    def resolution(self, videos, video_order):
        video_order = re.search(r"\d+", video_order)
        if not video_order:
            return None

        return sorted(
            [x for x in videos if int(x.Height) == int(video_order.group())],
            key=lambda k: int(k.Bitrate),
        )[-1]

    def video_filter_by_high_for_each(self, videos: list):
        return sorted(videos, key=lambda k: (int(k.Height), int(k.Bitrate)))

    def audio_language_filter(self, media: list):
        dialog = set()
        commentary = set()
        descriptive = set()
        filtered_media = []

        for track in sorted(media, key=lambda k: int(k.Bitrate), reverse=True):
            if track.Type == "DIALOG":
                if not track.Language in dialog:
                    filtered_media.append(track)
                    dialog.add(track.Language)

        for track in sorted(media, key=lambda k: int(k.Bitrate), reverse=True):
            if track.Type == "COMMENTARY":
                if not track.Language in commentary:
                    filtered_media.append(track)
                    commentary.add(track.Language)

        for track in sorted(media, key=lambda k: int(k.Bitrate), reverse=True):
            if track.Type == "DESCRIPTIVE":
                if not track.Language in descriptive:
                    filtered_media.append(track)
                    descriptive.add(track.Language)

        return filtered_media

    def getInfo(self, track, Type="NONE"):
        # return None
        text = []
        if Type == "SUBTITLE":
            if track.Type:
                text += ["Type: {}".format(track.Type)]
            if track.Profile:
                text += ["Profile: {}".format(track.Profile)]
            if track.Name:
                text += ["Name: {}".format(track.Name)]
            if track.Language:
                text += ["Language: {}".format(track.Language)]
        elif Type == "AUDIO":
            if track.Type:
                text += ["Type: {}".format(track.Type)]
            if track.Drm:
                text += ["Drm: {}".format(track.Drm)]
            if track.Channels:
                text += ["Channels: {}".format(track.Channels)]
            if track.Codec:
                text += ["Codec: {}".format(track.Codec)]
            if track.Profile:
                text += ["Profile: {}".format(track.Profile)]
            if track.Bitrate:
                text += ["Bitrate: {}kbps".format(track.Bitrate)]
            if track.Size:
                text += ["Size: {}".format(f"{track.Size/1048576:0.2f} MiB" if track.Size < 1073741824 else f"{track.Size/1073741824:0.2f} GiB")]
            if track.Name:
                text += ["Name: {}".format(track.Name)]
            if track.Language:
                if track.Original:
                    text += ["Language: {} (ORIGINAL)".format(track.Language)]
                else:
                    text += ["Language: {}".format(track.Language)]

        elif Type == "VIDEO":
            if track.Type:
                text += ["Type: {}".format(track.Type)]
            if track.Drm:
                text += ["Drm: {}".format(track.Drm)]
            if track.FrameRate:
                text += ["FrameRate: {}".format(track.FrameRate)]
            if track.Codec:
                text += ["Codec: {}".format(track.Codec)]
            if track.Profile:
                text += ["Profile: {}".format(track.Profile)]
            if track.Bitrate:
                text += ["Bitrate: {}kbps".format(track.Bitrate)]
            if track.Size:
                text += ["Size: {}".format(f"{track.Size/1048576:0.2f} MiB" if track.Size < 1073741824 else f"{track.Size/1073741824:0.2f} GiB")]
            if track.Height and track.Width:
                text += ["Resolution: {}x{}".format(track.Width, track.Height)]

        return "{} - {}".format(Type, " | ".join(text))

    def add_subtitle(self, **kwargs):
        Text = namedtuple("_", "Text")
        Text.DownloadType = kwargs.get("DownloadType", "URL")  # ["URL", "DASH"]
        Text.Url = kwargs.get("Url", None)
        Text.Segments = kwargs.get("Segments", None)
        Text.Profile = kwargs.get("Profile", None)  # ["WEBVTT", "DFXP", "SRT", "XML", "TTML"]
        Text.Type = kwargs.get("Type", None)  # ["SUBTITLE", "FORCED", "CC", "SDH"]
        Text.Language = kwargs.get("Language", None)
        Text.Name = kwargs.get("Name", None)
        Text.Cdn = kwargs.get("Cdn", None)
        Text.Extras = kwargs.get("Extras", None)
        Text.Info = self.getInfo(Text, "SUBTITLE")
        self.tracks.TimedText.append(Text)

        return

    def add_audio(self, **kwargs):
        Audio = namedtuple("_", "Audio")
        Audio.DownloadType = kwargs.get("DownloadType", "URL")  # ["URL", "DASH"]
        Audio.Url = kwargs.get("Url", None)
        Audio.Segments = kwargs.get("Segments", None)
        Audio.Type = kwargs.get("Type", None)  # ["DIALOG", "COMMENTARY", "DESCRIPTIVE"]
        Audio.Profile = kwargs.get("Profile", None)  # ["AAC", "EAC3", "AC3", "M4A", "OGG", "DTS", "UNKNOWN"]
        Audio.Language = kwargs.get("Language", None)
        Audio.Name = kwargs.get("Name", None)
        Audio.Drm = kwargs.get("Drm", None)
        Audio.Size = kwargs.get("Size", None)
        Audio.Bitrate = kwargs.get("Bitrate", None)
        Audio.Codec = kwargs.get("Codec", None)
        Audio.Cdn = kwargs.get("Cdn", None)
        Audio.PSSH = kwargs.get("PSSH", None)
        Audio.Original = kwargs.get("Original", None)
        Audio.Channels = kwargs.get("Channels", None)
        Audio.Extras = kwargs.get("Extras", None)
        Audio.Info = self.getInfo(Audio, "AUDIO")
        self.tracks.Audios.append(Audio)

        return

    def add_video(self, **kwargs):
        Video = namedtuple("_", "Video")
        Video.DownloadType = kwargs.get("DownloadType", "URL")  # ["URL", "DASH"]
        Video.Url = kwargs.get("Url", None)
        Video.Segments = kwargs.get("Segments", None)
        Video.Type = kwargs.get("Type", None)  # ["CONTENT", "TRAILER", "UNKNOWN"]
        Video.Profile = kwargs.get("Profile", None)  # ["AVC", "HEVC", "HDR", "VP9", "DOLBY_VISION", "UNKNOWN"]
        Video.Drm = kwargs.get("Drm", None)
        Video.FrameRate = kwargs.get("FrameRate", None)
        Video.Size = kwargs.get("Size", None)
        Video.Bitrate = kwargs.get("Bitrate", None)
        Video.Codec = kwargs.get("Codec", None)
        Video.Height = kwargs.get("Height", None)
        Video.Width = kwargs.get("Width", None)
        Video.Cdn = kwargs.get("Cdn", None)
        Video.PSSH = kwargs.get("PSSH", None)
        Video.Extras = kwargs.get("Extras", None)
        Video.Info = self.getInfo(Video, "VIDEO")
        self.tracks.Videos.append(Video)

        return
