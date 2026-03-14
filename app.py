#!/usr/bin/env python3
"""
영어 작문 연습 — Streamlit 웹 앱
pip install google-genai streamlit
환경변수: GEMINI_API_KEY
"""

import streamlit as st
from google import genai
import os

MODEL = "gemini-2.5-flash"

SENTENCE_PROMPT = """영어 작문 연습용 한국어 문장 10개를 만들어주세요.

학습자: 한국외대 독일어교육과 졸업, 독해 영어 능숙, C1 수준 목표

조건:
- 단순 직역이 안 되는 문장 (영어 특유의 표현/구조 필요)
- 관용 표현, 수동태, 복잡한 시제 포함
- 비즈니스/시사/일상 골고루
- 번호와 문장만 출력 (설명 없이)
"""

FEEDBACK_PROMPT = """영어 작문 강사로서 아래 번역을 평가해주세요.

한국어: {korean}
학습자 번역: {user_answer}

다음 형식을 반드시 지켜서 답하세요 (한국어로):

[평가]
✅ 정확함 / 🔶 개선 가능 / ❌ 오류 있음 중 하나만 선택

[모범 번역]
자연스러운 영어 1가지만

[핵심 수정]
- 틀리거나 어색한 부분만 1~3개, 한 줄씩 간결하게

[어려운 단어]
모범 번역에 쓰인 어려운 단어/표현 2~3개:
단어 | 뜻 | 짧은 예문

불필요한 인사말, 칭찬, 긴 설명 금지."""


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ GEMINI_API_KEY 환경변수가 없습니다. https://aistudio.google.com/apikey 에서 발급받으세요.")
        st.stop()
    return genai.Client(api_key=api_key)


def generate_sentences(client) -> list[str]:
    response = client.models.generate_content(model=MODEL, contents=SENTENCE_PROMPT)
    sentences = []
    for line in response.text.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            parts = line.split(".", 1)
            if len(parts) == 2:
                sentences.append(parts[1].strip())
    return sentences[:10]


def parse_feedback(text: str) -> dict:
    sections = {}
    current = None
    current_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current:
                sections[current] = "\n".join(current_lines).strip()
            current = stripped[1:-1]
            current_lines = []
        else:
            current_lines.append(line)
    if current:
        sections[current] = "\n".join(current_lines).strip()
    return sections


def get_feedback(client, korean: str, user_answer: str) -> dict:
    prompt = FEEDBACK_PROMPT.format(korean=korean, user_answer=user_answer)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return parse_feedback(response.text.strip())


# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(page_title="영어 작문 연습", page_icon="📖", layout="centered")

