import re
import unicodedata
from typing import List, Optional

import pysrt

AUTHOR_STRINGS = (
    "synced and corrected by",
    "sync and corrections by",
    "subtitles by",
    "encoded and released by",
    "opensubtitles.org",
    "please rate this subtitle",
    "captioning sponsored by",
    "captioned by",
)

class sdh:
    def __init__(self):
        self._index = None
        self._contents = ''
        self.start = None
        self.end = None

    def __str__(self):
        return '{}\n{} --> {}\n{}\n'.format(self._index, self.start, self.end, self._contents)

    def __eq__(self, other):
        if self.__str__() == other.__str__():
            return True
        return False

    def _get_text(self):
        return self.__str__()

    def _contents_to_list(self):
        if isinstance(self._contents, str):
            self._contents = self._contents.split('\n')

    def _contents_to_str(self):
        if isinstance(self._contents, list):
            self._contents = '\n'.join(self._contents)

    @property
    def index(self):
        if self._index is None:
            return False
        return self._index

    @index.setter
    def index(self, index):
        self._index = int(index)

    @property
    def contents(self):
        return self._contents

    @contents.setter
    def contents(self, item):
        if self._contents:
            self._contents += '\n{}'.format(item)
        else:
            self._contents = '{}'.format(item)

    def _filter_empty(self):
        if not self.contents:
            self.index = 0

    @property
    def lines(self):
        '''Subtitle entry as a newline separated list'''
        return [str(self._index), '{} --> {}'.format(self.start, self.end), *self._contents.split('\n')]

    @staticmethod
    def _remove_comma_space(matchobj):
        return matchobj.group(0).replace(' ,', ',')

    @staticmethod
    def _add_comma_space(matchobj):
        return matchobj.group(0).replace(',', ', ')

    def fix_comma_spaces(self):
        for _ in re.findall(r'[A-Za-z]+\s+,', self._contents):
            self._contents = re.sub(r'[A-Za-z]+\s+,', self._remove_comma_space, self._contents)

        for _ in re.findall(r'[A-Za-z]+,[A-Za-z]+', self._contents):
            self._contents = re.sub(r'[A-Za-z]+,[A-Za-z]+', self._add_comma_space, self._contents)

    def remove_font_colours(self):
        self._contents = re.sub(r'\<font(.*)\>(.*)\</font\>', '', self._contents, flags=re.DOTALL)
        self._filter_empty()

    def remove_asterisks(self):
        if '*' in self._contents:
            self.index = 0

    def remove_music(self):
        self._contents = re.sub(r'♪(.*)♪', '', self._contents, flags=re.DOTALL)
        # Remove behaving as inline
        self._contents_to_list()
        for idx, _ in enumerate(self._contents):
            if any(symbol in self._contents[idx] for symbol in ['#', '♪']):
                self._contents[idx] = ''
        self._contents_to_str()
        self._filter_empty()

    def remove_sound_effects(self):
        # Remove single line brackets
        self._contents_to_list()
        for idx, _ in enumerate(self._contents):
            self._contents[idx] = re.sub(r'[\(\[][\S ]*[\)\]][\s:]*', '', self._contents[idx])

        self._remove_lone_symbols()
        self._contents_to_str()
        # Remove multi-line brackets
        self._contents = re.sub(r'[\(\[][\S\s]*[\)\]][\s:]*', '', self._contents)
        self._filter_empty()

    def replace_names(self):
        # Care is taken here to preserve genuine sentences with a colon.
        names = re.findall(r'([A-Z0-9 ]+ *: *|[A-Z]{1}[a-z]+ *: *)', self._contents)
        if len(names) > 1:
            # Replace names with '- '
            self._contents = re.sub(r'([A-Z0-9 ]+ *: *|[A-Z]{1}[a-z]+ *: *)', '- ', self._contents).lstrip()
        else:
            # Replace name with empty string.
            self._contents = re.sub(r'([A-Z0-9 ]+ *: *|[A-Z]{1}[a-z]+ *: *)', '', self._contents).lstrip()

        self._filter_empty()

    def remove_author(self):
        for author_str in AUTHOR_STRINGS:
            if author_str in self._contents.lower():
                self.index = 0
                break

    def fix_italics(self):
        if '<i>' in self._contents and '</i>' not in self._contents:
            self._contents += '</i>'
        if '</i>' in self._contents and '<i>' not in self._contents:
            self._contents = '<i>' + self._contents
        self._contents = re.sub(r'<i>[\_\-\‐\?#\s¶]*</i>', '', self._contents, flags=re.DOTALL)
        self._remove_lone_symbols()

    def _remove_lone_symbols(self):
        self._contents_to_list()
        for idx, _ in enumerate(self._contents):
            self._contents[idx] = re.sub(r'^[\_\-\‐\?#\s¶]*$', '', self._contents[idx])
            self._contents[idx] = re.sub(r'^[\_\-\‐\?#\s¶]*<i>[\_\-\‐\?#\s¶]*$', '<i>', self._contents[idx])
            self._contents[idx] = re.sub(r'^[\_\-\‐\?#\s¶]*</i>[\_\-\‐\?#\s¶]*$', '</i>', self._contents[idx])
        # Removes empty strings
        self._contents = list(filter(None, self._contents))
        # Set index as 0 for later deletion
        if len(self.contents) == 0:
            self.index = 0
        self._contents_to_str()

