import os
import platform
from pathlib import Path
from time import gmtime, strftime

import toml
from helpers.Utils.utils import tuple_, utils
import random
import string
import sys
from os.path import dirname, join
from helpers.Utils.utils import get_current_dir, tuple_, utils
from pywidevine.cdm import cdm, deviceconfig

PATH = str(Path(os.path.realpath(__name__)).parent)

def load_config():
    cfg = Path(f"{PATH}/configs/config.toml")
    data = cfg.read_text(encoding="utf8")
    return toml.loads(data)

config_data = load_config()

# ~ CONFIG
config = tuple_()

# ~ dirPath
config.dirPath = PATH

# ~ CDM
config.CDM = tuple_()
config.CDM.chrome = deviceconfig.chrome_cdm_1610_l3
config.CDM.andrl3 = deviceconfig.android_s905x_l3
config.CDM.andrl3_v2 = deviceconfig.android_phone8162_l3
# ~ DEVICES
config.DEVICES = tuple_()
config.DEVICES.NETFLIX = config.CDM.chrome
config.DEVICES.APPLETV = config.CDM.andrl3_v2
config.DEVICES.ITUNES = config.CDM.andrl3_v2
config.DEVICES.AMAZON = config.CDM.andrl3_v2
config.DEVICES.DCUNIVERSE = config.CDM.andrl3_v2
config.DEVICES.DISNEYPLUS = config.CDM.andrl3_v2
config.DEVICES.STARPLUS = config.CDM.andrl3_v2
config.DEVICES.HULU = config.CDM.andrl3_v2
config.DEVICES.STAN = config.CDM.andrl3_v2
config.DEVICES.SHAHID = config.CDM.andrl3_v2
config.DEVICES.RAKUTEN = config.CDM.andrl3_v2
config.DEVICES.GOOGLEPLAY = config.CDM.andrl3_v2
config.DEVICES.FANDANGONOW = config.CDM.andrl3_v2
config.DEVICES.HBOMAX = config.CDM.andrl3_v2
config.DEVICES.OSN = config.CDM.andrl3_v2
config.DEVICES.PEACOCK = config.CDM.andrl3_v2
# ~ MUXER
config.MUXER = tuple_()
config.MUXER.LANGUAGE_CODE_LIST = f"{config.dirPath}/tools/languages.json"

config.MUXER.GROUP = config_data["OTHERS"]["GROUP"]
config.MUXER.DELETE_EPISODE_TITLE = False
config.MUXER.SCHEME = "P2P"
config.MUXER.SCHEMES = {
    "CC": "{t}",
    "sdr": "{t}.{r}.{s}.WEB-DL.{ac}.x265-{gr}",
    "hdr": "{t}.{r}.{s}.WEB-DL.{ac}.HDR.{vc}-{gr}",
    "P2P": "{t}.{r}.{s}.WEB-DL.{ac}.{vc}-{gr}",
    "psig": "{t}.MULTi.{r}.{s}.WEB-DL.{ac}.{vc}-{gr}",
    "nsrc": "{t}.{r}.WEB-DL.{ac}.{vc}-{gr}",
    "SIMPLE": "{t}.{r}.{s}.WEB-DL-{gr}",
}
# ~ PATHS
config.PATHS = tuple_()
config.PATHS.DL_FOLDER = f"{config.dirPath}"
config.PATHS.DIR_PATH = f"{config.dirPath}"
config.PATHS.ITUNES_LOGINS = f"{config.dirPath}/configs/itunes.yml"
config.PATHS.BINARY_PATH = f"{config.dirPath}/tools"
config.PATHS.COOKIES_PATH = f"{config.dirPath}/configs/Cookies"
config.PATHS.PRESETS_FOLDER = f"{config.dirPath}/configs/Presets"
config.PATHS.LOGGING_FOLDER = f"{config.dirPath}/configs/Logging"
config.PATHS.KEYS_PATH = f"{config.dirPath}/configs/KEYS"
config.PATHS.TOKENS_PATH = f"{config.dirPath}/configs/Tokens"
config.PATHS.JSON_PATH = f"{config.dirPath}/json"
config.PATHS.LOGA_PATH = f"{config.dirPath}/tools/aria2c/aria2c"
# ~ SETTINGS
config.SETTINGS = tuple_()
config.SETTINGS.enable_aria2c_logging = False
config.SETTINGS.enable_menu_selection = True
config.SETTINGS.enable_aria2c_moded_progress_bar = False
config.SETTINGS.external_txt_key = f"{config.PATHS.KEYS_PATH}/external.txt"
config.SETTINGS.skip_video_demux = [
    "HBOMAX",
    "APPLETV",
    "GOOGLEPLAY",
    "DCUNIVERSE",
    "ITUNES"
]

