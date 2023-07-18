import string 
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
from time import time, strftime, gmtime
import logging
import shutil
from config import Config
from jvdb import manage_db
from datetime import datetime
from pytz import timezone
from psutil import virtual_memory, cpu_percent
from jvdrive import GdriveStatus, GoogleDriveHelper
from util import *
from jvripper import *
from logging.handlers import RotatingFileHandler
from expiringdict import ExpiringDict
from time import time
import random
#from uvloop import install
from urllib.parse import quote

# the logging things
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            "log.txt", maxBytes=50000000, backupCount=10
        ),
        logging.StreamHandler(),
    ],
)

log = logging.getLogger(__name__)


BLACKLISTED_EXTENSIONS = (".PY",".ENV", ".CPY", ".PYC", "YML", ".TXT", ".SH", "DOCKERFILE", "CACHE", "SESSION", "JOURNAL", "TOOLS", "CONFIGS", "__")
mydb = manage_db()
JVBot = Client("JVPaidBot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
USER_DATA = ExpiringDict(max_len=1000, max_age_seconds=60*60)
# Bot stats
BOT_UPSTATE = datetime.now(timezone('Asia/Kolkata')).strftime("%d/%m/%y %I:%M:%S %p")
BOT_START_TIME = time()

CHECK_ONCE = []
QUEUE = asyncio.Queue(5000)
task = False

async def is_subscribed(user_id):
    chkUser = await mydb.get_user(user_id)
    if user_id in Config.OWNER_ID:
        return True
    if chkUser:
        expiryDate = chkUser.get("expiry")
        balance = chkUser.get("balance")
        start_date = chkUser.get("start")
        #start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f") 
        now_date = datetime.now()
        if (now_date-start_date).days < expiryDate:
            if balance > 0:
                return True

async def filter_subscription(_, __, m):
    chkUser = await is_subscribed(m.from_user.id)
    if m.from_user.id in Config.OWNER_ID:
        return True
    if chkUser:
        return True
    await m.reply_text("You haven't subscribed yet, check using /plans\n\ncontact owner to get subscription")
    return False

static_auth_filter = filters.create(filter_subscription)

@JVBot.on_message(filters.command("sub") & filters.user(Config.OWNER_ID))
async def tg_subget_Handler(bot: JVBot, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = message.text.split(" ", 1)[1]
    msg_ = await get_subscription(user_id)
    await message.reply_text(msg_)


@JVBot.on_message(filters.command(["myplan"]))
async def tg_infoget_Handler(bot: JVBot, message: Message):
    user_id = message.from_user.id
    msg_ = await get_subscription(user_id)
    await message.reply_text(msg_)

async def get_subscription(user_id):
    if user_id in Config.OWNER_ID:
        return "No limit for this user, infinite downloads allowed"
    chkUser = await mydb.get_user(user_id)
    if chkUser:
        expiryDate = chkUser.get("expiry")
        balance = chkUser.get("balance")
        start_date = chkUser.get("start")
        #start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f") 
        now_date = datetime.now()
        msg = f"""**Subscription details:**
**user**: `{user_id}`
**videos**: `{balance}`
**expires**: {expiryDate - (now_date-start_date).days} days
Contact owner for updating subscription. """
    else:
        msg = "No Subscription found...\n\ncheck /plans to get your subscription now..."
    return msg

@JVBot.on_message(filters.command(["status", "stats"]) & static_auth_filter)
async def status_msg(bot, update):
  currentTime = strftime("%H:%M:%S", gmtime(time() - BOT_START_TIME)) 
  total, used, free = shutil.disk_usage(".")
  total, used, free = humanbytes(total), humanbytes(used), humanbytes(free)
  cpu_usage = cpu_percent()
  ram_usage = f"{humanbytes(virtual_memory().used)}/{humanbytes(virtual_memory().total)}"
  msg = f"**Bot Current Status**\n\n**Bot Uptime:** {currentTime} \n\n**Total disk space:** {total} \n**Used:** {used} \n**Free:** {free} \n**CPU Usage:** {cpu_usage}% \n**RAM Usage:** {ram_usage}\n**Restarted on** `{BOT_UPSTATE}`"
  await update.reply_text(msg, quote=True)


@JVBot.on_message(filters.command("auth") & filters.user(Config.OWNER_ID))
async def tg_auth_Handler(bot: JVBot, message: Message):
    if message.reply_to_message:
        _, balance, days = message.text.split(" ")
        expiryDate = int(days)
        balance = int(balance)
        from_user = message.reply_to_message.from_user
    else:
        try:
            _, user_id, balance, days = message.text.split(" ")
            from_user = await bot.get_users(int(user_id))
            expiryDate = int(days)
            balance = int(balance)
        except:
            return await message.reply_text("send along with proper format or reply to user msg")
    await mydb.set_user(from_user.id, expiryDate, balance)
    await message.reply_text(f"""**New User added**
**expiry**: {expiryDate} days
**Videos**: {balance} videos
User Details:
  user: {from_user.mention}
  id: `{from_user.id}`""")
    
@JVBot.on_message(filters.command("start"))
async def start_handler(bot: JVBot, message: Message):
    await message.reply_text(text=f"""Hello👋 {message.from_user.mention},

I am OTT Downloader Bot. I can help you to download content from OTT Platforms.

Check /plans to buy""")

@JVBot.on_message(filters.command("availableotts"))
async def otts(bot: JVBot, message: Message):
    await message.reply_text(text="""****Available Otts**

`• Zee5
• Hotstar(in the way)
• Netflix
• Prime Video 
• Lionsgate Play
• Erosnow
• Vrott`""")
    
@JVBot.on_message(filters.command("help"))
async def help(bot: JVBot, message: Message):
   await message.reply_text(text="""**Commands for PRIME_VIDEO/NETFLIX 👇**

[-q quality
-sl subtitles
-al audios spilt with 
-s season number
-e 1~ download all episodes
-vp {AVC,HEVC,HDR,DOLBY_VISION,VP9,UHD,CBR,CVBR,MAIN,HIGH}] 

**Ex:** 
[`/pv https://www.primevideo.com/detail/0SUJLFBDCKESPBD4G1HS131GTW -q 1080 -vp HEVC -al hi,en -sl en`]

[`/pv  https://www.primevideo.com/detail/0JV5DHR0ETGXOJNHQPD28DBI2T -s 1 -e 1~ -al hi,en -sl en -q 1080 -vp HEVC`]

Ex:
Movie:👇
[`/nf https://www.netflix.com/watch/80189685 -q 480 -vp MAIN -al all -sl eng -s 1 -e 1~`]

Series: 👇
[`/nf https://www.netflix.com/watch/81098494 -q 1080 -vp MAIN -al all -sl eng`]

[`/zee5 https://www.zee5.com/movies/details/vimanam/0-0-1z5387314`]

[`/zee5 https://www.zee5.com/web-series/details/mukhbir-the-story-of-a-spy/0-6-4z5199975:1:1-3`]
==> [`series_id:season_number:start_episode-end_episode`]

**Contact @tony_rd_jr for more!**""", disable_web_page_preview=True)
                       
                       
@JVBot.on_message(filters.command("plans"))
async def plans(bot: JVBot, message: Message):
    await message.reply_text(text='''DRM-DL BOT' s Plans
    
Plan Name - Starter 
Price - 799₹ [All Otts]
Drm Video Limit - Unlimited 
Validity - 38 Days 

Plan Name - Standard
Price - 599₹ [All otts]
Drm Video Limit - Unlimited
Validity - 28 Days

Payment Methods : 

INR - PhonePe, Paytm, Google Pay [UPI]
USD - PayPal,Crypto [Extra Charge]
BDT - BKash, Nagad [Extra Charge]

°°Term and Conditions°°

• Payments are non-refundable, and we do not provide refunds. 
• If the service ceases to function, no compensation is provided.

**Note - Don't Ask To Reduce Price..**

• Contact @Alex0512i To Buy Supcription!!''')
                       

async def upload_to_gdrive(bot, input_str, sts_msg):
    up_dir, up_name = input_str.rsplit('/', 1)
    gdrive = GoogleDriveHelper(up_name, up_dir, bot.loop, sts_msg)
    size = get_path_size(input_str)
    success = await sync_to_async(bot.loop, gdrive.upload, up_name, size)
    msg = sts_msg.reply_to_message if sts_msg.reply_to_message else sts_msg
    if success:
        url_path = quote(f'{up_name}')
        share_url = f'{Config.INDEX_LINK}/{url_path}'
        if success[3] == "Folder":
            share_url += '/'
        sent = await msg.reply_text(f"""**File Name:** `{success[4]}`
**Size:** `{humanbytes(success[1])}`
**Type:** `{success[3]}`
**Total Files:** `{success[2]}`

[Drive]({success[0]}) | [Index]({share_url})""",
                           disable_web_page_preview=True
          )
        await sent.copy(chat_id=Config.LOG_CHANNEL)
    else:
        await msg.reply_text("Upload failed to gdrive")



@JVBot.on_message(filters.command("unauth") & filters.user(Config.OWNER_ID))
async def tg_unauth_Handler(bot: JVBot, message: Message):
    if message.reply_to_message:
         user_id = message.reply_to_message.from_user.id
         from_user = message.reply_to_message.from_user
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
            from_user = await bot.get_users(int(user_id))
        except:
            return await message.reply_text("send along with I'd or reply to user msg")
    try:
        user_id = int(user_id)
    except:
        return await message.reply_text("send along with I'd or reply to user msg")
    await mydb.delete_user(user_id)
    await message.reply_text(f"Now {from_user.id} can not use me")

@JVBot.on_message(filters.command(["logs", "log"]) & filters.user(Config.OWNER_ID))
async def tg_unauth_Handler(bot: JVBot, message: Message):
    if os.path.exists("log.txt"):
        await message.reply_document("log.txt")
        return

@JVBot.on_message(filters.command(["rem", "remd"]) & static_auth_filter)
async def tg_unauth_Handler(bot: JVBot, message: Message):
    cmd, path = message.text.split(" ", 1)
    log.info("rem request from:", message.from_user.mention, "::", cmd, path)
    if cmd == "/rem":
        if path.startswith(str(message.from_user.id)) or message.from_user.id in Config.OWNER_ID:
            os.remove(path)
            await message.reply_text(f"Removed file {path}")
    else:
        if path.startswith(str(message.from_user.id)) or message.from_user.id in Config.OWNER_ID:
            shutil.rmtree(path)
            await message.reply_text(f"Removed dir {path}")


async def bg_worker():
    global QUEUE
    while True:
        if not QUEUE.empty():
            try:
                bot, msg = await QUEUE.get()
                await main_handler(bot, msg)
            except Exception as e:
                log.error(e)
                pass
            finally:
                QUEUE.task_done()
        await asyncio.sleep(1)

async def checkUserQueue(userId):
    global QUEUE
    i = 1
    for queue in QUEUE._queue:
        i += 1
        if queue[1].from_user.id == userId:
            return i
    return False

@JVBot.on_message(filters.command(["pv", "zee5", "nf"], prefixes=[".", "/", "#","~"]) & static_auth_filter)
async def queue_handler(bot, message):
    global task, QUEUE, CHECK_ONCE
    try:
        if message.from_user.id in Config.OWNER_ID:
            return await main_handler(bot, message)
        if len(QUEUE._queue) != 0:
            buttons = [[
                InlineKeyboardButton("Server Status 📊", callback_data="q_status"),
                InlineKeyboardButton("Cancel ⛔", callback_data="queue_cancel")
            ]]
        else:
            buttons = None
        if message.from_user.id in CHECK_ONCE:
            return await message.reply_text("Your a task already going on, so please wait....\n\nThis method was implemented to reduce the overload on bot. So please cooperate with us.")
        if not (await checkUserQueue(message.from_user.id)):
            await QUEUE.put_nowait((bot, message))
            CHECK_ONCE.append(message.from_user.id)
        else:
            await message.reply_text("You are already in queue**QUEUE**.\nThis method was implemented to reduce the overload on bot. So please cooperate with us.\n\n Press the following button to check the position in queue", reply_markup=InlineKeyboardMarkup(buttons))
    except asyncio.QueueFull:
        await message.reply_text("Queue Full 🥺\nPlease send task after few 2-5 minutes")
    except Exception as e:
        log.error(e, exc_info=True)
    else:
        if not task:
            for i in range(Config.MAX_WORKERS):
                asyncio.create_task(bg_worker())
        await asyncio.sleep(0.5)
        if buttons:
            await message.reply_text(text="Your Task added to **QUEUE**.\nThis method was implemented to reduce the overload on bot. So please cooperate with us.\n\n Press the following button to check the position in queue", reply_markup=InlineKeyboardMarkup(buttons))

@JVBot.on_callback_query(filters.regex("^q_status$"))
async def status_cb(c, m):
    exist = await checkUserQueue(m.from_user.id)
    if exist:
        await m.answer(f"Position in QUEUE: {exist}\nTotal Pending: {len(QUEUE._queue)}", show_alert=True)
    else:
        return await m.message.edit("Your Task was not exits on Queue 🤷‍♂️")


@JVBot.on_callback_query(filters.regex("^queue_cancel$"))
async def cancel_queue(c, m):
    for data in QUEUE._queue:
        if data[1].from_user.id == m.from_user.id:
            break
    else:
        return await m.message.edit("Your Task was already removed from queue")
    try:
        QUEUE._queue.remove(data)
        QUEUE._unfinished_tasks -= 1
        await m.message.edit("__Task Removed from queue Sucessfully 😊__")
    except Exception as e:
        print(e)
        await m.message.edit("Your task already removed from queue")

@JVBot.on_callback_query(filters.regex(pattern="^video"))
async def video_handler(bot: Client, query: CallbackQuery):
    global CHECK_ONCE
    _, key, video = query.data.split("#", 2)
    if query.from_user.id not in USER_DATA:
        await query.answer("You are not authorized to use this button.", show_alert=True)
        return
    check_user = await is_subscribed(query.from_user.id)
    if not check_user:
        await query.answer("You are not subscribed to use this bot.", show_alert=True)
        return
    if key not in USER_DATA[query.from_user.id]:
        await query.answer("Session expired, please try again.", show_alert=True)
        return 
    if key in USER_DATA[query.from_user.id]:
        if len(USER_DATA[query.from_user.id][key]["audios"]) == 0:
            await query.answer("No audio streams found, please try again.", show_alert=True)
            return
        drm_client = USER_DATA[query.from_user.id][key]
        if drm_client:
            list_audios = USER_DATA[query.from_user.id][key]["audios"]
            drm_client = USER_DATA[query.from_user.id][key]["client"]
            jvname = USER_DATA[query.from_user.id][key]["jvname"]
            file_pth = USER_DATA[query.from_user.id][key]["folder"]
            file_pth = os.path.join(Config.TEMP_DIR, file_pth)
            await query.message.edit("Please wait downloading in progress")
            rcode = await drm_client.downloader(video, list_audios, query.message)
            #await sts_.edit(f"Video downloaded in {file_pth}")
            try:
                await query.message.edit(f"Please wait starting **gdrive** upload of `{jvname}`")
                sts = query.message
            except:
                sts = await query.message.reply_text(f"Please wait starting **gdrive** upload of `{jvname}`")
            for fileP in os.listdir(file_pth):
                await upload_to_gdrive(bot, os.path.join(file_pth, fileP), sts)
            try:
                await sts.delete()
            except:
                await sts.delete()
            await mydb.set_user(user_id=query.from_user.id, balance = 0 - drm_client.COUNT_VIDEOS)
            if os.path.exists(file_pth):
                shutil.rmtree(file_pth)
            CHECK_ONCE.remove(msg.from_user.id)
            #await query.message.edit("Error occured, contact @Jigarvarma2005 for fixing.")
        else:
            await query.answer("Session expired, please try again.", show_alert=True)
            return

@JVBot.on_message(filters.command("js"))
async def js(bot, msg):
    await msg.reply_text(msg.reply_to_message)

@JVBot.on_callback_query(filters.regex(pattern="^audio"))
async def audio_handler(bot: Client, query: CallbackQuery):
    _, key, audio = query.data.split("#", 2)
    if query.from_user.id not in USER_DATA:
        await query.answer("You are not authorized to use this button.", show_alert=True)
        return
    if key not in USER_DATA[query.from_user.id]:
        await query.answer("Session expired, please try again.", show_alert=True)
        return 
    if audio=="process":
        if key in USER_DATA[query.from_user.id]:
            videos_q = await USER_DATA[query.from_user.id][key]["client"].get_videos_ids()
            markup = create_buttons(list([key]+videos_q), True)
            await query.edit_message_text("**Select video quality**", reply_markup=markup)
    else:
        audio, coice = audio.split("|", 1)
        if coice == "1":
            USER_DATA[query.from_user.id][key]["audios"].append(audio)
            markup = MakeCaptchaMarkup(query.message.reply_markup.inline_keyboard, query.data, f"{LANGUAGE_FULL_FORM.get(audio.lower(), audio)}✅")
        if coice == "0":
            USER_DATA[query.from_user.id][key]["audios"].remove(audio)
            markup = MakeCaptchaMarkup(query.message.reply_markup.inline_keyboard, query.data, f"{LANGUAGE_FULL_FORM.get(audio.lower(), audio)}")
        await query.message.edit_reply_markup(InlineKeyboardMarkup(markup))

async def drm_dl_client(bot, update, MpdUrl):
    user_fol = str(time())
    drm_client: Zee5 = Zee5(MpdUrl, user_fol)
    title = await drm_client.get_input_data()
    randStr = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 5))
    #passing the randStr to use it as a key for the USER_DATA dict
    user_choice_list = await drm_client.get_audios_ids(randStr)
    USER_DATA[update.from_user.id] = {}
    USER_DATA[update.from_user.id][randStr] = {}
    USER_DATA[update.from_user.id][randStr]["client"] = drm_client
    USER_DATA[update.from_user.id][randStr]["audios"] = []
    USER_DATA[update.from_user.id][randStr]["folder"] = user_fol
    USER_DATA[update.from_user.id][randStr]["jvname"] = title
    my_buttons = create_buttons(user_choice_list)
    await update.reply_text(f"{title}\n\n**Please select the audios to download**", reply_markup=my_buttons)
    return

