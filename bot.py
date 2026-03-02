import os, asyncio, yt_dlp
from telethon import TelegramClient, events, Button

# --- [بيانات المطور حسون] ---
api_id = 30703866 
api_hash = '304c79f8ee0598f83984578bdcdc1b5f' 
bot_token = '8631181450:AAEawLoYS1dHWC1k5xvmT_Opr_zifsHnmP8' 
ADMIN_ID = 5891747084 

client = TelegramClient('Hassan_Server_Session', api_id, api_hash).start(bot_token=bot_token)

# ملف حفظ المستخدمين (قاعدة بيانات بسيطة للسيرفر)
USERS_FILE = "users_list.txt"

def add_user(user_id):
    if not os.path.exists(USERS_FILE): open(USERS_FILE, "w").close()
    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

def get_users_count():
    if not os.path.exists(USERS_FILE): return 0
    with open(USERS_FILE, "r") as f:
        return len(f.read().splitlines())

# --- [رسالة الترحيب] ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    add_user(event.sender_id) # تسجيل المستخدم الجديد
    
    welcome_text = f"""✨ أهلاً بك في بوت التحميل ✨
يدعم: TikTok • Instagram • Facebook • YouTube
📎 أرسل الرابط فقط وسيتم التحميل فوراً.
━━━━━━━━
👑 المطور: حسـ𝑯᭄ـون 𝓱𝓪𝓼𝓼𝓸𝓷
📊 مستخدمي البوت الآن: {get_users_count()}
━━━━━━━━"""
    
    buttons = [[Button.url("📢 قناة المطور", "https://t.me/ha_i_i9")]]
    if event.sender_id == ADMIN_ID:
        buttons.insert(0, [Button.inline("⚙️ لوحة التحكم", data="admin_panel")])
    
    await event.respond(welcome_text, buttons=buttons)

# --- [معالج التحميل المقطع - دقة عالية] ---
@client.on(events.NewMessage(pattern=r'(https?://\S+)'))
async def download_handler(event):
    url = event.text
    process_msg = await event.reply("⏳ جاري سحب المقطع بأعلى دقة... انتظر ثواني")
    
    ydl_opts = {
        'format': 'best', # أعلى دقة
        'outtmpl': 'video_%(id)s.%(ext)s',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        caption = "✅ تم التحميل بنجاح!\n🎬 تم تحميله بواسطة بوت تحميل مقاطع تلجرام انستغرام\n\nهاك ورده كملت كيكه مالتك 🌹🍰"
        
        await client.send_file(event.chat_id, filename, caption=caption, reply_to=event.id)
        
        if os.path.exists(filename): os.remove(filename)
        await process_msg.delete()

    except Exception as e:
        await process_msg.edit(f"❌ فشل التحميل. تأكد من الرابط.\n{str(e)}")

# --- [لوحة التحكم للمطور] ---
@client.on(events.CallbackQuery(data="admin_panel"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    count = get_users_count()
    await event.edit(f"⚙️ **لوحة التحكم (المطور حسون):**\n\n👥 عدد المستخدمين: {count}", buttons=[
        [Button.inline("➕ إضافة قناة", data="add_channel")],
        [Button.inline("📢 إذاعة للمستخدمين", data="broadcast")]
    ])

print("✅ البوت جاهز للرفع على السيرفر المجاني 24 ساعة...")
client.run_until_disconnected()