st.markdown("""
<style>
  .stApp { max-width: 700px; margin: 0 auto; }
  .korean-sentence {
    font-size: 1.3rem; font-weight: 600;
    background: #1e3a5f; color: white;
    padding: 20px 24px; border-radius: 10px;
    margin-bottom: 16px; line-height: 1.6;
  }
  .feedback-box {
    border-radius: 8px; padding: 14px 18px;
    margin: 10px 0; line-height: 1.7;
  }
  .eval-good  { background: #d4edda; border-left: 4px solid #28a745; }
  .eval-ok    { background: #fff3cd; border-left: 4px solid #ffc107; }
  .eval-bad   { background: #f8d7da; border-left: 4px solid #dc3545; }
  .model-ans  { background: #e8f4fd; border-left: 4px solid #0d6efd; }
  .correction { background: #f8f9fa; border-left: 4px solid #6c757d; }
  .vocab-word { font-weight: bold; color: #0d6efd; }
  .progress-text { color: #6c757d; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# ── 세션 초기화 ──────────────────────────────────────────
if "sentences" not in st.session_state:
    st.session_state.sentences = []
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "feedback" not in st.session_state:
    st.session_state.feedback = None
if "answered" not in st.session_state:
    st.session_state.answered = False
if "finished" not in st.session_state:
    st.session_state.finished = False


# ── 헤더 ────────────────────────────────────────────────
st.title("📖 영어 작문 연습")
st.caption("한국어 문장을 영어로 번역하고 AI 피드백을 받아보세요")
st.divider()

client = get_client()


# ── 문장 생성 ────────────────────────────────────────────
if not st.session_state.sentences:
    if st.button("🎯 오늘의 연습 시작", type="primary", use_container_width=True):
        with st.spinner("문장 생성 중..."):
            st.session_state.sentences = generate_sentences(client)
            st.session_state.idx = 0
            st.session_state.feedback = None
            st.session_state.answered = False
            st.session_state.finished = False
        st.rerun()
    st.stop()


# ── 완료 화면 ────────────────────────────────────────────
if st.session_state.finished:
    st.success("🎉 오늘 연습 완료!")
    if st.button("🔄 다시 시작", use_container_width=True):
        st.session_state.sentences = []
        st.session_state.idx = 0
        st.session_state.feedback = None
        st.session_state.answered = False
        st.session_state.finished = False
        st.rerun()
    st.stop()


# ── 현재 문장 ────────────────────────────────────────────
total = len(st.session_state.sentences)
idx = st.session_state.idx
korean = st.session_state.sentences[idx]

st.markdown(f'<p class="progress-text">{idx + 1} / {total}</p>', unsafe_allow_html=True)
st.progress((idx) / total)

st.markdown(f'<div class="korean-sentence">🇰🇷 {korean}</div>', unsafe_allow_html=True)


# ── 입력 및 제출 ─────────────────────────────────────────
if not st.session_state.answered:
    with st.form("answer_form", clear_on_submit=False):
        user_input = st.text_area("✏️ 영어로 번역하세요", height=80, placeholder="Type your English translation here...")
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("📩 제출", type="primary", use_container_width=True)
        with col2:
            skipped = st.form_submit_button("⏭ 건너뜀", use_container_width=True)

    if submitted and user_input.strip():
        with st.spinner("채점 중..."):
            st.session_state.feedback = get_feedback(client, korean, user_input.strip())
        st.session_state.answered = True
        st.rerun()

    if skipped:
        st.session_state.answered = False
        st.session_state.feedback = None
        if idx + 1 >= total:
            st.session_state.finished = True
        else:
            st.session_state.idx += 1
        st.rerun()


# ── 피드백 표시 ──────────────────────────────────────────
if st.session_state.answered and st.session_state.feedback:
    fb = st.session_state.feedback

    # 평가
    eval_text = fb.get("평가", "")
    if "✅" in eval_text:
        css = "eval-good"
    elif "🔶" in eval_text:
        css = "eval-ok"
    else:
        css = "eval-bad"
    st.markdown(f'<div class="feedback-box {css}"><strong>{eval_text}</strong></div>', unsafe_allow_html=True)

    # 모범 번역
    model_ans = fb.get("모범 번역", "")
    if model_ans:
        st.markdown(f'<div class="feedback-box model-ans">📌 <strong>모범 번역</strong><br>{model_ans}</div>', unsafe_allow_html=True)

    # 핵심 수정
    corrections = fb.get("핵심 수정", "")
    if corrections:
        st.markdown(f'<div class="feedback-box correction">✏️ <strong>핵심 수정</strong><br>{corrections}</div>', unsafe_allow_html=True)

    # 어려운 단어
    vocab = fb.get("어려운 단어", "")
    if vocab:
        rows = [r.strip() for r in vocab.split("\n") if "|" in r]
        rows = [r for r in rows if not r.lower().startswith("단어")]
        if rows:
            st.markdown("**📚 어려운 단어**")
            table_html = '<table style="width:100%;border-collapse:collapse;margin-top:6px">'
            table_html += '<tr style="background:#f0f4f8"><th style="padding:8px;text-align:left">단어/표현</th><th style="padding:8px;text-align:left">뜻</th><th style="padding:8px;text-align:left">예문</th></tr>'
            for row in rows:
                parts = [p.strip() for p in row.split("|")]
                if len(parts) >= 3:
                    table_html += f'<tr style="border-top:1px solid #e2e8f0"><td style="padding:8px"><span class="vocab-word">{parts[0]}</span></td><td style="padding:8px">{parts[1]}</td><td style="padding:8px;color:#555;font-size:0.9em">{parts[2]}</td></tr>'
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("")

    # 다음 버튼
    if idx + 1 >= total:
        if st.button("🎉 완료!", type="primary", use_container_width=True):
            st.session_state.finished = True
            st.rerun()
    else:
        if st.button("▶ 다음 문장", type="primary", use_container_width=True):
            st.session_state.idx += 1
            st.session_state.feedback = None
            st.session_state.answered = False
            st.rerun()
