#!/usr/bin/env python3
"""
영어 작문 연습 — Streamlit 웹 앱
pip install groq streamlit supabase
환경변수: GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY
"""

import streamlit as st
from groq import Groq
import requests
import json
import os
import re
from datetime import date

MODEL = "llama-3.3-70b-versatile"

SENTENCE_PROMPT = """영어 작문 연습용 한국어 문장 1개를 만들어주세요.

학습자: 한국외대 독일어교육과 졸업, 독해 영어 능숙, C1 수준 목표

조건:
- 단순 직역이 안 되는 문장 (영어 특유의 표현/구조 필요)
- 관용 표현, 수동태, 복잡한 시제 포함
- 비즈니스/시사/일상 골고루
- 모든 단어는 반드시 한글로만 표기 (한자 절대 사용 금지)
- 문장만 출력 (번호, 설명 없이)
"""

FEEDBACK_PROMPT = """영어 작문 강사로서 아래 번역을 평가해주세요.

한국어: {korean}
학습자 번역: {user_answer}

다음 형식을 반드시 지켜서 답하세요 (한국어로):

[평가]
✅ 정확함 / 🔶 개선 가능 / ❌ 오류 있음 중 하나만 선택

[모범 번역]
자연스러운 영어 3가지 버전을 번호와 함께 제시:
1. (가장 일반적이고 자연스러운 버전)
2. (다른 구조나 표현을 사용한 버전)
3. (좀 더 격식있거나 고급 표현을 사용한 버전)

[핵심 수정]
학습자 번역에서 틀리거나 어색한 부분을 상세히 분석:
- 각 오류마다: 문제가 된 표현 → 올바른 표현 (왜 틀렸는지, 어떤 영어 규칙/관용법인지 구체적으로 설명)
오류가 없으면 "큰 오류 없음, 아래 개선 포인트 참고" 라고 쓰고 더 자연스럽게 만들 수 있는 부분 설명

[학습 포인트]
이 문장에서 핵심적으로 배워야 할 영어 표현이나 문법 포인트 1~2개를 구체적으로 설명
(예: 특정 동사의 용법, 영어에서 자주 쓰이는 구조, 한국어와 다른 사고방식 등)

[어려운 단어]
모범 번역에 쓰인 어려운 단어/표현 2~3개:
단어 | 뜻 | 짧은 예문

불필요한 인사말, 칭찬 금지."""


# ── Supabase REST ─────────────────────────────────────────
def _sb_headers():
    key = os.environ.get("SUPABASE_KEY")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

def _sb_url(path=""):
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not base or not os.environ.get("SUPABASE_KEY"):
        st.error("❌ SUPABASE_URL 또는 SUPABASE_KEY 환경변수가 없습니다.")
        st.stop()
    return f"{base}/rest/v1/history{path}"


def load_all_history() -> list:
    try:
        resp = requests.get(_sb_url("?select=*&order=created_at"), headers=_sb_headers(), timeout=10)
        grouped = {}
        for row in resp.json():
            d = row["session_date"]
            if d not in grouped:
                grouped[d] = {"date": d, "items": []}
            grouped[d]["items"].append({
                "id": row["id"],
                "korean": row.get("korean", ""),
                "user_answer": row.get("user_answer", ""),
                "eval": row.get("eval", ""),
                "model_ans": row.get("model_ans", ""),
            })
        return list(grouped.values())
    except Exception:
        return []


def extract_first_model_ans(model_ans_text: str) -> str:
    for line in model_ans_text.splitlines():
        line = line.strip()
        if line.startswith("1."):
            return line[2:].strip()
    return model_ans_text.splitlines()[0].strip() if model_ans_text else ""


def flush_history_to_db():
    saved_count = st.session_state.get("saved_count", 0)
    new_items = st.session_state.history[saved_count:]
    if not new_items:
        return
    rows = []
    for item in new_items:
        fb = item.get("feedback") or {}
        eval_text = fb.get("평가", "")
        model_ans_text = fb.get("모범 번역", "")
        first_ans = extract_first_model_ans(model_ans_text) if model_ans_text else ""
        rows.append({
            "session_date": st.session_state.session_date,
            "korean": item.get("korean", ""),
            "user_answer": item.get("user_answer", ""),
            "eval": eval_text,
            "model_ans": first_ans,
        })
    headers = _sb_headers()
    headers["Content-Type"] = "application/json; charset=utf-8"
    requests.post(_sb_url(), headers=headers, data=json.dumps(rows, ensure_ascii=False).encode("utf-8"), timeout=10)
    st.session_state.saved_count = len(st.session_state.history)


