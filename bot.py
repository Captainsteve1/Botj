from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os
from time import time, strftime, gmtime
import logging
import shutil
from config import Config
from jvdb import manage_db
from datetime import datetime
from pytz import timezone
from psutil import virtual_memory, cpu_percent
from jvdrive import upload_to_gdrive
from util import *
from logging.handlers import RotatingFileHandler
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
# Bot stats
BOT_UPSTATE = datetime.now(timezone('Asia/Kolkata')).strftime("%d/%m/%y %I:%M:%S %p")
BOT_START_TIME = time()
# i think we cant change the value in class
AUTH_USERS = Config.AUTH_USERS
async def auth_check(_, __, m):
    global AUTH_USERS
    return m.chat.id in AUTH_USERS

CHECK_ONCE = set()
QUEUE = asyncio.Queue(5000)
task = False

async def get_subscription(_, __, m):
    chkUser = await mydb.get_user(m.from_user.id)
    if m.from_user.id in Config.OWNER_ID:
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
    await m.reply_text("You haven't subscribed yet, check using /info\n\ncontact owner to get subscription")
    return False

static_auth_filter = filters.create(get_subscription)

@JVBot.on_message(filters.command("sub") & filters.user(Config.OWNER_ID))
async def tg_subget_Handler(bot: JVBot, message: Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = message.text.split(" ", 1)[1]
    msg_ = await get_subscription(user_id)
    await message.reply_text(msg_)


@JVBot.on_message(filters.command(["info", "plan"]))
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
        msg = "No Subscription found...\n\ncontact owner to get your subscription now..."
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

@JVBot.on_message(filters.command("gdrive") & static_auth_filter)
async def gdrive_Uploader_Handler(bot: JVBot, message: Message):
    try:
        input_str = message.text.split(" ", 1)[1]
        log.info("Gdrive UL request by " + str(message.from_user.id) + " for " + input_str)
        input_str = os.path.join(os.getcwd(), input_str)
    except:
        await message.reply_text("send along with file path")
        return
    await upload_to_gdrive(input_str, message)


@JVBot.on_message(filters.command("unauth") & filters.user(Config.OWNER_ID))
async def tg_unauth_Handler(bot: JVBot, message: Message):
    global AUTH_USERS
    if message.reply_to_message:
         user_id = message.reply_to_message.from_user.id
         from_user = message.reply_to_message.from_user
    else:
        try:
            user_id = message.text.split(" ", 1)[1]
            from_user = await bot.get_users(int(user_id))
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
    i = 1
    for queue in QUEUE._queue:
        i += 1
        if queue[1].from_user.id == userId:
            return i
    return False

@JVBot.on_message(filters.command(["nf", "amaz","dl","rip"], prefixes=[".", "/", "#","~"]) & static_auth_filter)
async def queue_handler(bot, message):
    global task
    try:
        if message.from_user.id in Config.OWNER_ID:
            return await main_handler(bot, message)
        if not (await checkUserQueue(message.from_user.id)):
            await QUEUE.put_nowait((bot, message))
        else:
            await message.reply_text("You are already in queue. Please wait for your turn")
    except asyncio.QueueFull:
        await message.reply_text("Queue Full 🥺\nPlease send task after few 2-5 minutes")
    except Exception as e:
        log.error(e)
    else:
        if not task:
            task = asyncio.create_task(bg_worker())
        await asyncio.sleep(0.5)
        if len(QUEUE._queue) != 0:
            buttons = [[
                InlineKeyboardButton("Server Status 📊", callback_data="q_status"),
                InlineKeyboardButton("Cancel ⛔", callback_data="queue_cancel")
            ]]
            await message.reply_text(text="Your Task added to **QUEUE**.\nThis method was implemented to reduce the overload on bot. So please cooperate with us.\n\n Press the following button to check the position in queue", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="markdown")

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

async def main_handler(bot: JVBot, m: Message):
    cmd = "python3.9 wvripper.py " + m.text.split(" ", 1)[1]
    log.info("Dl request from:", m.from_user.mention, "::", cmd)
    Xfol = f"{m.from_user.id}_temp_{time()}"
    cmd += f" -o {Xfol}"
    a_sts = await m.reply_text("**Downloading...**")
    err_res, t_res = await run_comman_d(cmd)
    log.info(err_res)
    filesCount = len(getListOfFiles(os.path.join(Xfol, "[OUTPUT]"), True))
    if filesCount >= 1:
        newXfol = f"{m.from_user.id}_output_{time()}"
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
    await a_sts.delete()
    for file in os.listdir(newXfol):
        await upload_to_gdrive(os.path.join(newXfol, file), m)
    try:
        shutil.rmtree(newXfol)
    except Exception as e:
        log.error(e)

#dict of commands of linux alies for windows
cmds = {"ls": "dir /B", "cd": "cd", "rm": "del", "mkdir": "mkdir", "mv": "move", "cp": "copy", "pwd": "cd", "cat": "type", "clear": "cls", "echo": "echo", "touch": "echo.>"}

@JVBot.on_message(filters.command(["s","shell","cmd"]) & filters.user(Config.OWNER_ID))
async def tg_s_Handler(bot: JVBot, message: Message):
    o_cmd = message.text.split(' ', 1)
    log.info(f"Shell request from {message.from_user.mention} :: {o_cmd}")
    sts = await message.reply_text("Please wait ....")
    if len(o_cmd) == 1:
        return await sts.edit('**Send a command to execute**')
    o_cmd = o_cmd[1]
    cmd = ""
    for i in o_cmd.split(" "):
        cmd += cmds.get(i, i) + " "
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
    print("--------@Jigarvarma2005--------")
    await JVBot.start()
    print("----------Bot Started----------")
    await idle()
    await JVBot.stop()
    print("----------Bot Stopped----------")
    print("--------------BYE!-------------")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(StartBot())
    