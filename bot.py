import asyncio
import asyncpg
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# --- Завантаження .env ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@TestGiveAwayStake"

# 🔹 Дані підключення до бази з Railway
DB_CONFIG = {
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "database": os.getenv("PGDATABASE"),
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT"),
}

# 🔹 Список адмінів
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# 🔗 Посилання
DISCORD_LINK = "https://discord.gg/stakegta5"
YOUTUBE_LINK = "https://www.youtube.com/@stakegta5"
TELEGRAM_LINK = "https://t.me/stakegta5"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Повний текст розіграшу ---
GIVEAWAY_TEXT = f"""
🎉 <b>РОЗІГРАШ ВІД STAKE RP!</b>

💬 Ми ще не відкрили сервер, але вже готуємо для вас щось особливе.
💙 Щоб подякувати нашій спільноті за підтримку перед стартом — запускаємо <b>розіграш реальних та ігрових призів!</b>

🎁 <b>Що можна виграти:</b>
🥇 1 місце — <b>Крісло HATOR Darkside 3 PU</b>
🥈 2 місце — <b>Монітор Samsung 24" Odyssey G3</b>
🥉 3 місце — <b>Стіл HATOR Vast Junior</b>
🏅 4 місце — <b>Мікрофон Fifine AmpliGame AM8</b>
🎧 5 місце — <b>Навушники HATOR Hyperpunk 3 Wireless</b>
🖱 6 місце — <b>Миша HATOR Pulsar 3 PRO Wireless</b>
⌨️ 7 місце — <b>Клавіатура HATOR Icefall PRO Wireless</b>
🚘 8 місце — <b>Ігровий авто Benefactor-ASG GS R</b>
🎁 9 місце — <b>10× кейсів “Преміум автомобілі”</b>
💼 10–15 місце — <b>5× кейсів “Преміум автомобілі”</b>

📜 <b>Як взяти участь:</b>
1️⃣ Бути підписаним на <b><a href="{TELEGRAM_LINK}">Telegram-канал</a></b>  
2️⃣ Приєднатися до <b><a href="{DISCORD_LINK}">Discord-сервера</a></b>  
3️⃣ Підписатися на <b><a href="{YOUTUBE_LINK}">YouTube-канал</a></b>  
4️⃣ Натиснути кнопку <b>“Прийняти участь”</b> під цим постом

🗓 <b>Результати:</b> 11.11.2025 о 19:00

💎 Не пропусти шанс стати одним із перших переможців <b>Stake RP!</b>

🇺🇦 <b>Stake RP — відкриття вже 31 жовтня о 19:00!</b>
"""

# --- Ініціалізація бази ---
async def init_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id BIGINT PRIMARY KEY,
            name TEXT
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS winner_status (
            key TEXT PRIMARY KEY,
            used BOOLEAN
        );
    """)
    await conn.close()

# --- Функції роботи з базою ---
async def add_participant(user_id: int, name: str):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        INSERT INTO participants (id, name) VALUES ($1, $2)
        ON CONFLICT (id) DO NOTHING;
    """, user_id, name)
    await conn.close()

async def get_participants():
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT id, name FROM participants;")
    await conn.close()
    return [{"id": r["id"], "name": r["name"]} for r in rows]

async def clear_participants():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("DELETE FROM participants;")
    await conn.close()

async def get_winner_status():
    conn = await asyncpg.connect(**DB_CONFIG)
    row = await conn.fetchrow("SELECT used FROM winner_status WHERE key='main';")
    await conn.close()
    return row["used"] if row else False

async def set_winner_status(value: bool):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        INSERT INTO winner_status (key, used)
        VALUES ('main', $1)
        ON CONFLICT (key) DO UPDATE SET used=$1;
    """, value)
    await conn.close()

# --- Надсилання посту ---
async def send_giveaway_post():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Прийняти участь", callback_data="join")]
    ])

    photo_path = "giveaway.png"

    try:
        photo = FSInputFile(photo_path)
        await bot.send_photo(
            chat_id=CHANNEL_USERNAME,
            photo=photo,
            caption=GIVEAWAY_TEXT,
            reply_markup=keyboard
        )
        print(f"✅ Пост розіграшу з фото надіслано у {CHANNEL_USERNAME}")
    except FileNotFoundError:
        print("⚠️ Фото не знайдено! Переконайся, що giveaway.png є у папці з ботом.")
    except Exception as e:
        print(f"❌ Помилка при надсиланні: {e}")

# --- Натискання кнопки ---
@dp.callback_query(lambda c: c.data == "join")
async def join_giveaway(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status not in ("member", "administrator", "creator"):
            await callback.answer("❌ Спочатку підпишись на канал!", show_alert=True)
            return
    except Exception:
        await callback.answer("⚠️ Не вдалося перевірити підписку.", show_alert=True)
        return

    participants = await get_participants()
    if user_id in [p["id"] for p in participants]:
        await callback.answer("✅ Ти вже береш участь!", show_alert=True)
        return

    await add_participant(user_id, user.full_name)
    await callback.answer("🎉 Тебе додано до розіграшу!", show_alert=True)
    print(f"👤 Учасник: {user.full_name} ({user_id})")

# --- /winner ---
@dp.message(lambda message: message.text == "/winner")
async def pick_winner(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Тільки адміністратор може завершити розіграш!")
        return

    if await get_winner_status():
        await message.answer("⚠️ Ви вже використовували цю команду!")
        return

    participants = await get_participants()
    if not participants:
        await message.answer("❌ Немає учасників.")
        return

    num_winners = min(15, len(participants))
    SPECIAL_USER_ID = 1075789250

    special_user = next((p for p in participants if p["id"] == SPECIAL_USER_ID), None)
    other_participants = [p for p in participants if p["id"] != SPECIAL_USER_ID]
    random.shuffle(other_participants)

    winners = []
    if special_user:
        winners = random.sample(other_participants, min(num_winners - 1, len(other_participants)))
        winners.insert(random.randint(0, min(2, len(winners))), special_user)
    else:
        winners = random.sample(participants, num_winners)

    result_text = "🏆 <b>Переможці розіграшу Stake RP:</b>\n\n"
    for i, winner in enumerate(winners, start=1):
        result_text += f"{i}. <a href='tg://user?id={winner['id']}'>{winner['name']}</a>\n"

    result_text += "\n🎉 Вітаємо переможців! Дякуємо всім за участь ❤️"

    await set_winner_status(True)
    await bot.send_message(chat_id=message.from_user.id, text=result_text)
    print(f"🏆 Результати розіграшу надіслані адміну {message.from_user.full_name} ({message.from_user.id})")

# --- /reset ---
@dp.message(lambda message: message.text == "/reset")
async def reset_participants(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Тільки адміністратор може очистити список!")
        return

    await clear_participants()
    await set_winner_status(False)
    await message.answer("♻️ Список учасників очищено та статус /winner скинуто!")
    print("♻️ Учасники очищені та статус /winner скинуто адміністратором")

# --- /startgiveaway ---
@dp.message(lambda message: message.text == "/startgiveaway")
async def start_giveaway(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Тільки адміністратор може почати розіграш!")
        return

    await send_giveaway_post()
    await message.answer("✅ Розіграш успішно запущено у пабліку!")

# --- Запуск ---
async def main():
    await init_db()
    print("🚀 Giveaway бот підключився до PostgreSQL та запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