def delete_history_item(item_id: int):
    requests.delete(_sb_url(f"?id=eq.{item_id}"), headers=_sb_headers(), timeout=10)


# ── Groq API ──────────────────────────────────────────────
def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        st.error("❌ GROQ_API_KEY 환경변수가 없습니다. https://console.groq.com 에서 무료로 발급받으세요.")
        st.stop()
    return Groq(api_key=api_key)


def is_korean_only(text: str) -> bool:
    return not bool(re.search(r'[a-zA-Z\u4e00-\u9fff\u3040-\u30ff]', text))


def generate_one_sentence(client) -> str:
    for _ in range(3):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": SENTENCE_PROMPT}],
            temperature=0.9,
        )
        sentence = response.choices[0].message.content.strip()
        if is_korean_only(sentence):
            return sentence
    return re.sub(r'[a-zA-Z\u4e00-\u9fff\u3040-\u30ff]+', '', sentence).strip()


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
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    result = parse_feedback(raw)
    if not result:
        result = {"__raw__": raw}
    return result


def nl2br(text: str) -> str:
    return text.replace("\n", "<br>")


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
  .my-answer  { background: #f5f0ff; border-left: 4px solid #7c3aed; }
  .model-ans  { background: #e8f4fd; border-left: 4px solid #0d6efd; }
  .correction { background: #f8f9fa; border-left: 4px solid #6c757d; }
  .learn-point { background: #fff8e1; border-left: 4px solid #f59e0b; }
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
if "user_answer" not in st.session_state:
    st.session_state.user_answer = ""
if "history" not in st.session_state:
    st.session_state.history = []
if "session_date" not in st.session_state:
    st.session_state.session_date = str(date.today())
if "saved_count" not in st.session_state:
    st.session_state.saved_count = 0


def go_home():
    flush_history_to_db()
    st.session_state.sentences = []
    st.session_state.idx = 0
    st.session_state.feedback = None
    st.session_state.answered = False
    st.session_state.finished = False
    st.session_state.user_answer = ""
    st.session_state.history = []
    st.session_state.saved_count = 0
    st.session_state.session_date = str(date.today())


client = get_client()


# ── 홈 화면 ──────────────────────────────────────────────
if not st.session_state.sentences:
    st.title("📖 영어 작문 연습")
    st.caption("한국어 문장을 영어로 번역하고 AI 피드백을 받아보세요")
    st.divider()

    if st.button("🎯 오늘의 연습 시작", type="primary", use_container_width=True):
        with st.spinner("문장 생성 중..."):
            try:
                st.session_state.sentences = [generate_one_sentence(client)]
            except Exception as e:
                st.error(f"🚨 {e}")
                st.stop()
            st.session_state.idx = 0
            st.session_state.feedback = None
            st.session_state.answered = False
            st.session_state.finished = False
            st.session_state.user_answer = ""
            st.session_state.history = []
            st.session_state.saved_count = 0
            st.session_state.session_date = str(date.today())
        st.rerun()

    # 이전 기록 표시
    all_history = load_all_history()
    if all_history:
        st.divider()
        st.subheader("📋 이전 연습 기록")
        for session in reversed(all_history):
            session_date = session.get("date", "")
            items = session.get("items", [])
            answered = [i for i in items if i.get("user_answer")]
            label = f"📅 {session_date}  —  {len(items)}문장 ({len(answered)}개 답변)"
            with st.expander(label):
                for j, item in enumerate(items):
                    col_content, col_del = st.columns([9, 1])
                    with col_content:
                        eval_icon = item.get("eval", "").split()[0] if item.get("eval") else ""
                        st.markdown(f"**{j+1}. {item['korean']}** {eval_icon}")
                        if item.get("user_answer"):
                            st.markdown(f"✏️ **내 번역:** {item['user_answer']}")
                        else:
                            st.markdown("✏️ **내 번역:** *(건너뜀)*")
                        if item.get("model_ans"):
                            first = extract_first_model_ans(item["model_ans"])
                            st.markdown(f"📌 **모범 번역:** {first}")
                    with col_del:
                        if st.button("🗑️", key=f"del_{item['id']}", help="이 항목 삭제"):
                            delete_history_item(item["id"])
                            st.rerun()
                    st.markdown("---")
    st.stop()


# ── 완료 화면 ────────────────────────────────────────────
if st.session_state.finished:
    flush_history_to_db()

    st.title("📖 영어 작문 연습")
    st.divider()
    st.success("🎉 오늘 연습 완료!")

    if st.session_state.history:
        st.subheader("📋 오늘의 연습 기록")
        for i, item in enumerate(st.session_state.history, 1):
            with st.expander(f"{i}. {item['korean'][:35]}{'...' if len(item['korean']) > 35 else ''}"):
                st.markdown(f"**🇰🇷 한국어:** {item['korean']}")
                st.markdown(f"**✏️ 내 번역:** {item['user_answer'] if item['user_answer'] else '*(건너뜀)*'}")
                model_ans = item["feedback"].get("모범 번역", "") if item["feedback"] else ""
                if model_ans:
                    st.markdown("**📌 모범 번역:**")
                    st.markdown(model_ans)

    if st.button("🏠 홈으로", use_container_width=True):
        go_home()
        st.rerun()
    st.stop()


# ── 연습 화면 헤더 ───────────────────────────────────────
idx = st.session_state.idx
korean = st.session_state.sentences[idx]

col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("📖 영어 작문 연습")
with col_home:
    st.markdown("<div style='padding-top:16px'>", unsafe_allow_html=True)
    if st.button("🏠 홈", help="홈으로 돌아가기 (현재까지 기록은 저장됩니다)"):
        go_home()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

st.markdown(f'<p class="progress-text">오늘 {idx + 1}번째 문장</p>', unsafe_allow_html=True)
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
            try:
                st.session_state.user_answer = user_input.strip()
                st.session_state.feedback = get_feedback(client, korean, user_input.strip())
            except Exception as e:
                st.error(f"🚨 {e}")
                st.stop()
        st.session_state.answered = True
        st.rerun()

    if skipped:
        st.session_state.history.append({
            "korean": korean,
            "user_answer": "",
            "feedback": None,
        })
        flush_history_to_db()
        st.session_state.feedback = None
        st.session_state.user_answer = ""
        st.session_state.answered = True
        st.rerun()


# ── 피드백 표시 ──────────────────────────────────────────
if st.session_state.answered:
    fb = st.session_state.feedback

    if fb is not None:
        if "__raw__" in fb:
            st.markdown(f'<div class="feedback-box correction">{nl2br(fb["__raw__"])}</div>', unsafe_allow_html=True)
        else:
            eval_text = fb.get("평가", "")
            if "✅" in eval_text:
                css = "eval-good"
            elif "🔶" in eval_text:
                css = "eval-ok"
            else:
                css = "eval-bad"
            st.markdown(f'<div class="feedback-box {css}"><strong>{eval_text}</strong></div>', unsafe_allow_html=True)

            if st.session_state.user_answer:
                st.markdown(f'<div class="feedback-box my-answer">🙋 <strong>내 번역</strong><br>{st.session_state.user_answer}</div>', unsafe_allow_html=True)

            model_ans = fb.get("모범 번역", "")
            if model_ans:
                st.markdown(f'<div class="feedback-box model-ans">📌 <strong>모범 번역</strong><br>{nl2br(model_ans)}</div>', unsafe_allow_html=True)

            corrections = fb.get("핵심 수정", "")
            if corrections:
                st.markdown(f'<div class="feedback-box correction">✏️ <strong>핵심 수정</strong><br>{nl2br(corrections)}</div>', unsafe_allow_html=True)

            learn_point = fb.get("학습 포인트", "")
            if learn_point:
                st.markdown(f'<div class="feedback-box learn-point">💡 <strong>학습 포인트</strong><br>{nl2br(learn_point)}</div>', unsafe_allow_html=True)

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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏁 오늘은 여기까지", use_container_width=True):
            if fb is not None:
                st.session_state.history.append({
                    "korean": korean,
                    "user_answer": st.session_state.user_answer,
                    "feedback": fb,
                })
                flush_history_to_db()
            st.session_state.finished = True
            st.rerun()
    with col2:
        if st.button("➕ 한 문장 더", type="primary", use_container_width=True):
            if fb is not None:
                st.session_state.history.append({
                    "korean": korean,
                    "user_answer": st.session_state.user_answer,
                    "feedback": fb,
                })
                flush_history_to_db()
            with st.spinner("새 문장 생성 중..."):
                try:
                    new_sentence = generate_one_sentence(client)
                except Exception as e:
                    st.error(f"🚨 {e}")
                    st.stop()
            st.session_state.sentences.append(new_sentence)
            st.session_state.idx += 1
            st.session_state.feedback = None
            st.session_state.answered = False
            st.session_state.user_answer = ""
            st.rerun()