# ~ VPN
config.VPN = tuple_()
config.VPN.proxies = None
config.VPN.nordvpn = tuple_()
config.VPN.nordvpn.port = config_data["VPN"]["nordvpn"]["port"]
config.VPN.nordvpn.email = config_data["VPN"]["nordvpn"]["email"]
config.VPN.nordvpn.passwd = config_data["VPN"]["nordvpn"]["passwd"]
config.VPN.nordvpn.http = "https://{email}:{passwd}@{ip}:{port}"
config.VPN.private = tuple_()
config.VPN.private.port = config_data["VPN"]["private"]["port"]
config.VPN.private.email = config_data["VPN"]["nordvpn"]["email"]
config.VPN.private.passwd = config_data["VPN"]["nordvpn"]["passwd"]
config.VPN.private.http = "http://{email}:{passwd}@{ip}:{port}"
config.VPN.torguard = tuple_()
config.VPN.torguard.port = config_data["VPN"]["torguard"]["port"]
config.VPN.torguard.email = config_data["VPN"]["nordvpn"]["email"]
config.VPN.torguard.passwd = config_data["VPN"]["nordvpn"]["passwd"]
config.VPN.torguard.http = "http://{email}:{passwd}@{ip}:{port}"
# ~ BIN
config.BIN = tuple_()
if platform.system() == "Linux":
    config.BIN.mp4decrypt = f"{config.PATHS.BINARY_PATH}/bento4/mp4decrypt"
    config.BIN.mp4dump = f"{config.PATHS.BINARY_PATH}/bento4/mp4dump"
    config.BIN.pandsdecryptor = f"{config.PATHS.BINARY_PATH}/bento4/mp4decrypt"
    config.BIN.shaka_packager = f"{config.PATHS.BINARY_PATH}/decryptor/packager-linux"
    config.BIN.mp4box = "mp4box"
    config.BIN.ffmpeg = "ffmpeg"
    config.BIN.ffprobe = "ffprobe"
    config.BIN.ffplay = "ffplay"
    config.BIN.MediaInfo = "mediainfo"
    config.BIN.mkvmerge = "mkvmerge"
    config.BIN.youtube = f"{config.PATHS.BINARY_PATH}/youtube-dl/youtube_dl/__main__.py"
    config.BIN.aria2c = "aria2c"
    config.BIN.SubtitleEdit = "mono SubtitleEdit"
    config.BIN.SubtitleEdit = "mono SubtitleEdit"
    config.BIN.SaldDL = f"SaldDL"
