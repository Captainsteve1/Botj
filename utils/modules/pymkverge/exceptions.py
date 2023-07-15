"""This module stores various exceptions used by the client"""


class mkvmergeError(Exception):
    """Exception for mkvmerge.exe issues"""


class UnknownLanguage(Exception):
    """Exception for iso code language issues"""


class mediainfoError(Exception):
    """Exception for mediainfo.exe issues"""
