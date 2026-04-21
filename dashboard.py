import os
from typing import Dict, List
import html

import gspread
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


# =========================================================
# CONFIG
# =========================================================
load_dotenv()

APP_TITLE = "🧩 Termfun Dashboard"
APP_SUBTITLE = "รวบรวมผลคะแนนสอบ, การสะท้อนผลกิจกรรม และ คะแนน Self-rating แต่ละทักษะ"

DEFAULT_GOOGLE_SHEET_KEY = "1pH-2bpO5FU-BniYxZR5jE8FeY6YfHfSJEF8z88_fhQQ"
REFLECTION_KEYS = [
    "ฐานวิชาการ 1 : แบ่งน้ำปันใจ",
    "ฐานวิชาการ 2 : The Cellular bridge",
    "ฐานวิชาการ 3 : Unlock the outbreak",
    "ฐานวิชาการ 4 : เกมครูเพ็ญศรี",
    "ฐานวิชาการ 5 : Forensic Science Challenge",
    "ฐานกิจกรรม 1 : ตุ๊กตาขนมปัง",
    "ฐานกิจกรรม 2 : Voices in the Room",
    "ฐานกิจกรรม 3 : Odyssey Plan & Dream Bingo",
]

SELF_RATE_GROUPS = [
    {
        "group_title": "🧠 Thinking Skills",
        "group_note": "ทักษะด้านการคิด วิเคราะห์ และสร้างแนวทางใหม่",
        "skills": [
            ("critical_thinking", "Critical Thinking", "critical thinking"),
            ("creativity", "Creativity", "creativity"),
            ("problem_solving", "Problem Solving", "problem solving"),
            ("information_literacy", "Information Literacy", "information literacy"),
        ],
    },
    {
        "group_title": "🤝 Working With Others",
        "group_note": "ทักษะด้านการทำงานร่วมกับผู้อื่นและการเข้าใจสังคมรอบตัว",
        "skills": [
            ("collaboration", "Collaboration", "collaboration"),
            ("communication", "Communication", "communication"),
            ("empathy", "Empathy", "empathy"),
            ("social_awareness", "Social Awareness", "social awareness"),
        ],
    },
    {
        "group_title": "🚀 Growth & Leadership",
        "group_note": "ทักษะด้านการเติบโต การเริ่มต้นลงมือทำ และการปรับตัว",
        "skills": [
            ("innovation", "Innovation", "innovation"),
            ("curiosity", "Curiosity", "curiosity"),
            ("initiative", "Initiative", "initiative"),
            ("adaptability", "Adaptability", "adaptability"),
        ],
    },
]

PREPOST_SUBJECTS = [
    {
        "label_th": "คณิต",
        "pre_candidates": ["pre-test คณิต", "pretest คณิต", "คณิต pre-test", "คณิต pretest", "math pre-test", "math pretest", "math_pre", "pre_math"],
        "post_candidates": ["post-test คณิต", "posttest คณิต", "คณิต post-test", "คณิต posttest", "math post-test", "math posttest", "math_post", "post_math"],
    },
    {
        "label_th": "ฟิสิกส์",
        "pre_candidates": ["pre-test ฟิสิกส์", "pretest ฟิสิกส์", "ฟิสิกส์ pre-test", "ฟิสิกส์ pretest", "physics pre-test", "physics pretest", "physics_pre", "pre_physics"],
        "post_candidates": ["post-test ฟิสิกส์", "posttest ฟิสิกส์", "ฟิสิกส์ post-test", "ฟิสิกส์ posttest", "physics post-test", "physics posttest", "physics_post", "post_physics"],
    },
    {
        "label_th": "เคมี",
        "pre_candidates": ["pre-test เคมี", "pretest เคมี", "เคมี pre-test", "เคมี pretest", "chemistry pre-test", "chemistry pretest", "chemistry_pre", "pre_chemistry"],
        "post_candidates": ["post-test เคมี", "posttest เคมี", "เคมี post-test", "เคมี posttest", "chemistry post-test", "chemistry posttest", "chemistry_post", "post_chemistry"],
    },
    {
        "label_th": "ชีวะ",
        "pre_candidates": ["pre-test ชีวะ", "pretest ชีวะ", "ชีวะ pre-test", "ชีวะ pretest", "biology pre-test", "biology pretest", "biology_pre", "pre_biology"],
        "post_candidates": ["post-test ชีวะ", "posttest ชีวะ", "ชีวะ post-test", "ชีวะ posttest", "biology post-test", "biology posttest", "biology_post", "post_biology"],
    },
    {
        "label_th": "อังกฤษ",
        "pre_candidates": ["pre-test อังกฤษ", "pretest อังกฤษ", "อังกฤษ pre-test", "อังกฤษ pretest", "english pre-test", "english pretest", "english_pre", "pre_english"],
        "post_candidates": ["post-test อังกฤษ", "posttest อังกฤษ", "อังกฤษ post-test", "อังกฤษ posttest", "english post-test", "english posttest", "english_post", "post_english"],
    },
]

