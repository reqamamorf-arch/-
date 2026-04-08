[08.04.2026 16:10] Ktoya: `python
import os
import base64
import io
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
INWORLD_API_KEY = os.getenv("INWORLD_API_KEY")
INWORLD_TTS_URL = "https://api.inworld.ai/tts/v1/voice"
INWORLD_VOICES_URL = "https://api.inworld.ai/voices/v1/voices"

TEMPS = [
    ("0.5 — монотонно", "0.5"),
    ("1.0 — нормально", "1.0"),
    ("1.5 — экспрессивно", "1.5"),
    ("2.0 — максимум", "2.0"),
]

user_settings = {}
voices_cache = []

def get_settings(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {"voiceId": "Ashley", "temperature": 1.0}
    return user_settings[user_id]

async def fetch_voices() -> list:
    global voices_cache
    if voices_cache:
        return voices_cache
    headers = {"Authorization": f"Basic {INWORLD_API_KEY}"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(INWORLD_VOICES_URL, headers=headers)
        response.raise_for_status()
        voices_cache = response.json().get("voices", [])
        return voices_cache

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎙 Сменить голос", callback_data="menu_voice")],
        [InlineKeyboardButton("🌡 Температура", callback_data="menu_temp")],
        [InlineKeyboardButton("⚙️ Мои настройки", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

def temp_menu():
    keyboard = [[InlineKeyboardButton(label, callback_data=f"temp_{val}")] for label, val in TEMPS]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)

def voice_menu(voices: list):
    keyboard = []
    for v in voices:
        label = v["displayName"]
        if v.get("source") == "IVC":
            label = f"⭐ {label}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"voice_{v['voiceId']}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_back")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙 Бот озвучки\n\nПросто напиши текст — озвучу!\nИли открой настройки:",
        reply_markup=main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu_voice":
        await query.edit_message_text("⏳ Загружаю голоса...")
        try:
            voices = await fetch_voices()
            await query.edit_message_text("Выбери голос:", reply_markup=voice_menu(voices))
        except Exception as e:
            await query.edit_message_text(f"Ошибка загрузки голосов: {e}", reply_markup=main_menu())

    elif data == "menu_temp":
        await query.edit_message_text("Выбери температуру:", reply_markup=temp_menu())

    elif data == "menu_settings":
        s = get_settings(user_id)
        await query.edit_message_text(
            f"⚙️ Текущие настройки:\nГолос: {s['voiceId']}\nТемпература: {s['temperature']}",
            reply_markup=main_menu()
        )

    elif data == "menu_back":
        await query.edit_message_text("Настройки:", reply_markup=main_menu())

    elif data.startswith("voice_"):
        voice_id = data[len("voice_"):]
        get_settings(user_id)["voiceId"] = voice_id
        await query.edit_message_text("✅ Голос изменён!", reply_markup=main_menu())

    elif data.startswith("temp_"):
        temp = float(data[len("temp_"):])
        get_settings(user_id)["temperature"] = temp
        await query.edit_message_text(f"✅ Температура: {temp}", reply_markup=main_menu())
[08.04.2026 16:10] Ktoya: async def text_to_speech(text: str, voice_id: str, temperature: float) -> bytes:
    headers = {
        "Authorization": f"Basic {INWORLD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voiceId": voice_id,
        "modelId": "inworld-tts-1.5-max",
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(INWORLD_TTS_URL, json=payload, headers=headers)
        response.raise_for_status()
        return base64.b64decode(response.json()["audioContent"])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    s = get_settings(update.effective_user.id)
    await update.message.reply_text("🎙 Озвучиваю...")
    try:
        audio_bytes = await text_to_speech(text, s["voiceId"], s["temperature"])
        await update.message.reply_voice(voice=io.BytesIO(audio_bytes))
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if name == "main":
    main()
`
