# 📖 영어 작문 연습 (English Writing Practice)

한국어 문장을 영어로 번역하고 AI 피드백을 받는 웹 앱입니다.

## 주요 기능

- AI가 매번 새로운 한국어 문장 10개 생성
- 사용자가 영어로 번역 후 제출
- AI 피드백: 평가 / 모범 번역 / 핵심 수정 / 어려운 단어
- 브라우저 기반 UI (터미널 타이핑 불필요)

## 기술 스택

- Python 3.x
- [Streamlit](https://streamlit.io) — 웹 UI
- [Google Gemini API](https://aistudio.google.com) — AI 피드백 (무료)

## 설치 방법

```bash
pip install streamlit google-genai
```

## 환경변수 설정

1. [Google AI Studio](https://aistudio.google.com/apikey)에서 무료 API 키 발급
2. 시스템 환경변수에 추가:

```
GEMINI_API_KEY=your_api_key_here
```

**Windows 설정 방법:**
`윈도우 키 + R` → `sysdm.cpl` → 고급 → 환경 변수 → 새로 만들기

## 실행 방법

### 방법 1: 더블클릭 (Windows)
`영어연습_실행.bat` 파일을 더블클릭

### 방법 2: 터미널
```bash
streamlit run app.py
```

브라우저가 자동으로 열립니다 → `http://localhost:8501`

## 피드백 형식

| 항목 | 내용 |
|------|------|
| 평가 | ✅ 정확함 / 🔶 개선 가능 / ❌ 오류 있음 |
| 모범 번역 | 자연스러운 영어 표현 |
| 핵심 수정 | 틀리거나 어색한 부분 간결하게 |
| 어려운 단어 | 단어 / 뜻 / 예문 표 |

## 대상 학습자

- 독해 영어는 가능하지만 작문/회화 향상을 원하는 분
- C1 수준 목표
