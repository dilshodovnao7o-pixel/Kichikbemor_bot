"""
Kichik Bemor — Interaktiv klinik simulyatsiya (Telegram bot)
Bolalar kasalliklari propedevtikasi asosida
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN") or "9101921724:AAFSPY0qOBejK7Btw3doIZnk9VuJBAjsa1w"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameStates(StatesGroup):
    collecting_anamnesis = State()
    assessing_condition = State()

CASE = {
    "child_name": "Sardor",
    "age": "1 yil 8 oy",
    "gender": "o'g'il bola",
}

KEY_POINTS = {
    "onset": "Kasallik qachon boshlangan?",
    "fever": "Isitma qancha bo'lgan?",
    "cough_type": "Yo'tal qanday (quruq/nam)?",
    "appetite": "Ishtahasi qanday?",
    "activity": "Faolligi o'zgarganmi?",
    "breathing": "Nafas olishi qiyinmi?",
    "previous_illness": "Oldin shunga o'xshash kasallik bo'lganmi?",
    "feeding": "Hozir qanday ovqatlanadi?",
    "vaccination": "Emlashlari to'liqmi?",
    "contacts": "Kasallar bilan muloqotda bo'lganmi?",
}

MOTHER_ANSWERS = {
    "onset": "Kecha kechqurun boshlandi. Avval biroz holisizlanib qoldi, keyin isitmasi ko'tarildi. Bugun ertalabdan yo'tal ham qo'shildi.",
    "fever": "Kecha 38.7°C bo'ldi. Paratsetamol berdik, 37.9 ga tushdi. Bugun ertalab yana 38.4 bo'ldi. Hozir ham issiq.",
    "cough_type": "Yo'tali quruq, hurrakli emas. Ko'p emas, lekin kechasi ko'proq bezovta qilyapti. Balchik chiqarmayapti.",
    "appetite": "Ishtahasi ancha kamaygan. Kechani deyarli yemadi. Faqat suv va biroz meva pyuresi ichdi. Ko'krak suti hali ham so'radi, lekin kam.",
    "activity": "Odatda juda faol edi, yugurib yurardi. Hozir sust, ko'p yotadi, o'yinchoqlarga qiziqmayapti. Ba'zida yig'lab yuboryapti.",
    "breathing": "Nafas olishi biroz tezroqdek. Burun qanotlari qimirlayapti ba'zida. Hurrak yo'q, lekin biroz og'irroq nafas olayotgandek.",
    "previous_illness": "Oldin bir necha marta shamollagan, lekin bunday isitma bilan yo'tal kamdan-kam. O'tgan oyda ORVI bo'lgan edi, tez o'tib ketgan.",
    "feeding": "1 yoshgacha deyarli faqat ko'krak suti bilan boqdim. 6 oylikdan boshlab qo'shimcha ovqat berdim. Hozir umumiy stoldan yeydi, lekin hali ham kechasi ko'krak so'radi.",
    "vaccination": "Emlashlari deyarli to'liq. Faqat oxirgi pnevmokokk emlashini biroz kechiktirib qo'yganmiz. Qizamiq-qizilcha-parotit emlashini olgan.",
    "contacts": "Bolalar bog'chasiga qatnaydi. O'tgan hafta guruhda 2-3 bola kasal bo'lgan. Uyda hech kim kasal emas.",
}

def start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🩺 O'yinni boshlash", callback_data="start_game")
    builder.button(text="ℹ️ Qanday o'ynaladi?", callback_data="how_to_play")
    builder.adjust(1)
    return builder.as_markup()

def main_questions_keyboard(asked: set):
    builder = InlineKeyboardBuilder()
    questions = [
        ("onset", "📅 Kasallik qachon boshlangan?"),
        ("fever", "🌡️ Isitma haqida so'rash"),
        ("cough_type", "😷 Yo'tal haqida so'rash"),
        ("appetite", "🍽 Ishtaha va ovqatlanish"),
        ("activity", "🏃 Faolligi va holati"),
        ("breathing", "😮‍💨 Nafas olishi"),
        ("previous_illness", "🩹 Oldingi kasalliklar"),
        ("feeding", "🍼 Ovqatlantirish anamnezi"),
        ("vaccination", "💉 Emlashlari"),
        ("contacts", "👥 Muloqot (kontakt)"),
        ("finish", "✅ Anamnezni yakunlash va baholash"),
    ]
    for key, text in questions:
        if key == "finish" or key not in asked:
            builder.button(text=text, callback_data=f"ask_{key}")
    builder.adjust(1)
    return builder.as_markup()

def severity_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Qoniqarli", callback_data="sev_satisfactory")
    builder.button(text="🟡 O'rtacha og'ir", callback_data="sev_moderate")
    builder.button(text="🟠 Og'ir", callback_data="sev_severe")
    builder.button(text="🔴 O'ta og'ir", callback_data="sev_critical")
    builder.adjust(1)
    return builder.as_markup()

def restart_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Qayta o'ynash", callback_data="start_game")
    builder.button(text="🏠 Bosh menyu", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "👨‍⚕️ <b>Kichik Bemor</b>\n"
        "Interaktiv klinik simulyatsiya\n\n"
        "Siz — yosh pediatr shifokorsiz.\n"
        "Bot — bemor bolaning onasi.\n\n"
        "Vazifangiz:\n"
        "• To'g'ri anamnez yig'ish\n"
        "• Bolaning holati va og'irlik darajasini baholash\n"
        "• Muhim ma'lumotlarni o'tkazib yubormaslik\n\n"
        "Bu oddiy test emas. Sizning savollaringiz va tartibingiz baholanadi."
    )
    await message.answer(text, reply_markup=start_keyboard(), parse_mode="HTML")

async def how_to_play(callback: CallbackQuery):
    text = (
        "📖 <b>Qanday o'ynaladi?</b>\n\n"
        "1. O'yinni boshlaysiz — sizga klinik holat beriladi.\n"
        "2. Onadan savollar so'raysiz (tugmalar orqali).\n"
        "3. Har bir javob — yangi ma'lumot.\n"
        "4. Yetarli deb hisoblasangiz — anamnezni yakunlaysiz.\n"
        "5. Bolaning og'irlik darajasini tanlaysiz.\n"
        "6. Bot sizni baholaydi.\n\n"
        "💡 Maslahat: Avval shoshilinch baholash uchun muhim narsalarni (nafas, es-hush, isitma) so'rang."
    )
    await callback.message.edit_text(text, reply_markup=start_keyboard(), parse_mode="HTML")
    await callback.answer()

async def start_game(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(asked=set(), score=0)
    intro = (
        f"📋 <b>Yangi bemor</b>\n\n"
        f"Ismi: <b>{CASE['child_name']}</b>\n"
        f"Yoshi: <b>{CASE['age']}</b>\n"
        f"Jinsi: {CASE['gender']}\n\n"
        f"Ona xavotirli ohangda:\n"
        f"<i>«Doktor, bolam isitmalab, yo'talyapti. Kecha kechqurundan boshlandi. Yordam bering...»</i>\n\n"
        f"Siz endi anamnez yig'ishni boshlashingiz mumkin.\n"
        f"Qaysi savoldan boshlaysiz?"
    )
    await state.set_state(GameStates.collecting_anamnesis)
    await callback.message.edit_text(intro, reply_markup=main_questions_keyboard(set()), parse_mode="HTML")
    await callback.answer()

async def ask_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    asked = data.get("asked", set())
    score = data.get("score", 0)
    key = callback.data.replace("ask_", "")

    if key == "finish":
        summary = (
            "📝 <b>Anamnez yig'ish yakunlandi</b>\n\n"
            "Endi <b>bolaning umumiy ahvoli va og'irlik darajasini</b> baholang.\n\n"
            "Esda tuting:\n"
            "• Qoniqarli — faol, ishtaha saqlangan\n"
            "• O'rtacha og'ir — sust, ishtaha kam, lekin hayotga tahdid yo'q\n"
            "• Og'ir — juda sust, muhim organlar faoliyati buzilgan\n"
            "• O'ta og'ir — es-hush buzilgan yoki shok"
        )
        await state.set_state(GameStates.assessing_condition)
        await callback.message.edit_text(summary, reply_markup=severity_keyboard(), parse_mode="HTML")
        await callback.answer()
        return

    if key in asked:
        await callback.answer("Bu savolni allaqachon so'ragansiz", show_alert=True)
        return

    answer = MOTHER_ANSWERS.get(key, "Kechirasiz, bu haqida aniq ayta olmayman...")
    asked.add(key)
    if key in KEY_POINTS:
        score += 1

    await state.update_data(asked=asked, score=score)
    text = (
        f"👩 <b>Ona javobi:</b>\n\n"
        f"<i>{answer}</i>\n\n"
        f"────────────────\n"
        f"Yig'ilgan muhim ma'lumotlar: <b>{score}/{len(KEY_POINTS)}</b>\n\n"
        f"Yana qanday savol berasiz?"
    )
    await callback.message.edit_text(text, reply_markup=main_questions_keyboard(asked), parse_mode="HTML")
    await callback.answer()

async def assess_severity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    score = data.get("score", 0)
    choice = callback.data.replace("sev_", "")
    correct = "moderate"
    is_correct = (choice == correct)

    if score >= 8:
        grade = "A'lo"
        comment = "Siz deyarli barcha muhim nuqtalarni so'ragansiz. Anamnez yig'ish juda yaxshi."
    elif score >= 6:
        grade = "Yaxshi"
        comment = "Asosiy ma'lumotlar yig'ilgan, lekin ba'zi muhim narsalar o'tkazib yuborilgan."
    elif score >= 4:
        grade = "Qoniqarli"
        comment = "Yetarli darajada, lekin anamnez to'liq emas."
    else:
        grade = "Zaif"
        comment = "Ko'p muhim ma'lumotlar olinmagan. Anamnez — tashxisning 50% dan ortig'ini tashkil qiladi."

    severity_text = {
        "satisfactory": "Qoniqarli",
        "moderate": "O'rtacha og'ir",
        "severe": "Og'ir",
        "critical": "O'ta og'ir"
    }

    result_text = (
        f"📊 <b>O'yin natijasi</b>\n\n"
        f"<b>Anamnez yig'ish:</b> {grade} ({score}/{len(KEY_POINTS)})\n"
        f"{comment}\n\n"
        f"<b>Sizning bahongiz:</b> {severity_text.get(choice, choice)}\n"
        f"<b>To'g'ri baholash:</b> O'rtacha og'ir\n\n"
    )

    if is_correct:
        result_text += "✅ Og'irlik darajasini to'g'ri aniqladingiz!\n\n"
    else:
        result_text += (
            "❌ Og'irlik darajasi noto'g'ri.\n"
            "Bu bolada isitma, yo'tal, sustlik va ishtaha pasayishi bor, "
            "lekin es-hush joyida va hayotga jiddiy tahdid yo'q. "
            "Shuning uchun <b>o'rtacha og'ir</b> deb baholanadi.\n\n"
        )

    result_text += (
        "────────────────\n"
        "<b>Eslatma:</b>\n"
        "• Avval shoshilinch holatlarni tekshiring\n"
        "• Anamnezni yoshga mos ravishda yig'ing\n"
        "• Onaning so'zlarini diqqat bilan tinglang\n\n"
        "Yana o'ynashni xohlaysizmi?"
    )

    await state.clear()
    await callback.message.edit_text(result_text, reply_markup=restart_keyboard(), parse_mode="HTML")
    await callback.answer()

async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "👨‍⚕️ <b>Kichik Bemor</b>\n"
        "Interaktiv klinik simulyatsiya\n\n"
        "Siz — yosh pediatr shifokorsiz.\n"
        "Bot — bemor bolaning onasi."
    )
    await callback.message.edit_text(text, reply_markup=start_keyboard(), parse_mode="HTML")
    await callback.answer()

async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.register(cmd_start, CommandStart())
    dp.callback_query.register(how_to_play, F.data == "how_to_play")
    dp.callback_query.register(start_game, F.data == "start_game")
    dp.callback_query.register(ask_question, F.data.startswith("ask_"))
    dp.callback_query.register(assess_severity, F.data.startswith("sev_"))
    dp.callback_query.register(main_menu, F.data == "main_menu")

    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
