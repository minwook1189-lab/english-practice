# 영어 작문 연습 (English Writing Practice)

한국어 문장을 영어로 번역하고 AI 피드백을 받는 웹 앱입니다.

## 주요 기능

- AI가 한국어 문장 1개 생성 → 영어로 번역 후 제출
- 추가 연습: "➕ 한 문장 더" 버튼으로 계속 연습 가능
- AI 채점: 평가 / 내 답변 / 모범 번역 3가지 버전 / 핵심 수정 / 학습 포인트 / 어려운 단어
- 연습 기록 자동 저장 (`history.json`) 및 홈 화면에서 조회/삭제

## 기술 스택

- Python 3.x
- [Streamlit](https://streamlit.io) — 웹 UI
- [Groq API](https://console.groq.com) — AI 피드백 (llama-3.3-70b-versatile)

## 설치 방법

```bash
pip install streamlit groq
```

## 환경변수 설정

[Groq Console](https://console.groq.com)에서 무료 API 키 발급 후 `영어연습_실행.bat` 파일에 설정:

```
set GROQ_API_KEY=your_api_key_here
```

## 실행 방법

### 방법 1: 더블클릭 (Windows)
`영어연습_실행.bat` 파일을 더블클릭

### 방법 2: 터미널
```bash
.venv/Scripts/streamlit.exe run app.py
```

브라우저가 자동으로 열립니다 → `http://localhost:8501`

## 채점 결과 형식

| 항목 | 내용 |
|------|------|
| 평가 | ✅ 정확함 / 🔶 개선 가능 / ❌ 오류 있음 |
| 내 답변 | 제출한 번역 |
| 모범 번역 | 자연스러운 영어 표현 3가지 버전 |
| 핵심 수정 | 틀리거나 어색한 부분 상세 설명 |
| 학습 포인트 | 이번 문장에서 배울 핵심 표현 |
| 어려운 단어 | 단어 / 뜻 / 예문 표 |

## 대상 학습자

- 독해 영어는 가능하지만 작문/회화 향상을 원하는 분
- C1 수준 목표
