from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "MASUKKAN_TOKEN_DARI_BOTFATHER"

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Menu", callback_data="menu")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("❌ Tutup", callback_data="close")]
    ]
    await update.message.reply_text(
        "🤖 *Halo! Saya Bot Telegram*\n\nPilih menu di bawah:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# /menu
async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🛠 Tools", callback_data="tools"),
            InlineKeyboardButton("📦 Produk", callback_data="produk")
        ],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back")]
    ]
    await update.message.reply_text(
        "📋 *Menu Utama*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Handle tombol
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu":
        keyboard = [
            [
                InlineKeyboardButton("🛠 Tools", callback_data="tools"),
                InlineKeyboardButton("📦 Produk", callback_data="produk")
            ],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back")]
        ]
        await query.edit_message_text(
            "📋 *Menu Utama*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "info":
        await query.edit_message_text(
            "ℹ️ *Info Bot*\n\n"
            "Bot ini dibuat dengan Python.\n"
            "Versi: 1.0",
            parse_mode="Markdown"
        )

    elif query.data == "tools":
        await query.edit_message_text(
            "🛠 *Tools*\n\n"
            "- Cek ID\n- Spam (coming soon)\n- Auto Reply",
            parse_mode="Markdown"
        )

    elif query.data == "produk":
        await query.edit_message_text(
            "📦 *Produk*\n\n"
            "- Nokos\n- Akun Premium\n- VPS",
            parse_mode="Markdown"
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("📋 Menu", callback_data="menu")],
            [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
            [InlineKeyboardButton("❌ Tutup", callback_data="close")]
        ]
        await query.edit_message_text(
            "🤖 *Halo! Saya Bot Telegram*\n\nPilih menu di bawah:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "close":
        await query.message.delete()

# Jalankan bot
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CallbackQueryHandler(button))

    print("✅ Bot berjalan!")
    app.run_polling()

if __name__ == "__main__":
    main()