st.set_page_config(
    page_title="Termfun Dashboard",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@100;200;300;400;500;600;700&display=swap');
    html, body, div, p, span, label, input, textarea, button, select {
        font-family: 'Kanit', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(145deg, #f8fcff 0%, #edf6ff 38%, #e0f0ff 100%) !important;
    }
    .main-card {
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 24px;
        padding: 1.2rem;
        box-shadow: 0 14px 40px rgba(15, 23, 42, 0.07);
        margin-bottom: 1rem;
    }
    .title-text {
        font-size: 2rem;
        font-weight: 700;
        color: #1d4ed8;
        margin-bottom: 0.3rem;
    }
    .soft-panel {
        padding: 0.8rem 1rem;
        border-radius: 20px;
        border: 1px solid rgba(191,219,254,0.75);
        background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(248,252,255,0.78));
        box-shadow: 0 10px 22px rgba(15,23,42,0.04);
        margin-bottom: 0.72rem;
        min-height: 108px;
    }
    .soft-panel-label {
        font-size: 0.68rem;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .soft-panel-value {
        font-size: 1.02rem;
        color: #0f172a;
        font-weight: 500;
        line-height: 1.6;
    }
    .sub-text {
        color: #475569;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.7rem;
        margin-top: 0.8rem;
    }
    .reflection-card {
        padding: 1rem;
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(239,246,255,0.88));
        border: 1px solid rgba(148,163,184,0.18);
        box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        margin-bottom: 0.8rem;
    }
    .reflection-chip {
        display: inline-block;
        margin-bottom: 0.5rem;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #1d4ed8;
        background: rgba(219, 234, 254, 0.95);
        border: 1px solid rgba(96,165,250,0.28);
    }
    .reflection-text {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    div[data-baseweb="select"] > div {
        border-radius: 16px !important;
        border: 1px solid rgba(191,219,254,0.9) !important;
        background: rgba(255,255,255,0.88) !important;
        box-shadow: 0 8px 18px rgba(15,23,42,0.05) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



def get_secret_or_env(name: str, default: str | None = None):
    if name in st.secrets:
        return st.secrets[name]
    return os.getenv(name, default)



def get_service_account_info() -> dict | None:
    if "gcp_service_account" in st.secrets:
        return dict(st.secrets["gcp_service_account"])
    return None


GOOGLE_SHEET_KEY = get_secret_or_env("GOOGLE_SHEET_KEY", DEFAULT_GOOGLE_SHEET_KEY)
GOOGLE_SHEET_WORKSHEET = get_secret_or_env("GOOGLE_SHEET_WORKSHEET", "data")
IDSHEET = get_secret_or_env("IDSHEET")
SERVICE_ACCOUNT_FILE = get_secret_or_env("SERVICE_ACCOUNT_FILE")


def require_env(name: str, value: str | None):
    if not value:
        st.error(f"⚠️ ไม่พบ {name} กรุณาตรวจสอบ .env หรือ Secrets")
        st.stop()



def escape_html(text: str | None) -> str:
    return html.escape("" if text is None else str(text))



def safe_float(value, default: float = 0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default



def get_google_credentials() -> Credentials:
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    service_account_info = get_service_account_info()

    if service_account_info:
        return Credentials.from_service_account_info(service_account_info, scopes=scopes)

    require_env("SERVICE_ACCOUNT_FILE", SERVICE_ACCOUNT_FILE)
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        st.error("⚠️ ไม่พบไฟล์ service account ตาม path ที่ระบุไว้")
        st.stop()

    return Credentials.from_service_account_info(st.secrets["gcp_service_account"])


@st.cache_resource
def get_gspread_client():
    return gspread.authorize(get_google_credentials())


@st.cache_data(ttl=60)
def load_sheet_data() -> List[Dict]:
    gc = get_gspread_client()
    sh = gc.open_by_key(GOOGLE_SHEET_KEY)
    worksheet = sh.worksheet(GOOGLE_SHEET_WORKSHEET)
    return worksheet.get_all_records()



def get_student_display_options(sheet_data: list[dict]) -> list[str]:
    return [str(row.get("ID", "")).strip() for row in sheet_data if str(row.get("ID", "")).strip()]



def get_selected_student(sheet_data: list[dict], selected_id: str) -> dict | None:
    return next((row for row in sheet_data if str(row.get("ID", "")).strip() == selected_id), None)



def get_prepost_value(selected_info: dict, candidates: list[str]):
    normalized = {str(k).strip().lower(): v for k, v in selected_info.items()}
    for candidate in candidates:
        value = normalized.get(candidate.strip().lower())
        if value not in (None, ""):
            return safe_float(value, None)
    return None



def get_prepost_scores(selected_info: dict) -> list[dict]:
    rows = []
    for subject in PREPOST_SUBJECTS:
        pre_score = get_prepost_value(selected_info, subject["pre_candidates"])
        post_score = get_prepost_value(selected_info, subject["post_candidates"])
        rows.append(
            {
                "วิชา": subject["label_th"],
                "Pre-test": "-" if pre_score is None else f"{pre_score:.1f}",
                "Post-test": "-" if post_score is None else f"{post_score:.1f}",
                "ผลต่าง": "-" if pre_score is None or post_score is None else f"{post_score - pre_score:+.1f}",
            }
        )
    return rows



def collect_reflection_items(selected_info: dict) -> list[dict]:
    items = []
    for key in REFLECTION_KEYS:
        text = str(selected_info.get(key, "")).strip()
        if text:
            items.append({"label": key, "text": text})
    return items



def render_star_rating(label: str, score: float, max_score: int = 5):
    score = max(0.0, min(safe_float(score), float(max_score)))
    percent = (score / max_score) * 100 if max_score > 0 else 0
    stars = "★" * max_score

    st.markdown(
        f"""
        <div style="
            padding: 0.95rem 1rem;
            border-radius: 20px;
            border: 1px solid rgba(191, 219, 254, 0.80);
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,252,255,0.82));
            box-shadow: 0 10px 22px rgba(15,23,42,0.04);
            margin-bottom: 0.8rem;
        ">
            <div style="font-size:0.78rem;color:#64748b;font-weight:600;margin-bottom:0.35rem;text-transform:uppercase;letter-spacing:0.05em;">{escape_html(label)}</div>
            <div style="display:flex;align-items:center;justify-content:space-between;gap:0.8rem;flex-wrap:wrap;">
                <div style="position:relative;display:inline-block;line-height:1;font-size:20px;letter-spacing:3px;white-space:nowrap;">
                    <div style="color:#cbd5e1;">{stars}</div>
                    <div style="position:absolute;left:0;top:0;width:{percent:.2f}%;overflow:hidden;color:#f59e0b;">{stars}</div>
                </div>
                <div style="font-size:0.98rem;font-weight:700;color:#0f172a;">{score:.1f}/{max_score}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def get_top_faculty_choices(selected_info: dict) -> list[tuple[str, str]]:
    candidates = [
        ("อันดับ 1", selected_info.get("คณะที่อยากเข้า อันดับ 1", "")),
        ("อันดับ 2", selected_info.get("คณะที่อยากเข้า อันดับ 2", "")),
        ("อันดับ 3", selected_info.get("คณะที่อยากเข้า อันดับ 3", "")),
    ]
    return [(rank, str(value).strip()) for rank, value in candidates if str(value).strip()]


require_env("GOOGLE_SHEET_KEY", GOOGLE_SHEET_KEY)
require_env("IDSHEET", IDSHEET)

try:
    sheet_data = load_sheet_data()
except Exception as exc:
    st.error(f"โหลดข้อมูลจาก Google Sheets ไม่สำเร็จ: {type(exc).__name__}: {exc}")
    st.stop()

if not sheet_data:
    st.warning("ยังไม่พบข้อมูลนักเรียนจาก Google Sheets")
    st.stop()

st.markdown(f'<div class="title-text">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-text">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

sheet_url = f"https://docs.google.com/spreadsheets/d/{IDSHEET}/edit#gid=0"
PROFILE_EXCLUDE_KEYS = ["ID"]

display_options = get_student_display_options(sheet_data)
selected_id = st.selectbox("เลือกนักเรียน", display_options)
selected_info = get_selected_student(sheet_data, selected_id)
st.link_button("🔍 เช็ค ID ตรงนี้", sheet_url)

if selected_info is None:
    st.error("ไม่พบข้อมูลของนักเรียนที่เลือก")
    st.stop()

st.markdown('<div class="section-title">📋 ข้อมูลน้อง</div>', unsafe_allow_html=True)

profile_items = [(key, value) for key, value in list(selected_info.items())[:3] if key not in PROFILE_EXCLUDE_KEYS]
profile_cols = st.columns(3)

for idx, (key, value) in enumerate(profile_items):
    with profile_cols[idx % 3]:
        st.markdown(
            f"""
            <div class="soft-panel">
                <div class="soft-panel-label">{escape_html(str(key))}</div>
                <div class="soft-panel-value">{escape_html(str(value))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<div class="section-title">🎯 คณะที่อยากเข้า 3 อันดับแรก</div>', unsafe_allow_html=True)
faculty_choices = get_top_faculty_choices(selected_info)

if faculty_choices:
    faculty_cols = st.columns(3)
    for idx, (rank, faculty) in enumerate(faculty_choices):
        with faculty_cols[idx % 3]:
            st.markdown(
                f"""
                <div class="soft-panel">
                    <div class="soft-panel-label">{escape_html(rank)}</div>
                    <div class="soft-panel-value">{escape_html(faculty)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("ยังไม่มีข้อมูลคณะที่อยากเข้า 3 อันดับแรก")

st.markdown('<div class="section-title">Reflection ตามฐาน</div>', unsafe_allow_html=True)
reflection_items = collect_reflection_items(selected_info)
reflection_filter_options = ["ทั้งหมด"] + REFLECTION_KEYS
selected_reflection_filter = st.selectbox(
    "กรอง Reflection ตามฐาน",
    reflection_filter_options,
    key="reflection_filter",
)

if selected_reflection_filter == "ทั้งหมด":
    filtered_reflections = reflection_items
else:
    filtered_reflections = [
        item for item in reflection_items
        if item["label"] == selected_reflection_filter
    ]

if filtered_reflections:
    for item in filtered_reflections:
        st.markdown(
            f"""
            <div class="reflection-card">
                <div class="reflection-chip">{escape_html(item['label'])}</div>
                <div class="reflection-text">“{escape_html(item['text'])}”</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("ฐานนี้ยังไม่มี Reflection")

st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">คะแนน Pre-test / Post-test</div>', unsafe_allow_html=True)
st.dataframe(pd.DataFrame(get_prepost_scores(selected_info)), use_container_width=True, hide_index=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">ภาพรวมทักษะจากข้อมูลในระบบ</div>', unsafe_allow_html=True)

for group in SELF_RATE_GROUPS:
    st.markdown(f"#### {group['group_title']}")
    st.caption(group["group_note"])

    cols = st.columns(2)
    for idx, skill in enumerate(group["skills"]):
        _, label, sheet_col = skill
        with cols[idx % 2]:
            render_star_rating(label, selected_info.get(sheet_col, 0))

st.markdown('</div>', unsafe_allow_html=True)
