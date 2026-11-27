
import asyncio
from dotenv import load_dotenv
from dotenv import dotenv_values
from telegram import Bot

load_dotenv()
token = dotenv_values(".env").get("BOT_TOKEN")

async def main():
    bot = Bot(token)
    info = await bot.get_me()
    print("Koneksi berhasil!")
    print("Nama bot:", info.first_name)
    print("Username bot:", info.username)
    print("ID bot:", info.id)

asyncio.run(main())