async def main_handler(bot: JVBot, m: Message):
    global CHECK_ONCE
    command, user_iput = m.text.split(" ", 1)
    if "zee5" in user_iput or "zee5" in command:
        return await drm_dl_client(bot, m, user_iput)
    cmd = "python3.9 wvripper.py " + user_iput
    log.info("Dl request from:" + str(m.from_user.id) + "::" + cmd)
    Xfol = f"{m.from_user.id}t_{time()}"
    Xfol = os.path.join(Config.TEMP_DIR, Xfol)
    cmd += f" -o {Xfol}"
    a_sts = await m.reply_text("**Downloading ...**")
    err_res, t_res = await run_comman_d(cmd)
    log.info(err_res)
    filesCount = len(getListOfFiles(os.path.join(Xfol, "[OUTPUT]"), True))
    if filesCount >= 1:
        newXfol = f"{m.from_user.id}_o_{time()}"
        newXfol = os.path.join(Config.TEMP_DIR, newXfol)
        os.makedirs(newXfol)
        os.rename(os.path.join(Xfol, "[OUTPUT]"), newXfol)
        try:
            shutil.rmtree(Xfol)
        except Exception as e:
            log.exception(e)
    else:
        return await a_sts.edit("**Download Failed..., Try Again Later**")
    if not m.from_user.id in Config.OWNER_ID:
        # To make it negative
        videos = 0 - filesCount
        await mydb.set_user(user_id=m.from_user.id, balance=videos)
    log.info(f"Dl completed for {m.from_user.mention} :: {newXfol}")
    for file in os.listdir(newXfol):
        await upload_to_gdrive(bot, os.path.join(newXfol, file), a_sts)
    try:
        await a_sts.delete()
    except:
        await a_sts.delete()
    try:
        shutil.rmtree(newXfol)
    except Exception as e:
        log.error(e)
    CHECK_ONCE.remove(msg.from_user.id)

