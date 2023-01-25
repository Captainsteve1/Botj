import asyncio
import logging
from pyrogram.types import Message
import re
import os
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

class JVPrimeDl:
    def __init__(self, cmd):
        self.cmd = cmd
        self.log = logging.getLogger("JVPrimeDl")
    
    async def download(self, message: Message):
        process = await asyncio.create_subprocess_shell(
            self.cmd,
            # stdout must a pipe to be accessible as process.stdout
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit = 1024 * 128 * 200)
        blank = 0
        count = 0
        flag = 0
        filename = ""
        ed = 0
        while True:
            try:
                data  = await process.stdout.readline()
                data = data.decode().strip().split("\r")[0].split("\n")[0]
            except:
                data = ""
            if data == "":
                blank += 1
            if blank == 30:
                break
            chk_dl = re.findall(r"Downloding: (.*)", data)
            if chk_dl:
                filename = chk_dl[0]
                continue
            if "WVripper took" in data:
                break
            if "Start Muxing" in data:
                flag = 1
                await message.edit("`Muxing Started ...`")
            if flag == 1:
                if data == "":
                    continue
                else:
                    await message.edit(data)
            if ed == 0:
                await message.edit("`Downloading Started ...`")
                ed = 1
            comp_ptrn = r".*((?:\d+\.)?\d+(?:B|KiB|MiB|GiB)).*/.*((?:\d+\.)?\d+(?:K|M|G)iB)?((?:\d+\.)?\d+\%)"
            comp_srch = re.search(comp_ptrn, data)
            if comp_srch is not None and int(comp_srch.groups()[-1].replace("%", "")) == 100:
                await message.edit(f"`{filename} Downloaded ....`")
            try:
                self.log.info(data)
                p_p = r"((?:\d+\.)?\d+\%)"
                t_p = r"((?:\d+\.)?\d+(?:K|M|G)iB)"
                try:
                    prog = re.search(p_p, data).group(1)
                    size = re.search(t_p, data).group(1)
                except:
                    continue
                try:
                    prg = prog.strip("% ")
                    prg = prg.replace("%", "")
                    pr_bar = ""
                    try:
                        percentage=int(prg.split(".")[0])
                    except Exception as e:
                        percentage = 0
                    for i in range(1,11):
                        if i <= int(percentage/10):
                            pr_bar += "●"
                    editstr = f"`✦ Downloading {filename} ...`\n\n`[{pr_bar}] {prog}%`\n\n`✦ Total {size}`"
                    count += 1
                    if count >= 5:
                        count = 0
                        await asyncio.sleep(3)
                        await message.edit(editstr)
                except Exception as e:
                    self.log.exception(e)
                    blank += 1
            except Exception as e:
                blank += 1
                self.log.exception(e)
                continue
        await process.wait()
        self.log.info(process.stderr.read().decode())
        await message.delete()

async def get_video_duration(input_file):
    metadata = extractMetadata(createParser(input_file))
    total_duration = 0
    if metadata.has("duration"):
        total_duration = metadata.get("duration").seconds
    return total_duration

def get_path_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = os.path.join(root, f)
            total_size += os.path.getsize(abs_path)
    return total_size

async def run_comman_d(command_list):
    process = await asyncio.create_subprocess_shell(
        command_list,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    return e_response, t_response

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T', 5: 'P', 6: 'E', 7: 'Z', 8: 'Y'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "day, ") if days else "") + \
        ((str(hours) + "hour, ") if hours else "") + \
        ((str(minutes) + "min, ") if minutes else "") + \
        ((str(seconds) + "sec, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]