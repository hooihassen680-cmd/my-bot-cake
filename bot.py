import os, asyncio, yt_dlp, re, json, time, sys
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

# --- [بيانات المطور - تأكد من صحتها] ---
api_id = 30703866 
api_hash = '304c79f8ee0598f83984578bdcdc1b5f' 
bot_token = '8631181450:AAEawLoYS1dHWC1k5xvmT_Opr_zifsHnmP8' 
ADMIN_ID = 5891747084 

client = TelegramClient('Hassan_Pro_Session', api_id, api_hash).start(bot_token=bot_token)

# ملفات قاعدة البيانات
CHANNELS_FILE = "channels_list.txt"
USERS_FILE = "users_list.txt"
STATS_FILE = "stats_data.json"

admin_states = {}

# --- [دوال النظام] ---
def init_db():
    for f in [USERS_FILE, CHANNELS_FILE]:
        if not os.path.exists(f): open(f, "w").close()
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f: json.dump({"total": 0}, f)

init_db()

async def check_sub(user_id):
    if not os.path.exists(CHANNELS_FILE): return None
    channels = open(CHANNELS_FILE, "r").read().splitlines()
    for ch in channels:
        try:
            await client(GetParticipantRequest(channel=ch, user_id=user_id))
        except UserNotParticipantError: return ch
        except: continue
    return None

# --- [رسالة الترحيب المدمجة - خانة واحدة] ---
@client.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    user_id = event.sender_id
    users = open(USERS_FILE, "r").read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f: f.write(f"{user_id}\n")
    
    user_name = event.sender.first_name
    count = len(open(USERS_FILE).read().splitlines())
    
    # رسالة ترحيب مدمجة مع عدد المستخدمين في رسالة واحدة
    welcome_msg = (
        f"✨ أهلاً بك {user_name}\n\n"
        f"أرسل الرابط الآن للتحميل بأعلى دقة وسلاسة 🚀\n"
        f"تيك توك، انستا، يوتيوب.. كله مدعوم!\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 المستخدمين: {count}"
    )
    
    buttons = [[Button.url("📢 قناة المطور", "https://t.me/ha_i_i9")]]
    
    if user_id == ADMIN_ID:
        buttons.append([Button.inline("⚙️ لوحة التحكم", data="admin_panel")])
    
    await event.respond(welcome_msg, buttons=buttons)

# --- [لوحة التحكم] ---
@client.on(events.CallbackQuery(data="admin_panel"))
async def admin(event):
    if event.sender_id != ADMIN_ID: return
    st = json.load(open(STATS_FILE))
    count = len(open(USERS_FILE).read().splitlines())
    await event.edit(
        f"⚙️ **لوحة التحكم للمطور حسون:**\n\n"
        f"📥 إجمالي التحميلات: {st.get('total', 0)}\n"
        f"👥 مستخدمين البوت: {count}", 
        buttons=[
            [Button.inline("➕ إضافة قناة", data="add_ch_mode")],
            [Button.inline("🔄 إعادة تشغيل البوت", data="restart_bot")]
        ]
    )

@client.on(events.CallbackQuery(data="add_ch_mode"))
async def start_add(event):
    admin_states[event.sender_id] = "waiting_channel"
    await event.respond("📥 أرسل الآن معرف القناة (سيتم الانتظار للأبد حتى ترسلها):")
    await event.answer()

@client.on(events.CallbackQuery(data="restart_bot"))
async def restart_bot(event):
    await event.edit("🔄 جاري إعادة التشغيل وتطبيق تحديثات الجودة...")
    await client.disconnect()
    os.execl(sys.executable, sys.executable, *sys.argv)

@client.on(events.NewMessage(incoming=True))
async def handle_admin_input(event):
    # ميزة الانتظار المفتوح بدون وقت (No Timeout)
    if event.sender_id == ADMIN_ID and admin_states.get(event.sender_id) == "waiting_channel":
        ch = event.text.replace("@", "").strip()
        with open(CHANNELS_FILE, "a") as f: f.write(f"{ch}\n")
        del admin_states[event.sender_id]
        await event.reply(f"✅ تمت إضافة القناة @{ch} بنجاح!")

# --- [نظام التحميل الفائق الجودة 4K/HD] ---
@client.on(events.NewMessage(pattern=r'(https?://\S+)'))
async def high_quality_download(event):
    not_sub = await check_sub(event.sender_id)
    if not_sub: return await event.reply(f"⚠️ اشترك أولاً في قناة البوت: @{not_sub}")

    url = event.text.strip()
    msg = await event.reply("⏳ جاري سحب المقطع بأعلى دقة متوفرة (4K/HD)...")
    
    # إعدادات الجودة القصوى
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # جلب أعلى جودة فيديو + أعلى جودة صوت
        'outtmpl': f'hassan_4k_{event.sender_id}.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4', # الدمج بصيغة mp4 لضمان الجودة
    }
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # الكليشة الموحدة
            caption = (
                "اكتمل التحميل ✔️\n"
                "تم تجهيز الفيديو بأفضل جودة متاحة.\n"
                "أرسل الرابط التالي عند الطلب"
            )
            
            # إرسال الملف مع دعم البث لضمان عدم ضغط الجودة من تلجرام
            await client.send_file(
                event.chat_id, 
                filename, 
                caption=caption, 
                reply_to=event.id,
                supports_streaming=True
            )
            await msg.delete()
            
            # تحديث الإحصائيات
            st = json.load(open(STATS_FILE))
            st["total"] = st.get("total", 0) + 1
            with open(STATS_FILE, "w") as f: json.dump(st, f)
            
    except Exception as e:
        await msg.edit(f"❌ حدث خطأ أثناء محاولة المعالجة.")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

print("🚀 البوت يعمل الآن بأقصى دقة تحميل (4K) يا حسون!")
client.run_until_disconnected()
