
import os
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))

# Menyimpan kategori pesan anggota
user_choices = {}

# Menyimpan hubungan pesan admin dengan pemilik pesan
message_users = {}


# =========================
# MENU UTAMA
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Pengaduan", callback_data="Pengaduan")],
        [InlineKeyboardButton("💡 Saran", callback_data="Saran")],
        [InlineKeyboardButton("❓ Pertanyaan", callback_data="Pertanyaan")],
        [InlineKeyboardButton("ℹ️ Tentang BRAJASTA", callback_data="Tentang")],
    ]

    await update.message.reply_text(
        "Selamat datang di BRAJASTA Official Bot!\n\n"
        "Silakan pilih layanan yang ingin kamu gunakan:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# TOMBOL MENU
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    
    if query.data == "Tentang":
        await query.message.reply_text(
            "𖤍 𝐁𝐑𝐀𝐉𝐀𝐒𝐓𝐀 𝐂𝐂 𖤍\n\n"
            "─────┈┈┈┄┄╌╌╌╌┄┄┈┈┈─────\n\n"
            "𝐅𝐨𝐫𝐠𝐞𝐝 𝐢𝐧 𝐬𝐢𝐥𝐞𝐧𝐜𝐞, 𝐮𝐧𝐢𝐭𝐞𝐝 𝐛𝐲 𝐩𝐫𝐢𝐝𝐞.\n\n"
            "Brajasta is a circle built on identity, "
            "loyalty, and respect. Different individuals, "
            "one bond, united under one name.\n\n"
            "We do not follow another's legacy. "
            "We create our own.\n\n"
            "𖤍 𝐖𝐄 𝐀𝐑𝐄 𝐁𝐑𝐀𝐉𝐀𝐒𝐓𝐀.\n"
            "𝑶𝒏𝒆 𝒄𝒊𝒓𝒄𝒍𝒆. 𝑶𝒏𝒆 𝒊𝒅𝒆𝒏𝒕𝒊𝒕𝒚.\n\n"
            "© 𝐁𝐑𝐀𝐉𝐀𝐒𝐓𝐀 𝐂𝐂\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "This is the official bot of BRAJASTA.\n\n"
            "Send your complaints, suggestions, "
            "or questions through this bot.\n\n"
            "Please use polite and respectful language."
        )
        return

    user_choices[query.from_user.id] = query.data

    await query.message.reply_text(
        f"Kamu memilih: {query.data}.\n\n"
        "Silakan tuliskan pesanmu. Pesan akan diteruskan "
        "kepada admin BRAJASTA."
    )


# =========================
# MENERIMA PESAN ANGGOTA
# =========================

async def receive_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    user_id = user.id

    if user_id not in user_choices:
        await update.message.reply_text(
            "Silakan pilih layanan terlebih dahulu dengan mengetik /start."
        )
        return

    category = user_choices[user_id]
    message_text = update.message.text

    admin_message = (
        "📩 PESAN BARU BRAJASTA\n\n"
        f"Kategori: {category}\n"
        f"Nama: {user.full_name}\n"
        f"Username: @{user.username if user.username else '-'}\n"
        f"User ID: {user_id}\n\n"
        f"Pesan:\n{message_text}\n\n"
        "↩️ Balas pesan ini menggunakan perintah:\n"
        "/balas ISI PESAN"
    )

    sent_message = await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=admin_message,
    )

    # Hubungkan pesan grup dengan user yang mengirim
    message_users[sent_message.message_id] = user_id

    await update.message.reply_text(
        "Pesanmu berhasil dikirim kepada admin BRAJASTA!\n"
        "Terima kasih telah menghubungi kami."
    )

    user_choices.pop(user_id, None)


# =========================
# ADMIN MEMBALAS ANGGOTA
# =========================

async def reply_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.id != ADMIN_GROUP_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Silakan gunakan /balas dengan cara me-reply pesan anggota."
        )
        return

    replied_message_id = update.message.reply_to_message.message_id
    user_id = message_users.get(replied_message_id)

    if not user_id:
        await update.message.reply_text(
            "Data pengirim tidak ditemukan. Pastikan kamu me-reply "
            "pesan asli dari bot."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Format: /balas Isi pesan untuk anggota"
        )
        return

    reply_text = " ".join(context.args)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "💬 Pesan dari Admin BRAJASTA:\n\n"
                f"{reply_text}"
            ),
        )

        await update.message.reply_text(
            "✅ Balasan berhasil dikirim kepada anggota."
        )

    except Exception:
        await update.message.reply_text(
            "❌ Balasan gagal dikirim. Anggota mungkin belum pernah "
            "membuka chat pribadi dengan bot atau telah memblokir bot."
        )


# =========================
# MENJALANKAN BOT
# =========================

def main():
    app = Application.builder().token(TOKEN).build()

    # Perintah anggota (hanya chat pribadi)
    app.add_handler(
        CommandHandler(
            "start",
            start,
            filters=filters.ChatType.PRIVATE,
        )
    )

    # Tombol menu
    app.add_handler(CallbackQueryHandler(button_handler))

    # Perintah balas khusus grup admin
    app.add_handler(
        CommandHandler(
            "balas",
            reply_user,
            filters=filters.ChatType.GROUPS,
        )
    )

    # Pesan anggota hanya diterima melalui chat pribadi
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & filters.TEXT
            & ~filters.COMMAND,
            receive_message,
        )
    )

    print("BRAJASTA Official Bot aktif!")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
