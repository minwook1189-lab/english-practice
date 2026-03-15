# english-practice 가상환경 설치 스크립트
# 새 PC에서 처음 작업할 때 한 번만 실행하세요

Write-Host "가상환경 생성 중..." -ForegroundColor Cyan
py -m venv .venv

Write-Host "패키지 설치 중..." -ForegroundColor Cyan
.\.venv\Scripts\pip install -r requirements.txt

Write-Host ""
Write-Host "완료! 이제 VS Code에서 .venv 인터프리터를 선택하세요." -ForegroundColor Green
Write-Host "Ctrl+Shift+P -> Python: Select Interpreter -> .venv" -ForegroundColor Yellow
