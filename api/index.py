
import os
import secrets
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from telegram import (
    Bot,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from upstash_redis.asyncio import Redis

# =========================
# KONFIGURASI
# =========================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_GROUP_ID_RAW = os.getenv("ADMIN_GROUP_ID")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

if not TOKEN or not ADMIN_GROUP_ID_RAW or not WEBHOOK_SECRET:
    raise RuntimeError("Environment variables belum lengkap.")

try:
    ADMIN_GROUP_ID = int(ADMIN_GROUP_ID_RAW)
except ValueError:
    raise RuntimeError("ADMIN_GROUP_ID harus berupa angka.")

app = FastAPI()

try:
    redis = Redis.from_env()
except Exception:
    logger.exception("Gagal menginisialisasi Redis.")
    raise


# =========================
# MENU UTAMA
# =========================

async def start(bot, chat_id):
    keyboard = [
        [InlineKeyboardButton("📩 Pengaduan", callback_data="Pengaduan")],
        [InlineKeyboardButton("💡 Saran", callback_data="Saran")],
        [InlineKeyboardButton("❓ Pertanyaan", callback_data="Pertanyaan")],
        [InlineKeyboardButton("ℹ️ Tentang BRAJASTA", callback_data="Tentang")],
    ]

    await bot.send_message(
        chat_id=chat_id,
        text=(
            "Selamat datang di BRAJASTA Official Bot!\n\n"
            "Silakan pilih layanan yang ingin kamu gunakan:"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# TENTANG BRAJASTA
# =========================

async def about(bot, chat_id):
    await bot.send_message(
        chat_id=chat_id,
        text=(
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
        ),
    )


# =========================
# CEK ADMIN
# =========================

async def is_admin(bot, user_id):
    try:
        member = await bot.get_chat_member(
            chat_id=ADMIN_GROUP_ID,
            user_id=user_id,
        )
        return member.status in ("administrator", "creator")

    except Exception:
        logger.exception("Gagal memeriksa status admin.")
        return False


# =========================
# MEMPROSES PESAN
# =========================

async def process_message(bot, message):
    user = message.from_user

    if not user:
        return

    chat = message.chat
    text = message.text or ""

    # MENU START
    if chat.type == "private" and text.startswith("/start"):
        await start(bot, chat.id)
        return

    # BALASAN ADMIN
    if chat.id == ADMIN_GROUP_ID and text.startswith("/balas"):
        if not await is_admin(bot, user.id):
            await bot.send_message(
                chat_id=chat.id,
                text="Maaf, hanya admin BRAJASTA yang dapat menggunakan perintah ini.",
            )
            return

        if not message.reply_to_message:
            await bot.send_message(
                chat_id=chat.id,
                text=(
                    "Silakan reply pesan asli dari bot "
                    "dengan format:\n/balas Isi pesan"
                ),
            )
            return

        reply_text = text.partition(" ")[2].strip()

        if not reply_text:
            await bot.send_message(
                chat_id=chat.id,
                text="Format: /balas Isi pesan untuk anggota",
            )
            return

        original_id = message.reply_to_message.message_id

        target_user = await redis.get(f"message:{original_id}")

        if not target_user:
            await bot.send_message(
                chat_id=chat.id,
                text="Data pengirim tidak ditemukan.",
            )
            return

        try:
            await bot.send_message(
                chat_id=int(target_user),
                text=f"💬 Pesan dari Admin BRAJASTA:\n\n{reply_text}",
            )

            await bot.send_message(
                chat_id=chat.id,
                text="✅ Balasan berhasil dikirim kepada anggota.",
            )

        except Exception:
            logger.exception("Gagal mengirim balasan admin.")

            await bot.send_message(
                chat_id=chat.id,
                text="❌ Balasan gagal dikirim kepada anggota.",
            )

        return

    # ABAIKAN PESAN GRUP LAIN
    if chat.type != "private":
        return

    # ABAIKAN PESAN NON-TEKS DAN COMMAND
    if not text or text.startswith("/"):
        return

    user_id = user.id

    category = await redis.get(f"choice:{user_id}")

    if not category:
        await bot.send_message(
            chat_id=chat.id,
            text=(
                "Silakan pilih layanan terlebih dahulu "
                "dengan mengetik /start."
            ),
        )
        return

    admin_message = (
        "📩 PESAN BARU BRAJASTA\n\n"
        f"Kategori: {category}\n"
        f"Nama: {user.full_name}\n"
        f"Username: @{user.username if user.username else '-'}\n"
        f"User ID: {user_id}\n\n"
        f"Pesan:\n{text}\n\n"
        "↩️ Balas pesan ini dengan format:\n"
        "/balas ISI PESAN"
    )

    sent = await bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=admin_message,
    )

    await redis.set(
        f"message:{sent.message_id}",
        str(user_id),
    )

    await redis.delete(f"choice:{user_id}")

    await bot.send_message(
        chat_id=chat.id,
        text=(
            "Pesanmu berhasil dikirim kepada admin BRAJASTA!\n"
            "Terima kasih telah menghubungi kami."
        ),
    )


# =========================
# MEMPROSES TOMBOL
# =========================

async def process_callback(bot, callback):
    if not callback.message:
        return

    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    await bot.answer_callback_query(callback.id)

    if chat_id != user_id:
        return

    if callback.data == "Tentang":
        await about(bot, chat_id)
        return

    if callback.data in ("Pengaduan", "Saran", "Pertanyaan"):
        await redis.set(
            f"choice:{user_id}",
            callback.data,
        )

        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"Kamu memilih: {callback.data}.\n\n"
                "Silakan tuliskan pesanmu. Pesan akan diteruskan "
                "kepada admin BRAJASTA."
            ),
        )


# =========================
# HALAMAN UTAMA API
# =========================

@app.get("/")
async def home():
    return {
        "status": "BRAJASTA Official Bot API aktif"
    }


# =========================
# WEBHOOK TELEGRAM
# =========================

@app.post("/webhook")
async def webhook(request: Request):

    received_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        "",
    )

    if not secrets.compare_digest(
        received_secret,
        WEBHOOK_SECRET,
    ):
        logger.warning("Webhook ditolak: secret tidak cocok.")
        raise HTTPException(
            status_code=403,
            detail="Invalid secret",
        )

    try:
        data = await request.json()

        async with Bot(TOKEN) as bot:

            update = Update.de_json(data, bot)

            if update.message:
                await process_message(bot, update.message)

            elif update.callback_query:
                await process_callback(bot, update.callback_query)

        return {"ok": True}

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Terjadi kesalahan saat memproses webhook Telegram."
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal memproses update Telegram",
        )
