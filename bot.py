import os, asyncio, yt_dlp, re, json, time, sys
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

# --- [بيانات المطور] ---
api_id = 30703866 
api_hash = '304c79f8ee0598f83984578bdcdc1b5f' 
bot_token = '8631181450:AAEawLoYS1dHWC1k5xvmT_Opr_zifsHnmP8' 
ADMIN_ID = 5891747084 

client = TelegramClient('Hassan_Server_Session', api_id, api_hash).start(bot_token=bot_token)

# ملفات قاعدة البيانات
USERS_FILE = "users_list.txt"
CHANNELS_FILE = "channels_list.txt"
STATS_FILE = "stats_data.json"
HISTORY_FILE = "download_history.json"

admin_states = {}
pending_downloads = {}

# --- [دوال النظام] ---
def init_db():
    for f in [USERS_FILE, CHANNELS_FILE]:
        if not os.path.exists(f): open(f, "w").close()
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f: json.dump({"total": 0, "sites": {}, "peak_hours": {}}, f)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f: json.dump({}, f)

init_db()

def add_user(user_id):
    users = open(USERS_FILE, "r").read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f: f.write(f"{user_id}\n")

def update_stats(url):
    site = "Other"
    if "tiktok" in url: site = "TikTok"
    elif "instagram" in url: site = "Instagram"
    elif "youtube" in url or "youtu.be" in url: site = "YouTube"
    
    data = json.load(open(STATS_FILE))
    data["total"] += 1
    data["sites"][site] = data["sites"].get(site, 0) + 1
    hour = time.strftime("%H")
    data["peak_hours"][hour] = data["peak_hours"].get(hour, 0) + 1
    with open(STATS_FILE, "w") as f: json.dump(data, f)

def save_history(user_id, title, msg_media):
    data = json.load(open(HISTORY_FILE))
    user_h = data.get(str(user_id), [])
    user_h.insert(0, {"title": title, "media": str(msg_media)})
    data[str(user_id)] = user_h[:5]
    with open(HISTORY_FILE, "w") as f: json.dump(data, f)

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
    add_user(event.sender_id)
    not_sub = await check_sub(event.sender_id)
    if not_sub:
        return await event.respond(f"⚠️ اشترك بالقناة أولاً: @{not_sub}", buttons=[Button.url("اشتراك", f"https://t.me/{not_sub}")])
    
    await event.respond(f"✨ أهلاً بك في بوت التحميل المطور ✨\n\n📊 المستخدمين: {len(open(USERS_FILE).read().splitlines())}\n📂 لرؤية سجل تحميلاتك أرسل: /history", 
                        buttons=[[Button.url("📢 القناة", "https://t.me/ha_i_i9")], [Button.inline("⚙️ لوحة التحكم", data="admin_panel")] if event.sender_id == ADMIN_ID else []])

@client.on(events.NewMessage(pattern='/history'))
async def history(event):
    data = json.load(open(HISTORY_FILE)).get(str(event.sender_id), [])
    if not data: return await event.respond("📭 سجل التحميلات فارغ.")
    text = "📂 **آخر 5 فيديوهات حملتها:**\n\n"
    for i, item in enumerate(data): text += f"{i+1}. {item['title']}\n"
    await event.respond(text)

# --- [لوحة التحكم المعدلة] ---
@client.on(events.CallbackQuery(data="admin_panel"))
async def admin(event):
    if event.sender_id != ADMIN_ID: return
    st = json.load(open(STATS_FILE))
    top = max(st["sites"], key=st["sites"].get) if st["sites"] else "None"
    await event.edit(f"⚙️ **إحصائيات حسون:**\n\n📥 تحميلات: {st['total']}\n🌐 أكثر موقع: {top}\n👥 مستخدمين: {len(open(USERS_FILE).read().splitlines())}", 
                     buttons=[
                         [Button.inline("➕ إضافة قناة", data="add_ch"), Button.inline("📢 إذاعة", data="bc")],
                         [Button.inline("🔄 إعادة تشغيل البوت", data="restart_bot")],
                         [Button.inline("🗑 مسح القنوات", data="del_ch")]
                     ])

# --- [تنفيذ إعادة التشغيل] ---
@client.on(events.CallbackQuery(data="restart_bot"))
async def restart_bot(event):
    if event.sender_id != ADMIN_ID: return
    await event.edit("🔄 جاري إعادة تشغيل البوت... انتظر 5 ثواني.")
    await client.disconnect()
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.CallbackQuery(pattern=r"(add_ch|bc)"))
async def admin_input_req(event):
    admin_states[event.sender_id] = event.data.decode()
    await event.respond("📥 أرسل المطلوب الآن:")

@client.on(events.NewMessage(incoming=True))
async def handle_admin_input(event):
    if event.sender_id != ADMIN_ID or event.sender_id not in admin_states: return
    state = admin_states.pop(event.sender_id)
    if state == "add_ch":
        with open(CHANNELS_FILE, "a") as f: f.write(event.text.replace("@","") + "\n")
        await event.reply("✅ تمت إضافة القناة.")
    elif state == "bc":
        users = open(USERS_FILE).read().splitlines()
        await event.reply(f"⏳ جاري الإذاعة لـ {len(users)}...")
        for u in users:
            try: await client.send_message(int(u), event.text); await asyncio.sleep(0.1)
            except: continue
        await event.reply("✅ تمت الإذاعة.")

# --- [التحميل] ---
@client.on(events.NewMessage(pattern=r'(https?://\S+)'))
async def handler(event):
    if await check_sub(event.sender_id): return await event.reply("⚠️ اشترك بالقناة أولاً.")
    pending_downloads[event.sender_id] = event.text
    buttons = [[Button.inline("🎬 فيديو", data=f"v_{event.sender_id}"), Button.inline("🎵 MP3", data=f"a_{event.sender_id}")],
               [Button.inline("🎤 بصمة صوتية", data=f"n_{event.sender_id}")]]
    await event.reply("🚀 اختر الصيغة:", buttons=buttons)

@client.on(events.CallbackQuery(pattern=r"(v|a|n)_(\d+)"))
async def download(event):
    mode, uid = event.data.decode().split('_')
    if event.sender_id != int(uid): return
    url = pending_downloads.get(int(uid))
    if not url: return await event.edit("⚠️ انتهى الوقت.")
    
    await event.edit("⏳ جاري التحميل... انتظر قليلاً")
    
    opts = {'format': 'bestaudio/best' if mode in ['a', 'n'] else 'best', 'outtmpl': f'dl_{uid}.%(ext)s', 'quiet': True}
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Video')
            
            caption = "اكتمل التحميل ✔️\nتم تجهيز الفيديو بأفضل جودة متاحة.\nأرسل الرابط التالي عند الطلب"
            
            # إرسال حسب النوع
            msg = await client.send_file(event.chat_id, filename, caption=caption, voice_note=(mode=='n'))
            
            update_stats(url)
            save_history(uid, title, msg.media)
    except Exception as e: await event.respond(f"❌ خطأ: {str(e)[:100]}")
    finally:
        if filename and os.path.exists(filename): os.remove(filename)

print("✅ البوت شغال يا حسون مع ميزة إعادة التشغيل...")
client.run_until_disconnected()
