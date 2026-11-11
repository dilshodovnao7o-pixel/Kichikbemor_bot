import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# States
class GameStates(StatesGroup):
    choosing_case = State()
    collecting_anamnesis = State()
    assessing_condition = State()
    finished = State()

# Cases data
CASES = {
    "case1": {
        "title": "1 yosh 8 oylik bola - isitma va yo'tal",
        "age": "1 yosh 8 oy",
        "complaint": "Isitma (38.5°C) va yo'tal 2 kundan beri",
        "mother_answers": {
            "isitma_qachon": "2 kun oldin boshlangan, kechasi baland",
            "yotal_turi": "Quruq yo'tal, ba'zan nam",
            "ovqat": "Kam yeyapti, suv ichyapti",
            "uyqu": "Bezovta, yomon uxlayapti",
            "qusish": "Yo'q",
            "diareya": "Yo'q",
            "nafas": "Tezroq nafas olayapti",
            "teri": "Odatdagidek",
            "kontakt": "Bog'cha bolalari bilan",
            "dori": "Paracetamol berilgan"
        },
        "key_points": ["isitma_qachon", "yotal_turi", "nafas", "ovqat", "uyqu"],
        "severity": "o'rtacha og'ir"
    },
    "case2": {
        "title": "3 oylik chaqaloq - qusish va isitma",
        "age": "3 oy",
        "complaint": "Qusish va 37.8°C isitma 1 kundan beri",
        "mother_answers": {
            "isitma_qachon": "Kecha kechqurun",
            "qusish": "Har ovqatdan keyin, ko'p",
            "ovqat": "Emizish kamaygan",
            "nafas": "Oddiy",
            "diareya": "Yo'q",
            "teri": "Quruqroq",
            "uyqu": "Ko'p uxlayapti",
            "kontakt": "Yo'q",
            "dori": "Hech narsa berilmagan"
        },
        "key_points": ["qusish", "ovqat", "isitma_qachon", "teri"],
        "severity": "og'ir"
    },
    "case3": {
        "title": "5 yoshli bola - qorin og'rig'i",
        "age": "5 yosh",
        "complaint": "Qorin og'rig'i va isitma 6 soatdan beri",
        "mother_answers": {
            "ogriq_joyi": "O'ng pastki qorin",
            "isitma_qachon": "Bugun ertalab",
            "qusish": "1 marta",
            "ovqat": "Hech narsa yemayapti",
            "diareya": "Yo'q",
            "nafas": "Oddiy",
            "uyqu": "Bezovta",
            "kontakt": "Maktab"
        },
        "key_points": ["ogriq_joyi", "isitma_qachon", "qusish", "ovqat"],
        "severity": "og'ir"
    }
}

# Keyboards
def cases_keyboard():
    builder = InlineKeyboardBuilder()
    for key, case in CASES.items():
        builder.button(text=case["title"], callback_data=f"case_{key}")
    builder.adjust(1)
    return builder.as_markup()

def questions_keyboard(asked: set):
    builder = InlineKeyboardBuilder()
    all_q = [
        ("isitma_qachon", "Isitma qachon boshlangan?"),
        ("yotal_turi", "Yo'tal turi?"),
        ("qusish", "Qusish bormi?"),
        ("ovqat", "Ovqatlanishi qanday?"),
        ("nafas", "Nafas olishi?"),
        ("uyqu", "Uyqu holati?"),
        ("diareya", "Diareya bormi?"),
        ("teri", "Teri holati?"),
        ("ogriq_joyi", "Og'riq qayerda?"),
        ("kontakt", "Kontaktlar?"),
        ("dori", "Dori berilganmi?")
    ]
    for key, text in all_q:
        if key not in asked:
            builder.button(text=text, callback_data=f"q_{key}")
    builder.button(text="✅ Baholashga o'tish", callback_data="assess")
    builder.adjust(1)
    return builder.as_markup()

def severity_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Qoniqarli", callback_data="sev_qoniqarli")
    builder.button(text="O'rtacha og'ir", callback_data="sev_o'rtacha")
    builder.button(text="Og'ir", callback_data="sev_og'ir")
    builder.adjust(1)
    return builder.as_markup()

