import codecs
import math
import os
import re
import unicodedata

import pysrt


class FixSubtitleTimeCodes:
    def __init__(self):
        """Merge_lines_with_same_time_codes"""
        self.added = set()

    def pysrt_to_dict(self, subs):
        sub_dict = list()
        for line in subs:
            start = str(line.start)
            end = str(line.end)
            text = line.text
            sub_dict.append(
                {"start": start, "end": end, "text": text,}
            )

        return sub_dict

    def merge_two_lines_text(self, l1, l2):
        text = l1["text"] + "\n" + l2["text"]
        start = l1["start"]
        end = l2["end"]
        line = {
            "start": start,
            "end": end,
            "text": text,
        }

        return line

    def merge_lines_with_same_time(self, subs: dict):
        added = set()
        sub_dict_merged = list()

        for n, subtitle in enumerate(subs):
            if str(subtitle["start"]) in added:
                continue
            for n2, subtitle2 in enumerate(subs):
                if n == n2:
                    continue
                if subtitle["start"] == subtitle2["start"] and subtitle["end"] == subtitle2["end"]:
                    subtitle["text"] = f"{subtitle['text']}\n{subtitle2['text']}"
            sub_dict_merged.append(subtitle)
            added.add(str(subtitle["start"]))

        # for i, line in enumerate(subs):
        #     if not line["start"] in added:
        #         try:
        #             next_line = subs[i + 1]
        #         except IndexError:
        #             sub_dict_merged.append(line)
        #             added.add(line["start"])
        #             continue  # last line

        #         if (
        #             line["start"] == next_line["start"]
        #             and line["end"] == next_line["end"]
        #         ):
        #             sub_dict_merged.append(self.merge_two_lines_text(line, next_line))
        #         else:
        #             sub_dict_merged.append(line)

        #         added.add(line["start"])

        return sub_dict_merged

    def save_subs(self, Out: str, subs: dict):
        file = codecs.open(Out, "w", encoding=self.encoding)
        for idx, text in enumerate(subs, start=1):
            file.write(
                "{}\n{} --> {}\n{}\n\n".format(
                    str(idx), text["start"], text["end"], text["text"].strip(),
                )
            )

        file.close()

        return

    def Merge(self, Input=None, Output=None, encoding="utf-8"):
        self.encoding = "utf-8"
        TEXT = pysrt.open(Input, encoding=self.encoding)
        TEXT = self.pysrt_to_dict(TEXT)
        TEXT = self.merge_lines_with_same_time(TEXT)
        self.save_subs(Output, TEXT)


