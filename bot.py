import os, asyncio, yt_dlp, re, json, time, sys
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

# --- [بيانات المطور - عدلها إذا تغيرت] ---
api_id = 30703866 
api_hash = '304c79f8ee0598f83984578bdcdc1b5f' 
bot_token = '8631181450:AAEawLoYS1dHWC1k5xvmT_Opr_zifsHnmP8' 
ADMIN_ID = 5891747084 

client = TelegramClient('Hassan_Server_Session', api_id, api_hash).start(bot_token=bot_token)

# ملفات قاعدة البيانات
USERS_FILE = "users_list.txt"
CHANNELS_FILE = "channels_list.txt"
STATS_FILE = "stats_data.json"

admin_states = {}
pending_urls = {}

# --- [دوال النظام وقاعدة البيانات] ---
def init_db():
    for f in [USERS_FILE, CHANNELS_FILE]:
        if not os.path.exists(f): open(f, "w").close()
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f: json.dump({"total": 0}, f)

init_db()

def add_user(user_id):
    users = open(USERS_FILE, "r").read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f: f.write(f"{user_id}\n")

async def check_sub(user_id):
    channels = open(CHANNELS_FILE, "r").read().splitlines()
    for ch in channels:
        try:
            await client(GetParticipantRequest(channel=ch, user_id=user_id))
        except UserNotParticipantError: return ch
        except: continue
    return None

# --- [الأوامر الرئيسية] ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    add_user(user_id)
    
    # فحص الاشتراك الإجباري
    not_sub = await check_sub(user_id)
    if not_sub:
        return await event.respond(
            f"⚠️ عذراً عزيزي، عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه.\n\n📍 القناة: @{not_sub}", 
            buttons=[Button.url("اضغط هنا للاشتراك", f"https://t.me/{not_sub}")]
        )

    welcome_text = (
        f"✨ أهلاً بك في بوت التحميل المطور ✨\n\n"
        f"📊 مستخدمي البوت الآن: {len(open(USERS_FILE).read().splitlines())}\n"
        f"━━━━━━━━\n"
        f"👑 المطور: حسـ𝑯᭄ـون"
    )
    
    buttons = [[Button.url("📢 قناة المطور", "https://t.me/ha_i_i9")]]
    if user_id == ADMIN_ID:
        buttons.append([Button.inline("⚙️ لوحة التحكم", data="admin_panel")])
    
    await event.respond(welcome_text, buttons=buttons)

# --- [لوحة التحكم للمطور] ---
@client.on(events.CallbackQuery(data="admin_panel"))
async def admin(event):
    if event.sender_id != ADMIN_ID: return
    st = json.load(open(STATS_FILE))
    count = len(open(USERS_FILE).read().splitlines())
    await event.edit(
        f"⚙️ **لوحة التحكم (المطور حسون):**\n\n"
        f"👥 عدد المستخدمين: {count}\n"
        f"📥 إجمالي التحميلات: {st.get('total', 0)}\n"
        f"📢 القنوات المضافة: {len(open(CHANNELS_FILE).read().splitlines())}", 
        buttons=[
            [Button.inline("➕ إضافة قناة", data="add_ch"), Button.inline("📢 إذاعة", data="bc")],
            [Button.inline("🔄 إعادة تشغيل البوت", data="restart_bot")],
            [Button.inline("🗑 مسح القنوات", data="del_ch")]
        ]
    )

@client.on(events.CallbackQuery(data="restart_bot"))
async def restart_bot(event):
    if event.sender_id != ADMIN_ID: return
    await event.edit("🔄 جاري إعادة تشغيل البوت... انتظر 5 ثواني.")
    await client.disconnect()
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.CallbackQuery(pattern=r"(add_ch|bc)"))
async def admin_input_req(event):
    if event.sender_id != ADMIN_ID: return
    mode = event.data.decode()
    admin_states[event.sender_id] = mode
    msg = "📥 أرسل الآن معرف القناة (مثال: @username):" if mode == "add_ch" else "📢 أرسل نص الإذاعة الآن:"
    await event.respond(msg)
    await event.answer()

