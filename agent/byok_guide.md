# VS Code GitHub Copilot에 OpenAI API Key(BYOK) 등록 가이드

제공해주신 가이드 문서(`01_VSCode_Copilot에_OpenAI_API_Key(BYOK)_추가하기.pdf`)를 바탕으로 학습한, VS Code의 GitHub Copilot Chat에 개인 OpenAI API Key(BYOK, Bring Your Own Key)를 등록하는 핵심 방법입니다.

---

## 🔑 핵심 제약사항
> [!IMPORTANT]
> 본 가이드에서 제공되는 OpenAI API Key는 발급 시 **`gpt-5-mini`** 모델만 사용하도록 제한되어 있습니다. 따라서 Model ID는 반드시 **`gpt-5-mini`**로 입력/선택해야 합니다.

---

## 🛠️ 등록 절차 (Step-by-Step)

### 1. 사전 준비
1. VS Code 설치 완료 상태
2. 발급 완료된 OpenAI API Key 보유
3. VS Code 우측 하단/좌측 하단의 Copilot 버튼을 통해 **Github 계정 로그인** 완료 (인라인 자동완성 등 온전한 기능 활성화를 위해 필수)

### 2. OpenAI API Key 등록하기
1. **Chat 창 열기**: VS Code 상단 또는 사이드바의 **Chat 아이콘**을 클릭하여 Chat 화면을 엽니다.
2. **커맨드 팔레트 열기**: `Ctrl + Shift + P` 또는 `F1` 키를 누릅니다.
3. **메뉴 검색 및 선택**: `Chat: Manage Language Models`를 입력하고 해당 메뉴를 선택합니다.
4. **OpenAI Provider 추가**:
   - `Language Models` 설정 화면에서 **`+ Add Models`** 버튼을 클릭합니다.
   - 나타나는 드롭다운 목록에서 **`OpenAI`**를 선택합니다.
5. **정보 입력**:
   - **Group Name**: 기존 설정과 구분하기 위해 **`BYOK_OpenAI`**라고 입력 후 Enter 키를 누릅니다.
   - **API Key**: 발급받은 OpenAI API Key를 정확히 붙여넣은 뒤 Enter 키를 누릅니다.
6. **모델 노출 설정**:
   - 추가된 모델 목록 중에서 **`GPT-5 Mini`를 제외하고** 다른 모든 모델들은 눈 모양 아이콘을 클릭하여 보이지 않게(비활성화) 설정합니다.

### 3. 활성화 및 모델 선택
- VS Code Chat 창 하단의 **`Auto`** (또는 기존 선택된 모델명) 버튼을 클릭합니다.
- `Other Models` 카테고리 내의 **`GPT-5 Mini (BYOK_OpenAI)`** 모델을 선택합니다.

---

## ⚠️ 자주 발생하는 문제 해결 (Troubleshooting)

| 문제 현상 | 확인 및 조치 사항 |
| :--- | :--- |
| **OpenAI가 Provider 목록에 없음** | VS Code 및 GitHub Copilot 확장이 최신 버전인지 확인하고 Github 로그인을 다시 진행합니다. |
| **모델이 표시되지 않음** | API Key가 정상 등록되었는지 확인하거나, `chatLanguageModels.json` 파일을 확인합니다. Model Picker를 닫았다가 다시 열거나 VS Code를 재시작합니다. |
| **API Key 오류 / 응답 미생성** | API Key 전후에 공백이 없는지 확인하고, 계정의 결제 수단(Billing) 및 지출 한도 초과 여부, 인터넷 연결 상태를 확인합니다. |
