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
CHANNELS_FILE = "channels_list.txt"
USERS_FILE = "users_list.txt"
STATS_FILE = "stats_data.json"

admin_states = {} # لحفظ حالة الأدمن (انتظار المعرف) بدون وقت
pending_urls = {} # لحفظ الرابط للمستخدم لغرض التحويل

# --- [دوال النظام] ---
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
    if not os.path.exists(CHANNELS_FILE): return None
    channels = open(CHANNELS_FILE, "r").read().splitlines()
    for ch in channels:
        try:
            await client(GetParticipantRequest(channel=ch, user_id=user_id))
        except UserNotParticipantError: return ch
        except: continue
    return None

# --- [رسالة الترحيب] ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    add_user(event.sender_id)
    not_sub = await check_sub(event.sender_id)
    if not_sub:
        return await event.respond(f"⚠️ عزيزي، عليك الاشتراك في القناة أولاً: @{not_sub}", 
                                 buttons=[Button.url("اضغط هنا للاشتراك", f"https://t.me/{not_sub}")])
    
    welcome_text = (f"✨ أهلاً بك حسـ𝑯᭄ـون ✨\n\n"
                   f"أرسل الرابط الآن للتحميل بأعلى دقة وسلاسة 🚀\n"
                   f"تيك توك، انستا، يوتيوب.. كله مدعوم!\n"
                   f"━━━━━━━━\n"
                   f"📊 المستخدمين: {len(open(USERS_FILE).read().splitlines())}")
    
    buttons = [[Button.url("📢 قناة المطور", "https://t.me/ha_i_i9")]]
    if event.sender_id == ADMIN_ID:
        buttons.append([Button.inline("⚙️ لوحة التحكم", data="admin_panel")])
    
    await event.respond(welcome_text, buttons=buttons)

# --- [لوحة التحكم المعدلة] ---
@client.on(events.CallbackQuery(data="admin_panel"))
async def admin(event):
    if event.sender_id != ADMIN_ID: return
    st = json.load(open(STATS_FILE))
    await event.edit(f"⚙️ **لوحة التحكم:**\n\n📥 تحميلات: {st.get('total', 0)}\n👥 مستخدمين: {len(open(USERS_FILE).read().splitlines())}", 
                     buttons=[
                         [Button.inline("➕ إضافة قناة", data="add_ch_mode")],
                         [Button.inline("📢 إذاعة", data="bc_mode")],
                         [Button.inline("🔄 إعادة تشغيل", data="restart_bot")]
                     ])

@client.on(events.CallbackQuery(data="restart_bot"))
async def restart_bot(event):
    if event.sender_id != ADMIN_ID: return
    await event.edit("🔄 جاري إعادة تشغيل البوت... انتظر 5 ثواني.")
    await client.disconnect()
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.CallbackQuery(pattern=r"(add_ch_mode|bc_mode)"))
async def admin_input_req(event):
    mode = event.data.decode()
    admin_states[event.sender_id] = mode
    msg = "📥 أرسل الآن معرف القناة (مثال: @username):" if mode == "add_ch_mode" else "📢 أرسل نص الإذاعة:"
    await event.respond(msg)
    await event.answer()

@client.on(events.NewMessage(incoming=True))
async def handle_admin_input(event):
    # تم حذف نظام الوقت - البوت ينتظر للأبد حتى ترسل المعرف
    if event.sender_id != ADMIN_ID or event.sender_id not in admin_states: return
    
    state = admin_states.pop(event.sender_id)
    if state == "add_ch_mode":
        with open(CHANNELS_FILE, "a") as f: f.write(event.text.replace("@","").strip() + "\n")
        await event.reply(f"✅ تمت إضافة القناة {event.text} بنجاح!")
    elif state == "bc_mode":
        users = open(USERS_FILE).read().splitlines()
        await event.reply(f"⏳ جاري الإذاعة لـ {len(users)}...")
        for u in users:
            try: await client.send_message(int(u), event.text); await asyncio.sleep(0.1)
            except: continue
        await event.reply("✅ اكتملت الإذاعة.")

# --- [نظام التحميل والتحويل الذكي] ---
@client.on(events.NewMessage(pattern=r'(https?://\S+)'))
async def handler(event):
    if await check_sub(event.sender_id): return
    
    pending_urls[event.sender_id] = event.text.strip()
    buttons = [[Button.inline("🎬 مقطع مرئي", data=f"dl_v_{event.sender_id}"), 
                Button.inline("🎵 صوتي MP3", data=f"dl_a_{event.sender_id}")]]
    await event.reply("🚀 اختر الصيغة المطلوبة للتحميل:", buttons=buttons)

@client.on(events.CallbackQuery(pattern=r"dl_(v|a)_(\d+)"))
async def process_download(event):
    mode, uid = event.data.decode().split('_')[1], int(event.data.decode().split('_')[2])
    if event.sender_id != uid: return
    
    url = pending_urls.get(uid)
    await event.edit("⏳ جاري التحميل... انتظر قليلاً")
    
    opts = {'format': 'bestaudio/best' if mode == 'a' else 'best', 'outtmpl': f'h_{uid}.%(ext)s', 'quiet': True}
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # الكليشة الموحدة
            caption = ("اكتمل التحميل ✔️\n"
                      "تم تجهيز الفيديو بأفضل جودة متاحة.\n"
                      "أرسل الرابط التالي عند الطلب")
            
            await client.send_file(event.chat_id, filename, caption=caption)
            
            # تحديث الإحصائيات
            st = json.load(open(STATS_FILE)); st["total"] = st.get("total", 0) + 1
            with open(STATS_FILE, "w") as f: json.dump(st, f)

            # عرض خيار التحويل للصيغة الأخرى
            next_txt = "ملف صوتي 🎵" if mode == 'v' else "مقطع مرئي 🎬"
            next_data = f"dl_a_{uid}" if mode == 'v' else f"dl_v_{uid}"
            await event.respond(f"✅ هل تود تحويل نفس الرابط إلى {next_txt} أيضاً؟", 
                               buttons=[Button.inline("نعم، حمل الآن", data=next_data)])

    except Exception as e:
        await event.respond(f"❌ خطأ: {str(e)[:50]}")
    finally:
        if filename and os.path.exists(filename): os.remove(filename)

print("✅ البوت شغال يا حسون بآخر تحديث...")
client.run_until_disconnected()