@client.on(events.NewMessage(incoming=True))
async def handle_admin_input(event):
    # معالج الإضافة والإذاعة بدون وقت انتهاء
    user_id = event.sender_id
    if user_id != ADMIN_ID or user_id not in admin_states: return
    
    state = admin_states.pop(user_id)
    if state == "add_ch":
        channel = event.text.replace("@", "").strip()
        with open(CHANNELS_FILE, "a") as f: f.write(f"{channel}\n")
        await event.reply(f"✅ تمت إضافة القناة @{channel} بنجاح!")
    
    elif state == "bc":
        users = open(USERS_FILE).read().splitlines()
        await event.reply(f"⏳ جاري الإذاعة لـ {len(users)} مستخدم...")
        success = 0
        for u in users:
            try:
                await client.send_message(int(u), event.text)
                success += 1
                await asyncio.sleep(0.1)
            except: continue
        await event.reply(f"✅ اكتملت الإذاعة بنجاح لـ {success} مستخدم.")

# --- [نظام التحويل والتحميل] ---
@client.on(events.NewMessage(pattern=r'(https?://\S+)'))
async def handler(event):
    if await check_sub(event.sender_id):
        return # لا يستجيب إذا لم يشترك
    
    url = event.text.strip()
    pending_urls[event.sender_id] = url
    
    buttons = [
        [Button.inline("🎬 مقطع فيديو", data=f"ask_v_{event.sender_id}"), 
         Button.inline("🎵 صوتي MP3", data=f"ask_a_{event.sender_id}")]
    ]
    await event.reply("🤔 اختر الصيغة المطلوبة للتحميل:", buttons=buttons)

@client.on(events.CallbackQuery(pattern=r"ask_(v|a)_(\d+)"))
async def ask_convert(event):
    data = event.data.decode().split('_')
    mode, uid = data[1], int(data[2])
    if event.sender_id != uid: return
    
    if mode == 'v':
        text = "🎬 اخترت تحميل فيديو، هل تود تحويله إلى صوتي أيضاً؟"
        btns = [[Button.inline("نعم، حوله لصوت", data=f"dl_a_{uid}"), 
                 Button.inline("لا، فيديو فقط", data=f"dl_v_{uid}")]]
    else:
        text = "🎵 اخترت تحميل صوتي، هل تود تحويله إلى مقطع فيديو؟"
        btns = [[Button.inline("نعم، حوله لفيديو", data=f"dl_v_{uid}"), 
                 Button.inline("لا، صوتي فقط", data=f"dl_a_{uid}")]]
    
    await event.edit(text, buttons=btns)

@client.on(events.CallbackQuery(pattern=r"dl_(v|a)_(\d+)"))
async def start_dl(event):
    data = event.data.decode().split('_')
    mode, uid = data[1], int(data[2])
    url = pending_urls.get(uid)
    if not url: return await event.edit("⚠️ انتهت الجلسة، أرسل الرابط مجدداً.")
    
    await event.edit("⏳ جاري المعالجة والتحميل... انتظر قليلاً")
    
    # إعدادات التحميل
    opts = {
        'format': 'bestaudio/best' if mode == 'a' else 'best',
        'outtmpl': f'hassan_{uid}.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # الكليشة الموحدة التي طلبتها
            caption = (
                f"اكتمل التحميل ✔️\n"
                f"تم تجهيز الفيديو بأفضل جودة متاحة.\n"
                f"أرسل الرابط التالي عند الطلب"
            )
            
            await client.send_file(event.chat_id, filename, caption=caption)
            
            # تحديث إحصائيات التحميل
            st = json.load(open(STATS_FILE))
            st["total"] = st.get("total", 0) + 1
            with open(STATS_FILE, "w") as f: json.dump(st, f)
            
    except Exception as e:
        await event.respond(f"❌ فشل التحميل. تأكد من أن الرابط مدعوم.\n{str(e)[:50]}")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

print("✅ البوت شغال الآن بجميع التعديلات المطلوبة يا حسون!")
client.run_until_disconnected()