class DFXPConverter:
    def __init__(self):
        self.__replace__ = "empty_line"

    def leading_zeros(self, value, digits=2):
        value = "000000" + str(value)
        return value[-digits:]

    def convert_time(self, raw_time):
        if int(raw_time) == 0:
            return "{}:{}:{},{}".format(0, 0, 0, 0)

        ms = "000"
        if len(raw_time) > 4:
            ms = self.leading_zeros(int(raw_time[:-4]) % 1000, 3)
        time_in_seconds = int(raw_time[:-7]) if len(raw_time) > 7 else 0
        second = self.leading_zeros(time_in_seconds % 60)
        minute = self.leading_zeros(int(math.floor(time_in_seconds / 60)) % 60)
        hour = self.leading_zeros(int(math.floor(time_in_seconds / 3600)))
        return "{}:{}:{},{}".format(hour, minute, second, ms)

    def xml_id_display_align_before(self, text):

        align_before_re = re.compile(
            u'<region.*tts:displayAlign="before".*xml:id="(.*)"/>'
        )
        has_align_before = re.search(align_before_re, text)
        if has_align_before:
            return has_align_before.group(1)
        return u""

    def xml_to_srt(self, text):
        def append_subs(start, end, prev_content, format_time):
            subs.append(
                {
                    "start_time": self.convert_time(start) if format_time else start,
                    "end_time": self.convert_time(end) if format_time else end,
                    "content": u"\n".join(prev_content),
                }
            )

        display_align_before = self.xml_id_display_align_before(text)
        begin_re = re.compile(u"\s*<p begin=")
        sub_lines = (l for l in text.split("\n") if re.search(begin_re, l))
        subs = []
        prev_time = {"start": 0, "end": 0}
        prev_content = []
        start = end = ""
        start_re = re.compile(u'begin\="([0-9:\.]*)')
        end_re = re.compile(u'end\="([0-9:\.]*)')
        content_re = re.compile(u'">(.*)</p>')

        # span tags are only used for italics, so we'll get rid of them
        # and replace them by <i> and </i>, which is the standard for .srt files
        span_start_re = re.compile(u'(<span style="[a-zA-Z0-9_.]+">)+')
        span_end_re = re.compile(u"(</span>)+")
        br_re = re.compile(u"(<br\s*\/?>)+")
        fmt_t = True
        for s in sub_lines:
            span_start_tags = re.search(span_start_re, s)
            if span_start_tags:
                s = u"<i>".join(s.split(span_start_tags.group()))
            string_region_re = (
                r'<p(.*region="' + display_align_before + r'".*")>(.*)</p>'
            )
            s = re.sub(string_region_re, r"<p\1>{\\an8}\2</p>", s)
            content = re.search(content_re, s).group(1)

            br_tags = re.search(br_re, content)
            if br_tags:
                content = u"\n".join(content.split(br_tags.group()))

            span_end_tags = re.search(span_end_re, content)
            if span_end_tags:
                content = u"</i>".join(content.split(span_end_tags.group()))

            prev_start = prev_time["start"]
            start = re.search(start_re, s).group(1)
            end = re.search(end_re, s).group(1)
            if len(start.split(":")) > 1:
                fmt_t = False
                start = start.replace(".", ",")
                end = end.replace(".", ",")
            if (prev_start == start and prev_time["end"] == end) or not prev_start:
                # Fix for multiple lines starting at the same time
                prev_time = {"start": start, "end": end}
                prev_content.append(content)
                continue
            append_subs(prev_time["start"], prev_time["end"], prev_content, fmt_t)
            prev_time = {"start": start, "end": end}
            prev_content = [content]
        append_subs(start, end, prev_content, fmt_t)

        lines = (
            u"{}\n{} --> {}\n{}\n".format(
                s + 1, subs[s]["start_time"], subs[s]["end_time"], subs[s]["content"]
            )
            for s in range(len(subs))
        )
        return u"\n".join(lines)

    def Convert(self, content):
        return self.xml_to_srt(content)


