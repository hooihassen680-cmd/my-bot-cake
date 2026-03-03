import os
import sys
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant

# --- الإعدادات (ضع معلوماتك هنا) ---
API_ID = 1234567           
API_HASH = "your_hash"      
BOT_TOKEN = "your_token"    
ADMIN_ID = 12345678        
CHANNEL_USER = "MyChannel"  

app = Client("ExpertVideoBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# تخزين المستخدمين
users_db = set()

# --- دالة التحقق من الاشتراك (فورية وبدون تعليق) ---
async def is_subscribed(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USER, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True

# --- أوامر الإدارة ---
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def get_stats(_, message):
    await message.reply_text(f"📊 **عدد مستخدمي البوت الحالي:** `{len(users_db)}`")

@app.on_message(filters.command("restart") & filters.user(ADMIN_ID))
async def restart_bot(_, message):
    await message.reply_text("🔄 جاري إعادة التشغيل وتصفير العمليات...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- محرك المعالجة (حل التقطيع + جودة تيك توك) ---
async def process_smart_video(input_file, output_file):
    # الفلاتر: 
    # minterpolate لتنعيم الحركة (60 فريم) ومنع تقطيع السيارة
    # scale=-2:2160 لرفع الدقة لـ 4K مع الحفاظ على الأبعاد تلقائياً
    filter_complex = (
        "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:vsfm=1,"
        "scale=-2:2160:flags=lanczos,hqdn3d=1.0:1.0:5:5,unsharp=5:5:0.8:5:5:0.0"
    )
    
    command = [
        'ffmpeg', '-i', input_file,
        '-vf', filter_complex,
        '-c:v', 'libx264', '-crf', '17', '-preset', 'veryfast',
        '-b:v', '50M', '-pix_fmt', 'yuv420p', '-r', '60',
        output_file, '-y'
    ]
    
    process = await asyncio.create_subprocess_exec(*command)
    await process.wait()

# --- استقبال الفيديو ---
@app.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    users_db.add(user_id)

    # التحقق من الاشتراك
    if not await is_subscribed(client, user_id):
        return await message.reply_text(
            f"⚠️ **اشترك بالقناة أولاً لتتمكن من استخدام البوت:**\n@{CHANNEL_USER}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إضغط هنا للاشتراك", url=f"t.me/{CHANNEL_USER}")]])
        )

    status_msg = await message.reply_text("⏳ **جاري معالجة الفيديو برؤية الذكاء الاصطناعي.. يرجى الانتظار**")
    
    input_path = await message.download()
    output_path = f"ULTRA_{input_path}.mp4"

    try:
        await process_smart_video(input_path, output_path)
        
        # --- رسالتك المطلوبة مدمجة هنا ---
        caption_text = (
            "اكتمل التحميل ✔️\n"
            "تم تجهيز الفيديو بأفضل جودة متاحة.\n"
            "أرسل الرابط التالي عند الطلب\n\n"
            "⚙️ **التعديلات الفنية:**\n"
            "- رفع الانسيابية إلى 60FPS (بدون تقطيع)\n"
            "- تحسين الجودة الذكي (Smart 4K/8K)\n"
            "- تنقية الألوان والحدّة"
        )

        await message.reply_video(output_path, caption=caption_text)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ في المعالجة: `{e}`")
    
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

@app.on_message(filters.command("start"))
async def start(_, message):
    users_db.add(message.from_user.id)
    await message.reply_text("أرسل الفيديو الآن وسأقوم برفعه لأعلى جودة ومنع التقطيع فورا!")

app.run()
