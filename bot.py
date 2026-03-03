import os
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant

# --- الإعدادات (ضع بياناتك هنا) ---
API_ID = 1234567           
API_HASH = "your_hash"      
BOT_TOKEN = "your_token"    
ADMIN_ID = 12345678        # آيديك لتتمكن من رؤية الإحصائيات
CHANNEL_USER = "MyChannel"  # يوزر قناتك بدون @

app = Client("SmartQualityBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- نظام إدارة المستخدمين (Stats) ---
def add_user(user_id):
    users = set()
    if os.path.exists("users_list.txt"):
        with open("users_list.txt", "r") as f:
            users = set(line.strip() for line in f)
    if str(user_id) not in users:
        with open("users_list.txt", "a") as f:
            f.write(f"{user_id}\n")

def count_users():
    if not os.path.exists("users_list.txt"): return 0
    with open("users_list.txt", "r") as f:
        return len(f.readlines())

# --- التحقق من الاشتراك الإجباري (فوري وبدون قيود) ---
async def check_sub(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USER, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True # يعمل تلقائياً إذا واجه البوت مشكلة في الصلاحيات

# --- أوامر الأدمن ---
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def show_stats(_, message):
    count = count_users()
    await message.reply_text(f"📊 **عدد مستخدمي البot الحقيقي:** `{count}`")

@app.on_message(filters.command("restart") & filters.user(ADMIN_ID))
async def reboot(_, message):
    await message.reply_text("🔄 جاري إعادة التشغيل الفوري...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- نظام الإرسال الذكي (بدون تعديل لمنع التقطيع) ---
@app.on_message(filters.video | filters.document)
async def smart_delivery(client, message: Message):
    user_id = message.from_user.id
    add_user(user_id)

    # التحقق من القناة
    if not await check_sub(client, user_id):
        return await message.reply_text(
            f"⚠️ **يجب عليك الاشتراك في القناة أولاً:**\n@{CHANNEL_USER}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إضغط هنا للاشتراك", url=f"t.me/{CHANNEL_USER}")]])
        )

    # رسالة الانتظار
    status = await message.reply_text("📥 **جاري معالجة الفيديو ذكياً...**")

    try:
        # نص الرسالة التي طلبتها
        caption_msg = (
            "اكتمل التحميل ✔️\n"
            "تم تجهيز الفيديو بأفضل جودة متاحة.\n"
            "أرسل الرابط التالي عند الطلب"
        )

        # التحميل الذكي: إعادة إرسال ملف الميديا كما هو للحفاظ على الـ Bitrate والسلاسة
        if message.video:
            await message.reply_video(message.video.file_id, caption=caption_msg)
        else:
            await message.reply_document(message.document.file_id, caption=caption_msg)

        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ حدث خطأ: {e}")

@app.on_message(filters.command("start"))
async def start_handler(_, message):
    add_user(message.from_user.id)
    await message.reply_text("👋 أهلاً بك! أرسل الفيديو وسأقوم بتجهيزه لك فوراً بأفضل جودة وسلاسة.")

print("✅ البوت يعمل الآن بنظام الإرسال الذكي والاشتراك المفتوح...")
app.run()
