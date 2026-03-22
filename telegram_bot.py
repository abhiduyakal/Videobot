#!/usr/bin/env python3
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = "8787082521:AAH2K7_7Y0zLnU77luIKJk_HjDkReGfqwQg"
PINTEREST_LINK = "https://pin.it/5GtgARcTs"
INFO_CHANNEL_LINK = "https://t.me/yourchannel"
ADMIN_ID = 7575318765
VIDEO_DELETE_SECONDS = 300

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stored_video = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📌 Pinterest Subscribe", url=PINTEREST_LINK)],
        [InlineKeyboardButton("📢 Info Channel Join", url=INFO_CHANNEL_LINK)],
        [InlineKeyboardButton("🎬 Video Dekhein", callback_data="watch_video")],
    ]
    await update.message.reply_text(
        "👋 *Welcome!*\n\n📌 Pinterest subscribe karein\n📢 Info Channel join karein\n🎬 Video dekhein _(5 min baad delete hogi!)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def watch_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not stored_video.get("file_id"):
        await query.message.reply_text("⚠️ Abhi koi video nahi hai!")
        return
    sent = await query.message.reply_video(
        video=stored_video["file_id"],
        caption=f"{stored_video.get('caption', '🎬 Special Video')}\n\n⏳ *5 minute baad delete ho jaegi!*",
        parse_mode="Markdown"
    )
    context.job_queue.run_once(delete_video_job, VIDEO_DELETE_SECONDS, data={"chat_id": sent.chat_id, "message_id": sent.message_id})


async def delete_video_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
        notice = await context.bot.send_message(
            chat_id=data["chat_id"],
            text=f"🗑️ *Video delete ho gayi!*\n\n📌 [Pinterest]({PINTEREST_LINK})\n📢 [Info Channel]({INFO_CHANNEL_LINK})",
            parse_mode="Markdown"
        )
        context.job_queue.run_once(delete_notice_job, 60, data={"chat_id": data["chat_id"], "message_id": notice.message_id})
    except Exception as e:
        logger.warning(f"Error: {e}")


async def delete_notice_job(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception as e:
        logger.warning(f"Error: {e}")


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    video = update.message.video or update.message.document
    if video:
        stored_video["file_id"] = video.file_id
        stored_video["caption"] = update.message.caption or "🎬 Special Video"
        await update.message.reply_text("✅ *Video save ho gayi!*", parse_mode="Markdown")


async def setvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("📤 Ab video bhejo!")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = f"✅ Video hai: {stored_video.get('caption')}" if stored_video.get("file_id") else "❌ Koi video nahi."
    await update.message.reply_text(msg)


async def setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    global INFO_CHANNEL_LINK
    if context.args:
        INFO_CHANNEL_LINK = context.args[0]
        await update.message.reply_text(f"✅ Channel: {INFO_CHANNEL_LINK}")
    else:
        await update.message.reply_text("Example: /setchannel https://t.me/apnachannel")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setvideo", setvideo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("setchannel", setchannel))
    app.add_handler(CallbackQueryHandler(watch_video, pattern="^watch_video$"))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video))
    print("🤖 Bot chal raha hai!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
