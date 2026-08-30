import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, PRICING, WEBHOOK_PORT
import database as db
from payment_gateway import create_invoice, new_order_id, AutoKuyError
from webhook_server import build_webhook_app
from telethon.errors import SessionPasswordNeededError
from session_generator import generate_string_session, complete_login

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ConversationHandler states buat proses deploy userbot (setelah bayar)
PHONE, OTP, PASSWORD = range(3)

PACKAGE_LABELS = {
    "1_month": "1 Bulan",
    "3_months": "3 Bulan",
    "lifetime": "Lifetime",
}


# ---------- Menu utama ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.create_user(update.effective_user.id, update.effective_user.username)
    keyboard = [
        [InlineKeyboardButton("🚀 Deploy Userbot", callback_data="deploy")],
        [InlineKeyboardButton("📄 Cek Status", callback_data="status")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
    ]
    await update.message.reply_text(
        "🤖 *Auto Deploy Userbot*\n\nPilih menu di bawah:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "deploy":
        keyboard = [
            [InlineKeyboardButton(f"{label} - Rp{PRICING[key]:,}", callback_data=f"buy_{key}")]
            for key, label in PACKAGE_LABELS.items()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back")])
        await query.edit_message_text(
            "📦 *Pilih Paket Userbot*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif query.data == "info":
        await query.edit_message_text(
            "ℹ️ *Info Bot*\n\nLayanan auto deploy userbot Telegram.\nVersi: 2.0",
            parse_mode="Markdown",
        )

    elif query.data == "status":
        await send_status(query, context)

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("🚀 Deploy Userbot", callback_data="deploy")],
            [InlineKeyboardButton("📄 Cek Status", callback_data="status")],
            [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        ]
        await query.edit_message_text(
            "🤖 *Auto Deploy Userbot*\n\nPilih menu di bawah:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif query.data.startswith("buy_"):
        await handle_buy(query, context)


async def send_status(query, context):
    user = db.get_user(query.from_user.id)
    if not user or not user.is_premium:
        text = "❌ Kamu belum punya userbot aktif. Pilih *Deploy Userbot* buat mulai."
    else:
        until = user.premium_until.strftime("%d %b %Y") if user.premium_until else "Lifetime"
        text = f"✅ Userbot aktif.\nBerlaku sampai: *{until}*"
    await query.edit_message_text(text, parse_mode="Markdown")


# ---------- Pembayaran ----------

async def handle_buy(query, context):
    package = query.data.replace("buy_", "")
    amount = PRICING[package]
    order_id = new_order_id()
    telegram_id = query.from_user.id

    db.create_transaction(telegram_id, order_id, package, amount)

    await query.edit_message_text("⏳ Membuat invoice pembayaran...")

    try:
        invoice = await create_invoice(
            order_id=order_id,
            amount=amount,
            customer_name=query.from_user.full_name or "Customer",
            customer_phone=str(telegram_id),
        )
    except AutoKuyError as e:
        logger.exception("Gagal bikin invoice")
        await query.edit_message_text(
            "❌ Gagal membuat invoice. Coba lagi beberapa saat, atau hubungi admin."
        )
        return

    db.set_transaction_invoice(order_id, invoice["invoice_id"], invoice["payment_url"])

    keyboard = [[InlineKeyboardButton("💳 Bayar Sekarang", url=invoice["payment_url"])]]
    await query.edit_message_text(
        f"📦 Paket: *{PACKAGE_LABELS[package]}*\n"
        f"💰 Total: *Rp{invoice['total']:,}*\n"
        f"⏰ Bayar sebelum: {invoice['expires_at']}\n\n"
        "Setelah bayar, kamu akan otomatis dikonfirmasi di sini dan bisa lanjut deploy userbot.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ---------- Deploy userbot (dipanggil manual via /deploy setelah bayar) ----------

async def deploy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    if not user or not user.is_premium:
        await update.message.reply_text(
            "❌ Kamu belum punya paket aktif. Pilih *Deploy Userbot* di /start dulu.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📱 Kirim nomor HP akun yang mau di-deploy (format: 628xxxxxxxxxx).\n\n"
        "⚠️ Nomor ini dipakai untuk login ke akun Telegram kamu sendiri. "
        "Jangan pernah kirim nomor/OTP orang lain."
    )
    return PHONE


async def deploy_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import API_ID, API_HASH

    phone = update.message.text.strip()
    context.user_data["phone"] = phone

    await update.message.reply_text("⏳ Mengirim kode OTP...")
    try:
        client, string_session = await generate_string_session(API_ID, API_HASH, phone)
    except Exception:
        logger.exception("Gagal kirim OTP")
        await update.message.reply_text("❌ Gagal mengirim OTP. Cek kembali nomornya lalu /deploy ulang.")
        return ConversationHandler.END

    context.user_data["client"] = client
    await update.message.reply_text("🔑 Masukkan kode OTP yang kamu terima:")
    return OTP


async def deploy_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    context.user_data["code"] = code
    client = context.user_data["client"]
    phone = context.user_data["phone"]

    try:
        string_session = await complete_login(client, phone, code)
    except SessionPasswordNeededError:
        await update.message.reply_text("🔒 Akun ini pakai 2FA. Kirim password-nya:")
        return PASSWORD
    except Exception:
        logger.exception("Login gagal")
        await update.message.reply_text("❌ Kode OTP salah/expired. /deploy untuk mengulang.")
        return ConversationHandler.END

    return await finish_deploy(update, context, string_session)


async def deploy_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    client = context.user_data["client"]
    phone = context.user_data["phone"]
    code = context.user_data["code"]

    try:
        string_session = await complete_login(client, phone, code, password=password)
    except Exception:
        logger.exception("Login 2FA gagal")
        await update.message.reply_text("❌ Password salah. /deploy untuk mengulang.")
        return ConversationHandler.END

    return await finish_deploy(update, context, string_session)


async def finish_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE, string_session: str):
    telegram_id = update.effective_user.id
    phone = context.user_data.get("phone")

    db.update_user_session(telegram_id, phone, string_session)
    context.user_data.clear()

    await update.message.reply_text(
        "✅ Userbot berhasil di-deploy dan aktif!\nCek status kapan saja lewat /start → Cek Status."
    )
    return ConversationHandler.END


async def deploy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Dibatalkan.")
    return ConversationHandler.END


# ---------- Runner: polling + webhook server bareng ----------

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))

    deploy_conv = ConversationHandler(
        entry_points=[CommandHandler("deploy", deploy_start)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deploy_phone)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, deploy_otp)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, deploy_password)],
        },
        fallbacks=[CommandHandler("cancel", deploy_cancel)],
    )
    app.add_handler(deploy_conv)

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        # Web server buat nerima webhook AutoKuy Pay, jalan di proses yang sama
        from aiohttp import web
        webhook_app = build_webhook_app(app.bot)
        runner = web.AppRunner(webhook_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
        await site.start()
        logger.info("✅ Bot polling + webhook server jalan di port %s", WEBHOOK_PORT)

        try:
            await asyncio.Event().wait()  # jalan selamanya
        finally:
            await runner.cleanup()
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
