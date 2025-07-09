import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests
import os


GEMINI_API_KEY = "AIzaSyAxttoT4QK9gh0krLJXeFvCWGWLXLDh9Rg"  # use mine *2 haha
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

QUESTIONS = [
    "What genre do you prefer? (e.g., Action, Comedy, Drama, Sci-Fi, Romance)",
    "Do you prefer Anime, Series, or Movies?",
    "Do you like recent releases or classics?",
    "Do you prefer short or long?",
    "Do you want something popular or a hidden gem?"
    "any other preference?"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data is not None:
        context.user_data['answers'] = []
        context.user_data['question_idx'] = 0
    if update.message:
        await update.message.reply_text(
            "Let's find you a show! I'll ask a few questions.\nType /cancel to stop at any time.\n\n" + QUESTIONS[0]
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if context.user_data is None or 'question_idx' not in context.user_data or 'answers' not in context.user_data:
        await update.message.reply_text(
            "Type /start to begin the show recommendation process!"
        )
        return
    idx = context.user_data['question_idx']
    context.user_data['answers'].append(update.message.text.strip())
    idx += 1
    if idx < len(QUESTIONS):
        context.user_data['question_idx'] = idx
        await update.message.reply_text(QUESTIONS[idx])
    else:
        answers = context.user_data['answers']
        suggestion = await get_gemini_suggestion(answers)
        await update.message.reply_text(f"{suggestion}\nType /start to try again!")
        if context.user_data is not None:
            context.user_data.clear()

async def get_gemini_suggestion(answers):
    prompt = (
        "You are a helpful AI assistant. Based on the following preferences, suggest a show (anime, series, or movie) and explain your choice in 1-2 sentences.\n" +
        ", ".join(answers)
    )
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            return f"[Error: Gemini API returned status {response.status_code}]"
    except Exception as e:
        return f"[Error: {e}]"

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data is not None:
        context.user_data.clear()
    if update.message:
        await update.message.reply_text('Conversation cancelled. Type /start to try again!')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    TOKEN = '/////////*/////////*/////////*/////////' # your telegram bot token you can get one from BotFather 
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('cancel', cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    
    app.run_polling()
