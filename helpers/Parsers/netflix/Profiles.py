class Profiles:
    def __init__(self):
        self.BPL = "bpl"
        self.MPL = "mpl"
        self.HPL = "hpl"
        self.HEVC = "hevc"
        self.HDR = "hdr"
        self.DV5 = "dv5"
        self.VP9 = "vp9"

        self.PLAYREADY = "playready"
        self.DASH = "dash"
        self.CENC = "cenc"
        self.PRK = "prk"
        self.MAIN = "main"
        self.MAIN10 = "main10"
        self.TL = "tl"
        self.DO = "do"
        self.H264 = "h264"
        self.PROFILE0 = "profile0"
        self.PROFILE2 = "profile2"

        self.BASE = ["BIF240", "BIF320", "webvtt-lssdh-ios8", "dfxp-ls-sdh"]
        self.AUDIO = {
            "AAC": ["heaac-2-dash", "heaac-2hq-dash"],
            "AC3": ["dd-5.1-dash"],
            "EAC3": ["ddplus-5.1-dash", "ddplus-5.1hq-dash"],
            "ATMOS": [
                "ddplus-2.0-dash",
                "dd-5.1-dash",
                "ddplus-5.1-dash",
                "ddplus-5.1hq-dash",
                "ddplus-atmos-dash",
            ],
        }

    def add_do(self, profiles):
        do_profiles = []

        for p in profiles:
            if p.endswith("prk"):
                p = f"{p}-{self.DO}"
            do_profiles.append(p)

        return do_profiles

    def get(self, profile="MAIN", resolution="FHD"):
        # MAIN
        if profile == "MAIN" and resolution == "SD":
            return [
                f"{self.PLAYREADY}-{self.H264}{self.BPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.BPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}22-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}22-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}30-{self.DASH}-{self.PRK}",
            ]
        elif profile == "MAIN" and resolution == "HD":
            return [
                f"{self.PLAYREADY}-{self.H264}{self.BPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.BPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}22-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}22-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}31-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}31-{self.DASH}-{self.PRK}",
            ]
        elif profile == "MAIN" and resolution == "FHD":
            return [
                f"{self.PLAYREADY}-{self.H264}{self.BPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.BPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}22-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}22-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}40-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}40-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}41-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.MPL}41-{self.DASH}-{self.PRK}",
            ]
        # HIGH
        elif profile == "HIGH" and resolution == "SD":
            return [
                f"{self.PLAYREADY}-{self.H264}{self.HPL}22-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}22-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}30-{self.DASH}-{self.PRK}",
            ]
        elif profile == "HIGH" and resolution == "HD":
            return [
                f"{self.PLAYREADY}-{self.H264}{self.HPL}22-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}22-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}31-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}31-{self.DASH}-{self.PRK}",
            ]
        elif profile == "HIGH" and resolution == "FHD":
            return [
                f"{self.PLAYREADY}-{self.H264}{self.HPL}22-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}22-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}30-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}30-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}40-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}40-{self.DASH}-{self.PRK}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}41-{self.DASH}",
                f"{self.PLAYREADY}-{self.H264}{self.HPL}41-{self.DASH}-{self.PRK}",
            ]
        # VP9
        elif profile == "VP9" and resolution == "SD":
            return [
                f"{self.VP9}-{self.PROFILE0}-L21-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L21-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE0}-L30-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE2}-L30-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE2}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        elif profile == "VP9" and resolution == "HD":
            return [
                f"{self.VP9}-{self.PROFILE0}-L21-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L21-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE0}-L30-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE2}-L30-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE2}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE0}-L31-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE2}-L31-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE2}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        elif profile == "VP9" and resolution == "FHD":
            return [
                f"{self.VP9}-{self.PROFILE0}-L21-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L21-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE0}-L30-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE2}-L30-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE2}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE0}-L31-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE2}-L31-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE2}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE0}-L40-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE0}-L40-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.VP9}-{self.PROFILE2}-L41-{self.DASH}-{self.CENC}",
                f"{self.VP9}-{self.PROFILE2}-L41-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        # HEVC
        elif profile == "HEVC" and resolution == "SD":
            return [
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.TL}",
            ]
        elif profile == "HEVC" and resolution == "HD":
            return [
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.TL}",
                f"{self.HEVC}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.TL}",
            ]
        elif profile == "HEVC" and resolution == "FHD":
            return [
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.TL}",
                f"{self.HEVC}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.TL}",
                f"{self.HEVC}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}-{self.TL}",
                f"{self.HEVC}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}-{self.TL}",
            ]
        # HDR
        elif profile == "HDR" and resolution == "SD":
            return [
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        elif profile == "HDR" and resolution == "HD":
            return [
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        elif profile == "HDR" and resolution == "FHD":
            return [
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.HDR}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        # DOLBY_VISION
        elif profile == "DOLBY_VISION" and resolution == "SD":
            return [
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        elif profile == "DOLBY_VISION" and resolution == "HD":
            return [
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
            ]
        elif profile == "DOLBY_VISION" and resolution == "FHD":
            return [
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L30-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L31-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L40-{self.DASH}-{self.CENC}-{self.PRK}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}",
                f"{self.HEVC}-{self.DV5}-{self.MAIN10}-L41-{self.DASH}-{self.CENC}-{self.PRK}",
            ]

        return []
