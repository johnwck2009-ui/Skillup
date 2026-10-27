import json
import logging
import os
import random
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATA_FILE = Path(os.getenv("DATA_FILE", "progress.json"))

LESSONS = {
    "digital": {
        "title": "Digital Skills",
        "text": (
            "DIGITAL SKILLS — LESSON 1\n\n"
            "A strong digital foundation starts with a few habits:\n"
            "• Use strong, unique passwords for your accounts.\n"
            "• Turn on two-step verification where available.\n"
            "• Check a website's address before entering personal details.\n"
            "• Keep your device and apps updated.\n"
            "• Back up important files.\n\n"
            "Remember: never share passwords or verification codes with anyone."
        ),
    },
    "business": {
        "title": "Business Basics",
        "text": (
            "BUSINESS BASICS — LESSON 1\n\n"
            "Start by identifying a real problem your audience has. Then:\n"
            "1. Describe the people who experience the problem.\n"
            "2. Ask potential customers what they currently do about it.\n"
            "3. Create a small, affordable way to test your idea.\n"
            "4. Track costs, feedback, and sales honestly.\n"
            "5. Improve the offer using what you learn.\n\n"
            "A business idea is a hypothesis until real customers validate it."
        ),
    },
    "productivity": {
        "title": "Productivity",
        "text": (
            "PRODUCTIVITY — LESSON 1\n\n"
            "Try this simple planning method:\n"
            "• Choose the three most important tasks for today.\n"
            "• Break each task into a small, clear next step.\n"
            "• Work on one task at a time.\n"
            "• Take short breaks when your focus drops.\n"
            "• Review what you completed before planning tomorrow.\n\n"
            "Consistency is usually more useful than a complicated system."
        ),
    },
}

QUIZ = [
    {
        "question": "Which is the safest password habit?",
        "options": [
            ("Reuse one password everywhere", "wrong"),
            ("Use unique, strong passwords", "correct"),
            ("Share passwords with friends", "wrong"),
        ],
        "explanation": "Unique passwords reduce the risk that one compromised account affects others.",
    },
    {
        "question": "What should you do before investing time or money in a business idea?",
        "options": [
            ("Assume everyone will buy it", "wrong"),
            ("Ignore customer feedback", "wrong"),
            ("Test whether customers need it", "correct"),
        ],
        "explanation": "Customer research and small tests help validate whether a problem and solution are real.",
    },
    {
        "question": "Which approach helps you focus on important work?",
        "options": [
            ("Multitask on everything", "wrong"),
            ("Choose priorities and work one at a time", "correct"),
            ("Avoid planning completely", "wrong"),
        ],
        "explanation": "Clear priorities and single-tasking can make work easier to manage.",
    },
    {
        "question": "What is two-step verification designed to do?",
        "options": [
            ("Add another layer of account security", "correct"),
            ("Make your password public", "wrong"),
            ("Automatically delete your account", "wrong"),
        ],
        "explanation": "It adds a second check beyond your password when signing in.",
    },
    {
        "question": "What is a useful way to improve a new product or service?",
        "options": [
            ("Never change anything", "wrong"),
            ("Listen to users and test improvements", "correct"),
            ("Ignore all feedback", "wrong"),
        ],
        "explanation": "Feedback and careful testing help you improve a product based on actual needs.",
    },
]

DAILY_TIPS = [
    "Digital safety tip: never share one-time login codes with someone who contacts you unexpectedly.",
    "Business tip: talk to potential customers before spending heavily on a new idea.",
    "Productivity tip: turn a large task into a small action you can complete in 10 minutes.",
    "Learning tip: explain a new idea in your own words to check your understanding.",
    "Online safety tip: pause before opening unexpected links or attachments.",
    "Business tip: record your costs so you can understand where your money goes.",
    "Learning tip: short, regular practice sessions can help you retain information.",
]


def load_progress():
    try:
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not read progress file; starting with empty progress.")
    return {}


def save_progress(data):
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = DATA_FILE.with_suffix(".tmp")
        temp_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp_file.replace(DATA_FILE)
    except OSError:
        logger.exception("Could not save progress. Check the deployment's writable storage.")


def get_user_progress(user_id):
    data = load_progress()
    return data.get(str(user_id), {"lessons": [], "quiz_correct": 0, "quiz_answered": 0})


def update_user_progress(user_id, updater):
    data = load_progress()
    key = str(user_id)
    user_data = data.setdefault(
        key, {"lessons": [], "quiz_correct": 0, "quiz_answered": 0}
    )
    updater(user_data)
    save_progress(data)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Learn a Skill", callback_data="lessons")],
        [InlineKeyboardButton("🧠 Take a Quiz", callback_data="quiz")],
        [InlineKeyboardButton("💡 Daily Learning", callback_data="daily")],
        [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
    ])