else:
    config.BIN.mp4decrypt = f"{config.PATHS.BINARY_PATH}/bento4/mp4decrypt.exe"
    config.BIN.mp4demuxer = f"{config.PATHS.BINARY_PATH}/mp4box/mp4demuxer.exe"
    config.BIN.mp4dump = f"{config.PATHS.BINARY_PATH}/bento4/mp4dump.exe"
    config.BIN.pandsdecryptor = f"{config.PATHS.BINARY_PATH}/decryptor/pandsdecryptor.exe"
    config.BIN.shaka_packager = f"{config.PATHS.BINARY_PATH}/decryptor/packager-win.exe"
    config.BIN.mp4box = f"{config.PATHS.BINARY_PATH}/mp4box/mp4box.exe"
    config.BIN.ffmpeg = f"{config.PATHS.BINARY_PATH}/ffmpeg/ffmpeg.exe"
    config.BIN.ffprobe = f"{config.PATHS.BINARY_PATH}/ffmpeg/ffprobe.exe"
    config.BIN.ffplay = f"{config.PATHS.BINARY_PATH}/ffmpeg/ffplay.exe"
    config.BIN.MediaInfo = f"{config.PATHS.BINARY_PATH}/MediaInfo/MediaInfo.exe"
    config.BIN.mkvmerge = f"{config.PATHS.BINARY_PATH}/mkvtoolnix/mkvmerge.exe"
    config.BIN.youtube = f"{config.PATHS.BINARY_PATH}/youtube-dl/youtube-dl.exe"
    config.BIN.aria2c = f"{config.PATHS.BINARY_PATH}/aria2c/aria2c.exe"
    config.BIN.SubtitleEdit = f"{config.PATHS.BINARY_PATH}/SubtitleEdit/SubtitleEdit.exe"
    config.BIN.CCExtractor = f"{config.PATHS.BINARY_PATH}/ccextractor/ccextractorwin.exe"
    config.BIN.SaldDL = f"{config.PATHS.BINARY_PATH}/SaldDL.exe"
# ~ SERVICES
config.SERVICES = tuple_()
# ╔═══════════════════
# ║
# ║  NETFLIX    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.NETFLIX = tuple_()
config.SERVICES.NETFLIX.NAME = "NETFLIX"
config.SERVICES.NETFLIX.TAG = "NF"
config.SERVICES.NETFLIX.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_nf.txt"
config.SERVICES.NETFLIX.keys_file = f"{config.PATHS.KEYS_PATH}/netflix.keys"
config.SERVICES.NETFLIX.token_file = f"{config.PATHS.TOKENS_PATH}/netflix_token.json"
config.SERVICES.NETFLIX.email = config_data["CREDENTIALS"]["NETFLIX"]["email"]
config.SERVICES.NETFLIX.password = config_data["CREDENTIALS"]["NETFLIX"]["password"]
config.SERVICES.NETFLIX.profiles = f"{config.PATHS.BINARY_PATH}/profiles.json"
config.SERVICES.NETFLIX.esn = "NFCDIE-03-{}".format(utils().random_hex(30))
config.SERVICES.NETFLIX.esn_manifest = "NFCDIE-03-{}".format(utils().random_hex(30))
config.SERVICES.NETFLIX.androidesn = "NFCDIE-03-{}".format(utils().random_hex(30))
ESN = config_data["OTHERS"]["ESN"]
#config.SERVICES.NETFLIX.esn = "NFCDCH-02-GRTTKNT2LAER6P2RWAMTNKJR9HG6XV"
#config.SERVICES.NETFLIX.esn_manifest = "NFANDROID2-PRV-SHIELDANDROIDTV-NVIDISHIELD=ANDROID=TV-5485-D4D24ABA523EF168874D77EEF136881FFEEEE72B0F594230D4FA05C24C8F756A"
#config.SERVICES.NETFLIX.androidesn = f"NFANDROID1-PRV-P-GOOGLEPIXEL=4=XL-{ESN}-BF80614C967DFD2D1CCDAAD69BCFD7063B037E6951CDF172C3D77792104CE05F"
config.SERVICES.NETFLIX.metada_language = "en"
config.SERVICES.NETFLIX.manifest_language = ["en-US"]