class SDHConverter:
    def __init__(self,):
        self.__replace__ = "empty_line"
        self.content = []

    def cleanLine(self, line, regex):
        line = re.sub("</i>", "", line)
        line = re.sub("<i>", "", line)
        if re.search(r"\[(.*)?\n(.*)?\]", line):
            line = re.sub(
                re.search(r"\[(.*)?\n(.*)?\]", line).group(), self.__replace__, line
            )

        if re.search(r"\((.*)?\n(.*)?\)", line):
            line = re.sub(
                re.search(r"\((.*)?\n(.*)?\)", line).group(), self.__replace__, line
            )

        try:
            # is it inside a markup tag?
            match = regex.match(line).group(1)
            tag = re.compile("(<[A-z]+[^>]*>)").match(match).group(1)
            line = re.sub(match, tag + self.__replace__, line)
        except:
            try:
                line = re.sub(regex, self.__replace__, line)
            except:
                pass
        return line

    def Save(self, Output):

        file = codecs.open(Output, "w", encoding=self.encoding)

        for idx, text in enumerate(self.content, start=1):
            file.write(
                "{}\n{} --> {}\n{}\n\n".format(
                    str(idx), text["start"], text["end"], text["text"].strip(),
                )
            )

        file.close()

    def Clean(self):
        if not self.content == []:
            temp = self.content
            self.content = []

            for text in temp:
                if text["text"].strip() == self.__replace__:
                    continue
                text.update({"text": re.sub(self.__replace__, "", text["text"])})

                if not text["text"].strip() == "":
                    self.content.append(text)

        return

    def Convert(self, Input=None, Output=None, content=None, encoding="utf-8"):

        self.encoding = encoding
        srt = pysrt.open(Input, encoding=self.encoding)

        for idx, line in enumerate(srt, start=1):
            number = str(idx)
            start = line.start
            end = line.end
            text = line.text

            try:
                text = self.cleanLine(text, re.compile(r"(\((.+): ?\)|\((.+): ?|^(.+): ?\))"))
                text = self.cleanLine(text, re.compile(r"(\((.+)?\)|\((.+)?|^(.+)?\))"))
                text = self.cleanLine(text, re.compile(r"(\[(.+)?\]|\[(.+)?|^(.+)?\])"))
                text = self.cleanLine(text, re.compile(r"([♩♪♫♭♮♯]+(.+)?[♩♪♫♭♮♯]+|[♩♪♫♭♮♯]+(.+)?|^(.+)?[♩♪♫♭♮♯]+)"))
                text = self.cleanLine(text, re.compile(r"(<font[^>]*>)|(<\/font>)"))
            except Exception:
                pass

            self.content.append(
                {"number": number, "start": start, "end": end, "text": text,}
            )

        self.Clean()
        self.Save(Output)

        return 


class WebVTT2Srt:
    def __init__(self):
        """Handle WEBVTT Subtitles"""

    def SimpleConverter(self, content):
        text = re.sub(r"WEBVTT", "", content)
        text = re.sub(re.compile(r"^(\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}).*", re.MULTILINE), r"\1", text)
        text = re.sub(r"{.*?}", "", text, flags=re.MULTILINE)
        text = re.sub(r"(.*\bposition:50.00%.*\bline:10.00%)\s*(.*)", r"\1\n{\\an8}\2", text, flags=re.MULTILINE)
        text = re.sub(r"&rlm;", "\u202B", text, flags=re.MULTILINE)
        text = re.sub(r"&lrm;", "\u202A", text, flags=re.MULTILINE)
        text = re.sub(r"&amp;", "&", text, flags=re.MULTILINE)
        text = re.sub(r"([\d]+)\.([\d]+)", r"\1,\2", text, flags=re.MULTILINE)
        text = re.sub(r"WEBVTT\n\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"NOTE.*\n", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n\s+\n", "", text, flags=re.MULTILINE)
        text = re.sub(r" position:.+%", "", text, flags=re.MULTILINE)
        text = re.sub(r"</?c.+?>", "", text, flags=re.MULTILINE)
        text = re.sub(r"NOTE+(..*)", "", text, flags=re.MULTILINE)
        text = re.sub(r"X-TIMESTAMP-MAP+(..*)", "", text, flags=re.MULTILINE)
        text = re.sub(r"</?[cv][^>]+>", "", text, flags=re.MULTILINE)
        text = re.sub(re.compile(r"^\s*$", re.MULTILINE), "", text)
        text = re.sub(r"&rlm;", "", text, flags=re.MULTILINE)
        text = re.sub(r"&gt;&gt; ", "", text, flags=re.MULTILINE)

        return text


class ReverseRtlStartEnd:
    def __init__(self):
        """Reverse RTL start/end"""

    def embed(self, text):
        text = re.sub('^', unicodedata.lookup('RIGHT-TO-LEFT EMBEDDING'), text, flags=re.MULTILINE) 

        return text

    def Reverse(self, Input: str, Output: str, encoding="utf-8"):
        subs = pysrt.open(Input, encoding=encoding)
        writer = codecs.open(Output, "w", encoding=encoding)

        for idx, line in enumerate(subs, start=1):
            start = str(line.start)
            end = str(line.end)
            text = self.embed(line.text)
            writer.write("{}\n{} --> {}\n{}\n\n".format(str(idx), start, end, text,))

        return text
