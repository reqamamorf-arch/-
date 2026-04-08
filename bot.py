import os
import base64
import io
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
INWORLD_API_KEY = os.getenv("INWORLD_API_KEY")

INWORLD_TTS_URL = "https://api.inworld.ai/tts/v1/voice"

async def text_to_speech(text: str) -> bytes:
    headers = {
        "Authorization": f"Basic {INWORLD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "voiceId": "default-vcvv4v2mkc9qpzshu9csrq__dzheremi_1",           # ✅ camelCase — так в официальной доке
        "modelId": "inworld-tts-1.5-max",  # ✅ camelCase
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(INWORLD_TTS_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data["audioContent"])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    await update.message.reply_text("🎙 Озвучиваю...")

    try:
        audio_bytes = await text_to_speech(text)
        await update.message.reply_voice(voice=io.BytesIO(audio_bytes))
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
