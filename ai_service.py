import os
import openai
from config import Config

openai.api_key = Config.OPENAI_API_KEY


# =============================
#   WHISPER — Audio → TEXT
# =============================

def transcribe_audio(audio_path: str) -> str:
    """
    Audio faylni Whisper model orqali matnga o‘giradi.
    """
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
        return transcript["text"]
    except Exception as e:
        print("Whisper error:", e)
        return ""


# =========================================
#   GPT-4o-mini — Matnni AI tahlil qilish
# =========================================

def analyze_client_review(text: str) -> dict:
    """
    Foydalanuvchi audio reviewi uchun AI tahlil.
    """
    prompt = f"""
    Quyidagi foydalanuvchi sharhini tahlil qil:

    "{text}"

    Natijani JSON formatida qaytar:

    {{
        "sentiment_score": (0-100),
        "quality_score": (0-100),
        "difficulty": 0,
        "materials_used": "",
        "extra_cost": 0,
        "recommended": "",
        "ai_summary": ""
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response["choices"][0]["message"]["content"]
        return eval(content)
    except Exception as e:
        print("GPT error:", e)
        return {}


def analyze_master_report(text: str) -> dict:
    """
    Usta audio hisobotining AI tahlili.
    """
    prompt = f"""
    Quyidagi usta tomonidan aytilgan audio hisobotni tahlil qil:

    "{text}"

    Natijani JSON formatida qaytar:

    {{
        "sentiment_score": 0,
        "quality_score": (0-100),
        "difficulty": (1-10),
        "materials_used": "",
        "extra_cost": 0,
        "recommended": "",
        "ai_summary": ""
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response["choices"][0]["message"]["content"]
        return eval(content)
    except Exception as e:
        print("GPT error:", e)
        return {}


# =========================================
#   FULL AI PIPELINE
# =========================================

def analyze_audio_file(order_id: int, audio_path: str, audio_type: str, db, AIReview):
    """
    Audio → Whisper → GPT → DB saqlash.
    audio_type = 'client' yoki 'master'
    """
    # 1) Audio → matn
    transcript = transcribe_audio(audio_path)

    if not transcript:
        return None

    # 2) AI tahlili
    if audio_type == "client":
        analysis = analyze_client_review(transcript)
    else:
        analysis = analyze_master_report(transcript)

    # 3) DBga yozish
    ai_review = AIReview(
        order_id=order_id,
        audio_file=audio_path,
        audio_type=audio_type,
        transcript=transcript,
        ai_summary=analysis.get("ai_summary", ""),
        sentiment_score=analysis.get("sentiment_score", 0),
        quality_score=analysis.get("quality_score", 0),
        difficulty=analysis.get("difficulty", 0),
        materials_used=analysis.get("materials_used", ""),
        extra_cost=analysis.get("extra_cost", 0),
        recommended=analysis.get("recommended", "")
    )

    db.session.add(ai_review)
    db.session.commit()

    return ai_review
