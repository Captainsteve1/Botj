import argparse
import json
import os
import sys
import urllib3
from helpers.main import main

def wvripper():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    parser = argparse.ArgumentParser(description="Widevine Ripper AKA WVRipper")
    parser.add_argument("content", nargs="?", help="Content URL or ID")
    parser.add_argument("--service", dest="service", help="Set the Service Name", default=None, choices=[
        "NETFLIX", "AMAZON", "APPLETV", "DISNEYPLUS", "SHAHID",
        "HULU", "STAN", "RAKUTEN", "GOOGLE", "FANDANGONOW",
        "PEACOCKTV", "HBOMAX", "OSN", "ITUNES", "PARAMOUNT", "STARPLUS"])
    parser.add_argument("--quality", "-q", dest="resolution", type=int, help="Configure Video resolution", default=1920)
    parser.add_argument("--output", "-o", dest="output", help="Set Download Folder")
    parser.add_argument("--folder", "-f", dest="outputfolder", help="Set an External Folder to Save Final .mkv File",)
    parser.add_argument("--nv", "--no-video", dest="novideo", help="Skip Downloading Video", action="store_true")
    parser.add_argument("--na", "--no-audio", dest="noaudio", help="Skip Downloading Audio", action="store_true")
    parser.add_argument("--ns", "--no-subs", dest="nosubs", help="Skip Downloading Subtitles", action="store_true")
    parser.add_argument("-e", "--episode", dest="episodeStart", help="Set The NO Episodes Which You Gonna Download", default="1~")
    parser.add_argument("-s", "--season", dest="season", help="Set The NO Season Which You Gonna Download", default=None)
    parser.add_argument("--keep", dest="keep", help="Keep Temp Files After Muxing, By Default All Erased", action="store_true")
    parser.add_argument("--audio-language", "-al", dest="AudioLanguage", help="Add Audio Languages Splited By `,` To Download", default="")
    parser.add_argument("--audio-description-language", "-ad", dest="AudioDescriptionLanguage", help="Add Description Audio Languages Splited By `,` To Download", default="")
    parser.add_argument("--subtitle-language", "-sl", dest="SubtitleLanguage", help="Add Subtitles Languages Splited By `,` To Download", default="")
    parser.add_argument("--subtitle-forced-language", "-fl", dest="ForcedSubtitleLanguage", help="Add Forced Subtitles Languages Splited By `,` To Download", default="")
    parser.add_argument("--title", "-t", dest="title", help="Set An Output For The Downloaded Files", default=None)
    parser.add_argument("--prompt", "-p", dest="prompt", help="Will Enable the Yes/No Prompt When URLs Are Grabbed", action="store_true")
    parser.add_argument("--license", "-keys", dest="license", help="Performe a License key and exit", action="store_true")
    parser.add_argument("--select", dest="select_by_asking", help="Will Let U Select A/V/S when Url Grapped", action="store_true")
    parser.add_argument("--smart-select", dest="smart_select", help="Select A/V/S Using some Algorithms", action="store_true")
    parser.add_argument("--audio-profile", "-ap", dest="audio_profile", choices=["AAC", "AC3", "EAC3", "ATMOS",], help="For Configure Audio Codec", default="ATMOS")
    parser.add_argument("--video-profile", "-vp", dest="video_profile", choices=["AVC", "HEVC", "HDR", "DOLBY_VISION", "VP9", "UHD", "CBR", "CVBR", "MAIN", "HIGH"], help="For Configure Video Codec", default="AVC")
    parser.add_argument("--cdn", dest="Cdn", choices=["ap1", "ap", "ak",], help="For Configure APPLETV CDN", default="ak")
    parser.add_argument("--no-aria2c", dest="noaria2c", help="Do Not Use `aria2c.exe` As Main Downloader", action="store_true")
    parser.add_argument("--no-chapters", "-nc", dest="nochpaters", help="Skip Downloading Chapters", action="store_true")
    parser.add_argument("--asin", action="store", dest="asin", help="Download From AMAZON With `asin`", default=None)
    parser.add_argument("--android", dest="android_mode", help="Enable Android Mode For AMAZON", action="store_true", default=False)
    parser.add_argument("--sd", dest="primevideo_sd", help="Download SD Quality LINUX Users From AMAZON", action="store_true", default=False)
    parser.add_argument("--region", dest="region", choices=["uk", "de", "us", "jp", "ps", "eu", "ca", "na", "fe"], help="For Configure AMAZON `region`", default=None)
    parser.add_argument("--nordvpn", "-nrd", action="store", dest="nordvpn", help="Downloading Using nordvpn proxies", default=None)
    parser.add_argument("--proxy", action="store", dest="proxy", help="Downloading Using proxy", default=None)
    parser.add_argument("--privatevpn", "-prv", action="store", dest="privtvpn", help="Downloading Using privatevpn proxies", default=None)
    parser.add_argument("--torguardvpn", "-tor", action="store", dest="torguardvpn", help="Downloading Using torguardvpn proxies", default=None)
    parser.add_argument("--no-proxy", dest="no_download_proxy", help="Do not Use proxy when Downloading", action="store_true", default=False)
    parser.add_argument("--nordvpn-host", "-nrdh", action="store", dest="nordvpn_host", help="Set localhost with port for nordvpn", default="localhost:8081")
    parser.add_argument("--show-asin", dest="show_asin", help="Show amazon titles asin", action="store_true")
    parser.add_argument("--watcher", dest="watcher", help="watcher for hbomax", action="store_true")

    parser.add_argument("-u", dest="upload", help="Active upload with packer", action="store_true", default=False)
    parser.add_argument(
        "--trackers",
        dest="trackers",
        help="choose one or more tracker to upload from: iptorrents,torrentday",
        action="store",
        default="iptorrents,torrentday",
    )
    parser.add_argument(
        "--type",
        dest="content_type",
        help="define content type",
        action="store",
        choices=["movie", "episode"],
        default=None,
    )
    parser.add_argument(
        "--desc",
        dest="description",
        help="pass a description file made by desc_maker.py",
        action="store",
        default=None,
    )
    parser.add_argument(
        "--seed",
        dest="seed",
        help="Seed the torrent that downloaded from tracker after upload",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--local-seed",
        dest="local_seed",
        help="Seed the torrent we created not the downloaded from tracker after upload",
        action="store_true",
        default=False,
    )

    parser.add_argument("--group", "-gr", dest="muxer_group", help="Set Group Name will override the one in config", action="store", default=None)
    parser.add_argument("--tag-style", "-ts", dest="muxer_scheme", help="Set The Naming Tagging Style For Output", default=None)
    parser.add_argument("--mkvmerge-extras", "-mkve", dest="extra_mkvmerge_params", help="Add Extra Commands For `mkvmerge.exe`", action="store", default=None)
    parser.add_argument("--mkvmerge-defaults", "-mkvd", dest="audio_subtitle_defaults", help="Set Defaults A/V/S Tracks For .mkv", action="store", default=None)
    parser.add_argument("--no-mux", dest="nomux", help="Skip Muxing", action="store_true", default=None)
    parser.add_argument("--schedule", dest="schedule", help="Schedule Downloads To Start Downloading at Specified Time", default=None)
    parser.add_argument("--enable-file-assister", dest="enable_file_assister", help="Do Some Stuff/Changes For Each Download When Finish", action="store_true", default=None)
    parser.add_argument("--save-preset", dest="save_preset", help="Save Customized Args For Later Use", default=None)
    parser.add_argument("--load-preset", dest="load_preset", help="Load Customized Args", default=None)
    parser.add_argument("--thread", dest="thread_tasks", help="thread downloading", action="store_true", default=None)
    parser.add_argument("--credit", dest="credit", help="download disney plus content with credits", action="store_true", default=None)
    parser.add_argument("--shaka-decrypt", dest="shaka_decrypt", help="decrypt appletv conten 4k (video only) with shaka-decrypt", action="store_true", default=None)
    parser.add_argument("--secret", dest="secret", help="secret", action="store", default=None)
    parser.add_argument("--itunes-region", dest="itunes_region", help="itunes_region", default=None)
    parser.add_argument("--host", dest="host", help="host", default=None)
    parser.add_argument("--retry", dest="retry", type=int, help="retry", default=0)
    parser.add_argument("--saldl", dest="saldl", help="saldl downloading", action="store_true", default=None)
    parser.add_argument("--rental", dest="rental", help="rental downloading", action="store_true", default=None)
    parser.add_argument("--ccextractor", dest="ccextractor", help="ccextractor downloading", action="store_true", default=None)

    parser.add_argument("--email", dest="email", type=str, help="email", default=None)
    parser.add_argument("--password", dest="password", type=str, help="password", default=None)
    parser.add_argument("--cookies", dest="cookies", type=str, help="cookies", default=None)
    # parser.add_argument("--itunes-profile", dest="itunes_profile", help="itunes_region", default=None)
    parser.add_argument("--market", dest="rakuten_market", type=str, help="rakuten_market", default=None)
    parser.add_argument("--tv-plex", dest="with_show_title", help="add finished downloaded seasons in folder with it show title name", action="store_true", default=None)
    parser.add_argument("--imax", dest="disney_imax", help="grap imax version for disney plus", action="store_true", default=None)
    # parser.add_argument("--tv-plex", dest="with_show_title", type=int, help="add finished downloaded seasons in folder with it show title name", default=None)

    args = parser.parse_args()

    os.environ["THREAD_MODE"] = "YES" if args.thread_tasks else "NO"

    wv = main(args)
    args, commands = wv._arguments_manager__()
    wv._start_service(args, commands)
    wv._eta()
    return

if __name__ == "__main__":
    wvripper()