def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main Menu", callback_data="home")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("quiz_index", None)
    context.user_data.pop("quiz_order", None)
    message = (
        "Welcome to SkillUp Academy!\n\n"
        "Build your knowledge with short lessons, quick quizzes, and practical learning tips. "
        "Choose an option below to get started. Everything happens right here in Telegram."
    )
    await update.effective_message.reply_text(message, reply_markup=main_menu())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Use /start to open the menu. Choose Learn a Skill for lessons, Take a Quiz to test your knowledge, "
        "Daily Learning for a practical tip, or My Progress to view your saved results.",
        reply_markup=main_menu(),
    )


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "home":
        context.user_data.pop("quiz_index", None)
        context.user_data.pop("quiz_order", None)
        await query.edit_message_text(
            "Welcome to SkillUp Academy! Choose what you'd like to do:",
            reply_markup=main_menu(),
        )
    elif action == "lessons":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Digital Skills", callback_data="lesson:digital")],
            [InlineKeyboardButton("Business Basics", callback_data="lesson:business")],
            [InlineKeyboardButton("Productivity", callback_data="lesson:productivity")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
        ])
        await query.edit_message_text("Choose a lesson:", reply_markup=keyboard)
    elif action.startswith("lesson:"):
        lesson_key = action.split(":", 1)[1]
        lesson = LESSONS.get(lesson_key)
        if not lesson:
            await query.edit_message_text("That lesson could not be found.", reply_markup=back_menu())
            return

        user_id = query.from_user.id
        def mark_lesson(user_data):
            completed = user_data.setdefault("lessons", [])
            if lesson_key not in completed:
                completed.append(lesson_key)
        update_user_progress(user_id, mark_lesson)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Choose Another Lesson", callback_data="lessons")],
            [InlineKeyboardButton("🧠 Take a Quiz", callback_data="quiz")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
        ])
        await query.edit_message_text(lesson["text"], reply_markup=keyboard)
    elif action == "quiz":
        context.user_data["quiz_order"] = random.sample(range(len(QUIZ)), len(QUIZ))
        context.user_data["quiz_index"] = 0
        await send_quiz_question(query, context)
    elif action.startswith("answer:"):
        parts = action.split(":")
        if len(parts) != 3:
            await query.edit_message_text("Please start a new quiz from the menu.", reply_markup=back_menu())
            return
        try:
            question_index = int(parts[1])
        except ValueError:
            await query.edit_message_text("Please start a new quiz from the menu.", reply_markup=back_menu())
            return
        selected = parts[2]
        order = context.user_data.get("quiz_order", [])
        current = context.user_data.get("quiz_index")
        if current is None or current >= len(order) or order[current] != question_index:
            await query.edit_message_text("This quiz question has expired. Start a new quiz when you're ready.", reply_markup=back_menu())
            return
        question = QUIZ[question_index]
        correct = selected == "correct"
        def record_answer(user_data):
            user_data["quiz_answered"] = user_data.get("quiz_answered", 0) + 1
            if correct:
                user_data["quiz_correct"] = user_data.get("quiz_correct", 0) + 1
        update_user_progress(query.from_user.id, record_answer)
        context.user_data["quiz_index"] = current + 1
        feedback = ("Correct! " if correct else "Not quite. ") + question["explanation"]
        await query.edit_message_text(feedback)
        await send_next_quiz_or_finish(query, context)
    elif action == "daily":
        tip = random.choice(DAILY_TIPS)
        await query.edit_message_text(
            "💡 DAILY LEARNING\n\n" + tip,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Another Tip", callback_data="daily")],
                [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
            ]),
        )
    elif action == "progress":
        progress = get_user_progress(query.from_user.id)
        answered = progress.get("quiz_answered", 0)
        correct = progress.get("quiz_correct", 0)
        accuracy = round(correct / answered * 100) if answered else 0
        lesson_count = len(progress.get("lessons", []))
        await query.edit_message_text(
            "📊 YOUR LEARNING PROGRESS\n\n"
            f"Lessons completed: {lesson_count}/{len(LESSONS)}\n"
            f"Quiz questions answered: {answered}\n"
            f"Correct answers: {correct}\n"
            f"Quiz accuracy: {accuracy}%\n\n"
            "Keep learning and try another lesson or quiz!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Learn a Skill", callback_data="lessons")],
                [InlineKeyboardButton("🧠 Take a Quiz", callback_data="quiz")],
                [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
            ]),
        )
    elif action == "about":
        await query.edit_message_text(
            "ABOUT SKILLUP ACADEMY\n\n"
            "SkillUp Academy is an educational Telegram bot with practical digital skills lessons, "
            "business basics, productivity tips, and interactive knowledge quizzes. "
            "Learn at your own pace, directly in this chat.",
            reply_markup=back_menu(),
        )


async def send_quiz_question(query, context):
    order = context.user_data.get("quiz_order", [])
    index = context.user_data.get("quiz_index", 0)
    if index >= len(order):
        await finish_quiz(query, context)
        return
    question_index = order[index]
    question = QUIZ[question_index]
    options = list(question["options"])
    random.shuffle(options)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"answer:{question_index}:{answer}")]
        for label, answer in options
    ] + [[InlineKeyboardButton("⬅️ End Quiz", callback_data="home")]])
    await query.edit_message_text(
        f"🧠 QUIZ — Question {index + 1} of {len(order)}\n\n{question['question']}",
        reply_markup=keyboard,
    )


async def send_next_quiz_or_finish(query, context):
    await send_quiz_question(query, context)


async def finish_quiz(query, context):
    progress = get_user_progress(query.from_user.id)
    order = context.user_data.get("quiz_order", [])
    answered = len(order)
    correct = progress.get("quiz_correct", 0)
    # Report this quiz's score using the per-quiz counter stored at quiz start.
    quiz_start_correct = context.user_data.get("quiz_start_correct", correct)
    score = max(0, correct - quiz_start_correct)
    context.user_data.pop("quiz_order", None)
    context.user_data.pop("quiz_index", None)
    context.user_data.pop("quiz_start_correct", None)
    await query.edit_message_text(
        f"Quiz complete!\n\nYour score: {score}/{answered}\n\n"
        "Review a lesson or take another quiz to keep learning.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Try Again", callback_data="quiz")],
            [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")],
        ]),
    )


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Please use the menu buttons to explore lessons, quizzes, and learning tips.",
        reply_markup=main_menu(),
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Add your Telegram bot token as an environment variable."
        )
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    logger.info("SkillUp Academy bot is starting.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
