import os
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant

# ==========================================================
# ⚙️ قسم المعلومات الكاملة (ضع بياناتك هنا)
# ==========================================================
API_ID = 30703866               # ايدي الـ API
API_HASH = "304c79f8ee0598f83984578bdcdc1b5f"      # هاش الـ API
BOT_TOKEN = "8631181450:AAEawLoYS1dHWC1k5xvmT_Opr_zifsHnmP8"    # توكن البوت من BotFather
ADMIN_ID = 5891747084            # آيديك الخاص (الأدمن)
CHANNEL_USER = "MyChannel"      # يوزر قناة الاشتراك الإجباري (بدون @)
# ==========================================================

app = Client("ExpertVideoBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 📊 نظام الإحصائيات (عدد المستخدمين) ---
def add_user(user_id):
    if not os.path.exists("all_users.txt"):
        with open("all_users.txt", "w") as f: pass
    with open("all_users.txt", "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open("all_users.txt", "a") as f:
            f.write(f"{user_id}\n")

def get_total_users():
    if not os.path.exists("all_users.txt"): return 0
    with open("all_users.txt", "r") as f:
        return len(f.readlines())

# --- 🔐 التحقق من الاشتراك (فوري ومفتوح) ---
async def is_subscribed(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USER, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True # لتجنب التوقف في حال تعطل صلاحيات البوت في القناة

# --- 🛠️ أوامر التحكم (الأدمن فقط) ---
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_cmd(_, message):
    count = get_total_users()
    await message.reply_text(f"📊 **إحصائيات البوت الحالية:**\n\n👥 عدد المستخدمين: `{count}`")

@app.on_message(filters.command("restart") & filters.user(ADMIN_ID))
async def restart_cmd(_, message):
    await message.reply_text("🔄 **جاري إعادة تشغيل النظام وتحديث الإضافات...**")
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- 🚀 نظام المعالجة الذكي (التحميل بدون تقطيع) ---
@app.on_message(filters.video | filters.document)
async def handle_video_delivery(client, message: Message):
    user_id = message.from_user.id
    add_user(user_id) # إضافة المستخدم للقاعدة

    # تحقق الاشتراك الإجباري
    if not await is_subscribed(client, user_id):
        return await message.reply_text(
            f"⚠️ **عذراً عزيزي، يجب عليك الاشتراك في القناة أولاً:**\n@{CHANNEL_USER}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إضغط هنا للاشتراك", url=f"t.me/{CHANNEL_USER}")]])
        )

    # إشعار البدء
    status = await message.reply_text("📥 **جاري تجهيز المقطع بأعلى جودة ذكية...**")

    try:
        # 📝 رسالتك الخاصة المطلوبة
        caption_text = (
            "اكتمل التحميل ✔️\n"
            "تم تجهيز الفيديو بأفضل جودة متاحة.\n"
            "أرسل الرابط التالي عند الطلب"
        )

        # التحميل الذكي (إرسال مباشر للحفاظ على الـ 60fps ومنع التقطيع)
        if message.video:
            await message.reply_video(message.video.file_id, caption=caption_text)
        else:
            await message.reply_document(message.document.file_id, caption=caption_text)
            
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ حدث خطأ أثناء المعالجة: `{e}`")

# --- أمر البداية ---
@app.on_message(filters.command("start"))
async def start_cmd(_, message):
    add_user(message.from_user.id)
    await message.reply_text(
        "👋 **أهلاً بك في بوت التحميل والمعالجة الذكية!**\n\n"
        "أرسل الفيديو وسأقوم بتسليمه لك بأعلى جودة وسلاسة ممكنة."
    )

print("✅ البوت يعمل الآن بكافة المعلومات والإضافات المصلحة...")
app.run()