def restart_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Yangi o'yin", callback_data="restart")
    return builder.as_markup()

# Handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "👨‍⚕️ <b>Kichik Bemor</b>\n"
        "Interaktiv klinik simulyatsiya (Qiyin rejim)\n\n"
        "Siz — yosh pediatr shifokorsiz.\n"
        "Bot — bemor bolaning onasi.\n\n"
        "Vazifangiz:\n"
        "• To'g'ri va kerakli anamnez yig'ish\n"
        "• Bolaning holatini to'g'ri baholash\n"
        "• Muhim ma'lumotlarni o'tkazib yubormaslik\n\n"
        "Ball tizimi ishlaydi. Noto'g'ri savollar ball kamaytiradi."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=cases_keyboard())
    await state.set_state(GameStates.choosing_case)

@dp.callback_query(F.data.startswith("case_"))
async def choose_case(callback: types.CallbackQuery, state: FSMContext):
    case_key = callback.data.split("_")[1]
    case = CASES[case_key]
    await state.update_data(case_key=case_key, asked=set(), score=0, correct_asked=0)
    text = (
        f"📋 <b>{case['title']}</b>\n\n"
        f"Yosh: {case['age']}\n"
        f"Shikoyat: {case['complaint']}\n\n"
        "Onadan savollar bering. Faqat kerakli savollarni tanlang!"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=questions_keyboard(set()))
    await state.set_state(GameStates.collecting_anamnesis)
    await callback.answer()

@dp.callback_query(F.data.startswith("q_"), GameStates.collecting_anamnesis)
async def ask_question(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    case = CASES[data["case_key"]]
    q_key = callback.data[2:]
    asked = data.get("asked", set())
    asked.add(q_key)
    score = data.get("score", 0)
    correct = data.get("correct_asked", 0)

    answer = case["mother_answers"].get(q_key, "Bu haqida ma'lumot yo'q.")
    if q_key in case["key_points"]:
        score += 10
        correct += 1
        extra = " ✅ (+10 ball)"
    else:
        score -= 5
        extra = " ⚠️ (-5 ball, keraksiz savol)"

    await state.update_data(asked=asked, score=score, correct_asked=correct)
    text = f"👩 Onaning javobi:\n{answer}{extra}\n\nKeyingi savolni tanlang:"
    await callback.message.edit_text(text, reply_markup=questions_keyboard(asked))
    await callback.answer()

@dp.callback_query(F.data == "assess", GameStates.collecting_anamnesis)
async def go_to_assess(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Bolaning holatini baholang:",
        reply_markup=severity_keyboard()
    )
    await state.set_state(GameStates.assessing_condition)
    await callback.answer()

@dp.callback_query(F.data.startswith("sev_"), GameStates.assessing_condition)
async def assess_severity(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    case = CASES[data["case_key"]]
    user_sev = callback.data[4:]
    correct_sev = case["severity"]
    score = data.get("score", 0)
    correct_asked = data.get("correct_asked", 0)
    total_key = len(case["key_points"])

    if user_sev == correct_sev:
        score += 30
        sev_result = "✅ To'g'ri baholadingiz! (+30 ball)"
    else:
        score -= 15
        sev_result = f"❌ Noto'g'ri. To'g'ri javob: {correct_sev} (-15 ball)"

    final_score = max(0, score)
    grade = "A'lo" if final_score >= 60 else "Yaxshi" if final_score >= 40 else "Qoniqarli" if final_score >= 20 else "Qayta o'rganish kerak"

    text = (
        f"🏁 <b>Natija</b>\n\n"
        f"Kerakli savollar: {correct_asked}/{total_key}\n"
        f"{sev_result}\n\n"
        f"Umumiy ball: {final_score}\n"
        f"Baho: <b>{grade}</b>\n\n"
        "Yana o'ynashni xohlaysizmi?"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=restart_keyboard())
    await state.set_state(GameStates.finished)
    await callback.answer()

@dp.callback_query(F.data == "restart")
async def restart(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback.message, state)
    await callback.answer()

@dp.message()
async def unknown(message: types.Message):
    await message.answer("/start buyrug'ini yuboring.")

async def main():
    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
