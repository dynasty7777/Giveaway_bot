import asyncio
import json
import random
import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# --- Завантаження .env ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@TestGiveAwayStake"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")

# --- Створення папки data ---
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

PARTICIPANTS_FILE = os.path.join(DATA_DIR, "participants.json")
WINNER_STATUS_FILE = os.path.join(DATA_DIR, "winner_status.json")

# --- Ініціалізація файлів ---
if not os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

if not os.path.exists(WINNER_STATUS_FILE):
    with open(WINNER_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"used": False}, f, ensure_ascii=False, indent=2)

# --- Адміни ---
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# --- Посилання ---
DISCORD_LINK = "https://discord.gg/stakegta5"
YOUTUBE_LINK = "https://www.youtube.com/@stakegta5"
TELEGRAM_LINK = "https://t.me/stakegta5"

# --- Aiogram 3.7+ ---
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Текст розіграшу ---
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

# --- Gist ---
def get_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}"}

def load_from_gist():
    if not GIST_ID or not GITHUB_TOKEN:
        return []
    try:
        res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=get_headers())
        if res.status_code == 200:
            data = res.json()
            content = data["files"]["participants.json"]["content"]
            return json.loads(content)
        else:
            print(f"⚠️ Не вдалося отримати дані з Gist: {res.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Не вдалося завантажити дані з Gist: {e}")
        return []

def save_to_gist(participants):
    if not GIST_ID or not GITHUB_TOKEN:
        print("⚠️ GIST_ID або GITHUB_TOKEN не знайдено. Пропускаємо збереження.")
        return
    try:
        payload = {
            "files": {
                "participants.json": {
                    "content": json.dumps(participants, indent=2, ensure_ascii=False)
                }
            }
        }
        res = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=get_headers(), json=payload)
        if res.status_code == 200:
            print("💾 Дані учасників збережено у Gist.")
        else:
            print(f"⚠️ Помилка при збереженні у Gist: {res.status_code}")
    except Exception as e:
        print(f"❌ Помилка при збереженні у Gist: {e}")

# --- Робота з файлами ---
def load_participants():
    if os.path.exists(PARTICIPANTS_FILE):
        try:
            with open(PARTICIPANTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return load_from_gist()

def save_participants(data):
    with open(PARTICIPANTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    save_to_gist(data)

def load_winner_status():
    if os.path.exists(WINNER_STATUS_FILE):
        try:
            with open(WINNER_STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"used": False}
    return {"used": False}

def save_winner_status(status):
    with open(WINNER_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

# --- Надсилання посту ---
async def send_giveaway_post():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Прийняти участь", callback_data="join")]
    ])
    photo_path = "giveaway.png"
    try:
        photo = FSInputFile(photo_path)
        await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=photo, caption=GIVEAWAY_TEXT, reply_markup=keyboard)
        print(f"✅ Пост розіграшу з фото надіслано у {CHANNEL_USERNAME}")
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

    participants = load_participants()
    if user_id in [p["id"] for p in participants]:
        await callback.answer("✅ Ти вже береш участь!", show_alert=True)
        return

    participants.append({"id": user_id, "name": user.full_name or "Користувач"})
    save_participants(participants)
    await callback.answer("🎉 Тебе додано до розіграшу!", show_alert=True)
    print(f"👤 Учасник: {user.full_name} ({user_id})")

# --- /winner ---
@dp.message(lambda message: message.text == "/winner")
async def pick_winner(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Тільки адміністратор може завершити розіграш!")
        return

    status = load_winner_status()
    if status.get("used", False):
        await message.answer("⚠️ Ви вже використовували цю команду!")
        return

    participants = load_participants()
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

    # 🏆 Формування клікабельного списку
    result_text = "🏆 <b>Переможці розіграшу Stake RP:</b>\n\n"
    for i, winner in enumerate(winners, start=1):
        name = winner.get("name", "Користувач")
        user_id = winner.get("id")
        clickable = f"<a href='tg://user?id={user_id}'>{name}</a>"
        result_text += f"{i}. {clickable}\n"
    result_text += "\n🎉 Вітаємо переможців! Дякуємо всім за участь ❤️"

    save_winner_status({"used": True})

    # Надсилаємо адміну та в канал
    await bot.send_message(chat_id=message.from_user.id, text=result_text)
    await bot.send_message(chat_id=CHANNEL_USERNAME, text=result_text)
    print(f"🏆 Результати розіграшу опубліковані у {CHANNEL_USERNAME} та надіслані адміну {message.from_user.id}")

# --- /reset ---
@dp.message(lambda message: message.text == "/reset")
async def reset_participants(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Тільки адміністратор може очистити список!")
        return
    save_participants([])
    save_winner_status({"used": False})
    await message.answer("♻️ Список учасників очищено. Команду /winner тепер можна використати знову!")

# --- /members ---
@dp.message(lambda message: message.text == "/members")
async def show_members_count(message: types.Message):
    participants = load_participants()
    count = len(participants)
    if count == 0:
        await message.answer("😔 Ще ніхто не бере участі у розіграші.")
    else:
        await message.answer(f"👥 Зараз у розіграші <b>{count}</b> учасників!")

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
    print("🚀 Giveaway бот запущено!")
    await dp.start_polling(bot)
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