# ╔═══════════════════
# ║
# ║  APPLETV    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.APPLETV = tuple_()
config.SERVICES.APPLETV.NAME = "APPLETV"
config.SERVICES.APPLETV.TAG = "APTV"
config.SERVICES.APPLETV.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_apple.txt"
config.SERVICES.APPLETV.keys_file = f"{config.PATHS.KEYS_PATH}/apple.keys"
config.SERVICES.APPLETV.token_file = f"{config.PATHS.TOKENS_PATH}/appletv.json"
config.SERVICES.APPLETV.email = "Latinomhd@gmail.com"
config.SERVICES.APPLETV.password = "9122Teamoalvarex"
# ╔═══════════════════
# ║
# ║  ITUNES    -> [SETTINGS]
# ║
# ╚═══════════════════
# itunes_logins_raw = config_data["CREDENTIALS"]["ITUNES"]["logins"]
# itunes_logins = dict()
# for key, value in itunes_logins_raw.items():
#     if value.get("cookies"):
#         itunes_logins["key"] = {
#             "cookies": value["cookies"].format(path=config.PATHS.COOKIES_PATH),
#             "email": value["email"],
#             "password": value["password"],
#         }
config.SERVICES.ITUNES = tuple_()
config.SERVICES.ITUNES.NAME = "ITUNES"
config.SERVICES.ITUNES.TAG = "ITUN"
config.SERVICES.ITUNES.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_itunes.txt"
config.SERVICES.ITUNES.keys_file = f"{config.PATHS.KEYS_PATH}/itunes.keys"
config.SERVICES.ITUNES.token_file = f"{config.PATHS.TOKENS_PATH}/itunes.json"
config.SERVICES.ITUNES.email = None # config_data["CREDENTIALS"]["ITUNES"]["email"]
config.SERVICES.ITUNES.password = None # config_data["CREDENTIALS"]["ITUNES"]["password"]
config.SERVICES.ITUNES.logins = None
# ╔═══════════════════
# ║
# ║  ITUNES    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.PARAMOUNT = tuple_()
config.SERVICES.PARAMOUNT.NAME = "PARAMOUNT"
config.SERVICES.PARAMOUNT.TAG = "PMTP"
config.SERVICES.PARAMOUNT.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_paramount.txt"
config.SERVICES.PARAMOUNT.keys_file = f"{config.PATHS.KEYS_PATH}/paramount.keys"
config.SERVICES.PARAMOUNT.token_file = f"{config.PATHS.TOKENS_PATH}/paramount.json"
config.SERVICES.PARAMOUNT.email = None
config.SERVICES.PARAMOUNT.password = None