@JVBot.on_callback_query(filters.regex("^q_status$"))
async def status_cb(c, m):
    exist = await checkUserQueue(m.from_user.id)
    if exist:
        await m.answer(f"Position in QUEUE: {exist}\nTotal Pending: {len(QUEUE._queue)}", show_alert=True)
    else:
        return await m.message.edit("Your Task was not exits on Queue 🤷‍♂️")



@JVBot.on_callback_query(filters.regex("^queue_cancel$"))
async def cancel_queue(c, m):
    for data in QUEUE._queue:
        if data[1].from_user.id == m.from_user.id:
            break
    else:
        return await m.message.edit("Your Task was already removed from queue")
    try:
        QUEUE._queue.remove(data)
        QUEUE._unfinished_tasks -= 1
        await m.message.edit("__Task Removed from queue Sucessfully 😊__")
    except Exception as e:
        print(e)
        await m.message.edit("Your task already removed from queue")

        
#dict of commands of linux alies for windows
cmds = {"ls": "dir /B", "cd": "cd", "rm": "del", "mkdir": "mkdir", "mv": "move", "cp": "copy", "pwd": "cd", "cat": "type", "clear": "cls", "echo": "echo", "touch": "echo.>"}

@JVBot.on_message(filters.command(["s","shell","cmd"]) & filters.user(Config.OWNER_ID))
async def tg_s_Handler(bot: JVBot, message: Message):
    o_cmd = message.text.split(' ', 1)
    log.info(f"Shell request from {message.from_user.mention} :: {o_cmd}")
    sts = await message.reply_text("Please wait ....")
    if len(o_cmd) == 1:
        return await sts.edit('**Send a command to execute**')
    cmd = o_cmd[1]
    #cmd = ""
    #for i in o_cmd.split(" "):
    #    cmd += cmds.get(i, i) + " "
    cmd = cmd.strip()
    while cmd.endswith(" "):
        cmd = cmd[:-1]
    for check in cmd.split(" "):
        if check.upper().endswith(BLACKLISTED_EXTENSIONS):
            return await sts.edit("you can't execute this cmd")
    reply = ''
    stderr, stdout = await run_comman_d(cmd)
    newstdout = ""
    for line in stdout.split("\n"):
        if message.from_user.id in Config.OWNER_ID:
            newstdout += line + "\n"
            continue
        if not line.strip().upper().endswith(BLACKLISTED_EXTENSIONS):
            newstdout += line + "\n"
    if len(newstdout) != 0:
        reply += f"<b>Stdout</b>\n<code>{newstdout}</code>\n"
    if len(stderr) != 0:
        reply += f"<b>Stderr</b>\n<code>{stderr}</code>\n"
    if len(reply) > 3000:
        with open('output.txt', 'w') as file:
            file.write(reply)
        with open('output.txt', 'rb') as doc:
            await message.reply_document(
                document=doc,
                caption=f"`{cmd}`")
            await sts.delete()
    elif len(reply) != 0:
        await sts.edit(reply)
    else:
        await sts.edit('Executed')

async def StartBot():
    #install()
    print("--------@Jigarvarma2005--------")
    await JVBot.start()
    print("----------Bot Started----------")
    await idle()
    await JVBot.stop()
    print("----------Bot Stopped----------")
    print("--------------BYE!-------------")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(StartBot())
