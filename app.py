import streamlit as st
import requests
import json
import time
import os

# --- 설정 및 상수 ---
# Gemini API 설정
# 모델: gemini-2.5-flash-preview-09-2025 사용
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
# API 키는 Streamlit Secrets를 통해 안전하게 불러옵니다.
# 배포 시 secrets.toml 파일에 GEMINI_API_KEY = "YOUR_API_KEY" 를 설정해야 합니다.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    # 로컬 테스트 환경을 위해 환경 변수에서 불러올 수 있도록 설정 (선택 사항)
    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if not API_KEY:
        st.error("⚠️ GEMINI_API_KEY를 찾을 수 없습니다. Streamlit `secrets.toml` 파일 또는 환경 변수를 확인해주세요.")
        st.stop()

SYSTEM_PROMPT = "당신은 친절하고 도움이 되는 AI 챗봇입니다. 한국어로 답변하며, 사용자 질문에 대해 간결하고 정확하게 정보를 제공합니다. 가능한 경우, 구글 검색 결과를 활용하여 답변을 보강합니다."

# --- API 호출 함수 (지수 백오프 포함) ---

def generate_content_with_retry(prompt, history, max_retries=5):
    """
    Gemini API를 호출하고 지수 백오프를 사용하여 재시도합니다.
    Google Search grounding을 활성화합니다.
    """
    url = f"{API_BASE_URL}?key={API_KEY}"
    
    # 채팅 기록을 API 형식에 맞게 변환
    contents = []
    # 이전 대화 기록 추가
    for message in history:
        # Streamlit session state는 role='assistant' 또는 'user'로 저장됨
        contents.append({
            "role": message["role"], 
            "parts": [{"text": message["content"]}]
        })
    # 현재 사용자 프롬프트 추가
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    # API 요청 페이로드
    payload = {
        "contents": contents,
        "tools": [{"google_search": {}}],  # Google Search Grounding 활성화
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
    }

    headers = {'Content-Type': 'application/json'}

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status() # HTTP 오류 발생 시 예외 throw
            result = response.json()
            
            # 응답 파싱
            candidate = result.get('candidates', [{}])[0]
            
            if candidate and candidate.get('content', {}).get('parts', [{}])[0].get('text'):
                text = candidate['content']['parts'][0]['text']
                sources = []
                
                # 출처(Sources) 추출 (Grounding Metadata)
                grounding_metadata = candidate.get('groundingMetadata')
                if grounding_metadata and grounding_metadata.get('groundingAttributions'):
                    sources = [
                        {
                            "uri": attr['web']['uri'],
                            "title": attr['web']['title']
                        }
                        for attr in grounding_metadata['groundingAttributions']
                        if attr.get('web', {}).get('uri') and attr.get('web', {}).get('title')
                    ]
                
                return text, sources
            
            return "응답을 생성할 수 없습니다.", []

        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP 오류 발생: {e.response.status_code}. 응답: {e.response.text}")
            break  # HTTP 오류는 재시도하지 않고 종료

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                st.error("API 호출 실패. 네트워크 연결 또는 API 키를 확인해주세요.")
                return "오류: API 호출에 실패했습니다.", []

    return "오류: 알 수 없는 이유로 API 호출에 실패했습니다.", []

# --- Streamlit UI 및 채팅 로직 ---

st.set_page_config(page_title="Gemini Streamlit 챗봇", layout="centered")
st.title("💡 Streamlit Gemini 챗봇")
st.caption("Gemini API와 Google Search Grounding 기능을 활용합니다.")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("여기에 질문을 입력하세요..."):
    # 1. 사용자 메시지 기록 및 화면에 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 챗봇 응답 생성 및 표시
    with st.chat_message("assistant"):
        with st.spinner("Gemini가 답변을 생성 중입니다..."):
            
            # API 호출을 위해 채팅 기록 준비
            history_for_api = []
            # API 요청은 최대 5개 이전의 메시지만 포함 (토큰 제한 고려)
            recent_messages = st.session_state.messages[:-1][-5:] 
            
            for msg in recent_messages:
                # Streamlit의 Markdown을 API 텍스트로 사용
                history_for_api.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # API 호출
            response_text, sources = generate_content_with_retry(prompt, history_for_api)

            # 응답 텍스트를 화면에 출력
            st.markdown(response_text)

            # 출처가 있다면 함께 표시
            if sources:
                st.markdown("---")
                st.markdown("**참고 출처:**")
                for source in sources:
                    st.markdown(f"- [{source['title']}]({source['uri']})")
            
    # 3. 챗봇 응답을 세션 상태에 기록 (출처 포함하여 저장)
    full_response_content = response_text
    if sources:
        # 기록용으로 출처를 텍스트에 포함 (필요하다면)
        source_links = "\n\n---\n**참고 출처:**\n" + "\n".join([f"- [{s['title']}]({s['uri']})" for s in sources])
        full_response_content += source_links

    st.session_state.messages.append({"role": "assistant", "content": full_response_content})

# 참고: GitHub에 코드를 푸시할 때는 API 키를 코드에 직접 넣지 말고, 
# Streamlit Community Cloud의 Secrets 관리 기능을 사용하세요.