# ╔═══════════════════
# ║
# ║  DISNEYPLUS    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.DISNEYPLUS = tuple_()
config.SERVICES.DISNEYPLUS.NAME = "DISNEYPLUS"
config.SERVICES.DISNEYPLUS.TAG = "DSNP"
config.SERVICES.DISNEYPLUS.token_file = f"{config.PATHS.TOKENS_PATH}/disney.json"
config.SERVICES.DISNEYPLUS.keys_file = f"{config.PATHS.KEYS_PATH}/disneyplus.keys"
config.SERVICES.DISNEYPLUS.email = config_data["CREDENTIALS"]["DISNEYPLUS"]["email"]
config.SERVICES.DISNEYPLUS.password = config_data["CREDENTIALS"]["DISNEYPLUS"]["password"]
# ╔═══════════════════
# ║
# ║  STARPLUS    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.STARPLUS = tuple_()
config.SERVICES.STARPLUS.NAME = "STARPLUS"
config.SERVICES.STARPLUS.TAG = "DSNP"
config.SERVICES.STARPLUS.token_file = f"{config.PATHS.TOKENS_PATH}/starplus.json"
config.SERVICES.STARPLUS.keys_file = f"{config.PATHS.KEYS_PATH}/starplus.keys"
config.SERVICES.STARPLUS.email = config_data["CREDENTIALS"]["STARPLUS"]["email"]
config.SERVICES.STARPLUS.password = config_data["CREDENTIALS"]["STARPLUS"]["password"]
# ╔═══════════════════
# ║
# ║  AMAZON    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.AMAZON = tuple_()
config.SERVICES.AMAZON.NAME = "AMAZON"
config.SERVICES.AMAZON.TAG = "AMZN"
config.SERVICES.AMAZON.keys_file = f"{config.PATHS.KEYS_PATH}/amazon.keys"
config.SERVICES.AMAZON.cookies_file = config.PATHS.COOKIES_PATH + "/cookies_{region}.txt"
config.SERVICES.AMAZON.token_file = config.PATHS.TOKENS_PATH + "/{region}.json"
# ╔═══════════════════
# ║
# ║  GOOGLEPLAY    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.GOOGLEPLAY = tuple_()
config.SERVICES.GOOGLEPLAY.NAME = "GOOGLEPLAY"
config.SERVICES.GOOGLEPLAY.TAG = "GP"
config.SERVICES.GOOGLEPLAY.keys_file = f"{config.PATHS.KEYS_PATH}/googleplay.keys"
config.SERVICES.GOOGLEPLAY.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_googleplay.txt"
config.SERVICES.GOOGLEPLAY.cookies_file_headers = f"{config.PATHS.COOKIES_PATH}/cookies_googleplay_headers.txt"
# ╔═══════════════════
# ║
# ║  HULU    -> [SETTINGS]
# ║
# ╚═══════════════════=
config.SERVICES.HULU = tuple_()
config.SERVICES.HULU.NAME = "HULU"
config.SERVICES.HULU.TAG = "HULU"
config.SERVICES.HULU.keys_file = f"{config.PATHS.KEYS_PATH}/hulu.keys"
config.SERVICES.HULU.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_hulu.txt"
# ╔═══════════════════
# ║
# ║  DCUNIVERSE    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.DCUNIVERSE = tuple_()
config.SERVICES.DCUNIVERSE.NAME = "DCUNIVERSE"
config.SERVICES.DCUNIVERSE.TAG = "DCU"
config.SERVICES.DCUNIVERSE.keys_file = f"{config.PATHS.KEYS_PATH}/dcu.keys"
config.SERVICES.DCUNIVERSE.token_file = f"{config.PATHS.TOKENS_PATH}/dcuniverse.json"
config.SERVICES.DCUNIVERSE.email = "email"
config.SERVICES.DCUNIVERSE.password = "password"
config.SERVICES.DCUNIVERSE.device_key = "DA59dtVXYLxajktV"
# ╔═══════════════════
# ║
# ║  STAN    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.STAN = tuple_()
config.SERVICES.STAN.NAME = "STAN"
config.SERVICES.STAN.TAG = "STAN"
config.SERVICES.STAN.keys_file = f"{config.PATHS.KEYS_PATH}/stan.keys"
config.SERVICES.STAN.token_file = f"{config.PATHS.TOKENS_PATH}/stan.json"
config.SERVICES.STAN.email = config_data["CREDENTIALS"]["STAN"]["email"]
config.SERVICES.STAN.password = config_data["CREDENTIALS"]["STAN"]["password"]
# ╔═══════════════════
# ║
# ║  HBOMAX    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.HBOMAX = tuple_()
config.SERVICES.HBOMAX.NAME = "HBOMAX"
config.SERVICES.HBOMAX.TAG = "HMAX"
config.SERVICES.HBOMAX.keys_file = f"{config.PATHS.KEYS_PATH}/hbomax.keys"
config.SERVICES.HBOMAX.token_file = f"{config.PATHS.TOKENS_PATH}/hbomax.json"
config.SERVICES.HBOMAX.email = config_data["CREDENTIALS"]["HBOMAX"]["email"]
config.SERVICES.HBOMAX.password = config_data["CREDENTIALS"]["HBOMAX"]["password"]
config.SERVICES.HBOMAX.id_language = "es" # ["en", "es"]
# ╔═══════════════════
# ║
# ║  PEACOCK    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.PEACOCK = tuple_()
config.SERVICES.PEACOCK.NAME = "PEACOCK"
config.SERVICES.PEACOCK.TAG = "PCOK"
config.SERVICES.PEACOCK.keys_file = f"{config.PATHS.KEYS_PATH}/peacock.keys"
config.SERVICES.PEACOCK.token_file = f"{config.PATHS.TOKENS_PATH}/peacock.json"
config.SERVICES.PEACOCK.email = config_data["CREDENTIALS"]["PEACOCK"]["email"]
config.SERVICES.PEACOCK.password = config_data["CREDENTIALS"]["PEACOCK"]["password"]
config.SERVICES.PEACOCK.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_peacock.txt"
# ╔═══════════════════
# ║
# ║  SHAHID    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.SHAHID = tuple_()
config.SERVICES.SHAHID.NAME = "SHAHID"
config.SERVICES.SHAHID.TAG = "SHID"
config.SERVICES.SHAHID.keys_file = f"{config.PATHS.KEYS_PATH}/shahid.keys"
config.SERVICES.SHAHID.token_file = f"{config.PATHS.TOKENS_PATH}/shahid.json"
# ╔═══════════════════
# ║
# ║  OSN    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.OSN = tuple_()
config.SERVICES.OSN.NAME = "OSN"
config.SERVICES.OSN.TAG = "OSN"
config.SERVICES.OSN.keys_file = f"{config.PATHS.KEYS_PATH}/osn.keys"
config.SERVICES.OSN.token_file = f"{config.PATHS.TOKENS_PATH}/osn.json"
config.SERVICES.OSN.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_osn.txt"
config.SERVICES.OSN.proxies = {
    "http": "http://abdalhmohmd8@gmail.com:123456@ae-dub.pvdata.host:8080",
    "https": "http://abdalhmohmd8@gmail.com:123456@ae-dub.pvdata.host:8080",
}
# ╔═══════════════════
# ║
# ║  RAKUTEN    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.RAKUTEN = tuple_()
config.SERVICES.RAKUTEN.NAME = "RAKUTEN"
config.SERVICES.RAKUTEN.TAG = "RKTN"
config.SERVICES.RAKUTEN.email = config_data["CREDENTIALS"]["RAKUTEN"]["email"]
config.SERVICES.RAKUTEN.password = config_data["CREDENTIALS"]["RAKUTEN"]["password"]
config.SERVICES.RAKUTEN.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_rakuten.txt"
config.SERVICES.RAKUTEN.keys_file = f"{config.PATHS.KEYS_PATH}/rakuten.keys"
config.SERVICES.RAKUTEN.token_file = f"{config.PATHS.TOKENS_PATH}/rakuten.json"
# ╔═══════════════════
# ║
# ║  FANDANGONOW    -> [SETTINGS]
# ║
# ╚═══════════════════
config.SERVICES.FANDANGONOW = tuple_()
config.SERVICES.FANDANGONOW.NAME = "FANDANGONOW"
config.SERVICES.FANDANGONOW.TAG = "FNOW"
config.SERVICES.FANDANGONOW.cookies_file = f"{config.PATHS.COOKIES_PATH}/cookies_fandangonow.txt"
config.SERVICES.FANDANGONOW.keys_file = f"{config.PATHS.KEYS_PATH}/fandangonow.keys"

utils().create_dirs_files(
    DIRS=[config.PATHS.COOKIES_PATH, config.PATHS.TOKENS_PATH, config.PATHS.LOGA_PATH, config.PATHS.PRESETS_FOLDER, config.PATHS.LOGGING_FOLDER], FILES=[],
)

PRESETS_FOLDER = config.PATHS.PRESETS_FOLDER
LOG_FILE = os.path.join(config.PATHS.LOGGING_FOLDER, "{}.log".format(strftime("%Y-%m-%d %H,%M,%S", gmtime())))


class wvripper_config:
    def config(self):
        return config