class sub_filters(object):
    def __init__(self, content: str) -> None:
        self.content = content
        self.content_srt: List[pysrt.srtitem.SubRipItem] = pysrt.from_string(self.content)

    def get_text(self) -> str:
        return "\n".join([
            f"{i}\n{sub.start} --> {sub.end}\n{sub.text}\n"
            for i, sub in enumerate(self.content_srt, start=1)
        ])

    @staticmethod
    def convert_vtt(text: str) -> str:
        srt = re.sub(r'WEBVTT', '', text)
        srt = re.sub(re.compile(
            r'^(\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}).*',
            re.MULTILINE
        )
            , r'\1', srt)
        srt = re.sub(r"NOTE+(..*)","",srt)
        srt = re.sub(r"X-TIMESTAMP-MAP+(..*)","",srt)
        srt = re.sub(r'</?[cv][^>]+>', '', srt)
        srt = re.sub(re.compile(r'^\s*$', re.MULTILINE), '', srt)
        srt = re.sub(r"&rlm;","",srt)
        srt = re.sub(r"&gt;&gt; ","",srt)
        return srt

    def fix_time_codes_apple_tv(self) -> None:
        filtered = list()
        merged = set()

        for idx, sub in enumerate(self.content_srt):
            if str(sub.start) in merged:
                continue
            filtered.append(sub)
            merged.add(str(sub.start))

        self.content_srt = filtered
        return

    def fix_time_codes(self) -> None:
        filtered = list()
        merged = set()

        for idx, sub in enumerate(self.content_srt):
            if str(sub.start) in merged:
                continue
            for idx2, sub2 in enumerate(self.content_srt):
                if idx == idx2:
                    continue
                if sub.start == sub2.start and sub.end == sub2.end:
                    if sub.text == sub2.text:
                        continue
                    sub.text = f"{sub.text}\n{sub2.text}"
            filtered.append(sub)
            merged.add(str(sub.start))

        self.content_srt = filtered
        return

    def rtl_embedding(self) -> None:
        for _, sub in enumerate(self.content_srt):
            sub.text = re.sub('^', unicodedata.lookup("RIGHT-TO-LEFT EMBEDDING"), sub.text, flags=re.MULTILINE)

        return

    def remove_sdh(
        self,
        remove_font_colours: Optional[bool] = False,
        remove_asterisks: Optional[bool] = False,
        remove_music: Optional[bool] = False,
        remove_sound_effects: Optional[bool] = False,
        replace_names: Optional[bool] = False,
        remove_author: Optional[bool] = False,
        fix_comma_spaces: Optional[bool] = False
    ) -> None:

        subtitles: List[sdh] = list()

        for idx, sub in enumerate(self.content_srt):
            Sub = sdh()
            Sub.index = idx
            Sub.start = sub.start
            Sub.end = sub.end
            Sub.contents = sub.text
            subtitles.append(Sub)

        if remove_font_colours:
            any(map(lambda sub: sub.remove_font_colours(), subtitles))
        if remove_asterisks:
            any(map(lambda sub: sub.remove_asterisks(), subtitles))
        if remove_music:
            any(map(lambda sub: sub.remove_music(), subtitles))
        if remove_sound_effects:
            any(map(lambda sub: sub.remove_sound_effects(), subtitles))
        if replace_names:
            any(map(lambda sub: sub.replace_names(), subtitles))
        if remove_author:
            any(map(lambda sub: sub.remove_author(), subtitles))
        if fix_comma_spaces:
            any(map(lambda sub: sub.fix_comma_spaces(), subtitles))

        any(map(lambda sub: sub.fix_italics(), subtitles))
        # Remove filtered items from list
        subtitles[:] = [sub for sub in subtitles if sub.index]
        # Reassign indices
        for idx, sub in enumerate(subtitles):
            sub.index = idx + 1

        subtitles = "\n".join([str(s) for s in subtitles])
        self.content_srt = pysrt.from_string(subtitles)
        return
