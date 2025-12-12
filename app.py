import streamlit as st
from google import genai
# google.genai.errors 경로가 최신 버전에서 표준입니다.
try:
    from google.genai.errors import (
        PermissionDenied,
        ResourceExhausted,
        Unauthenticated,
        APIError
    )
except ImportError as e:
    # 캐시 지우고 재실행했음에도 이 오류가 계속되면,
    # 이는 Streamlit Cloud 환경 자체의 문제입니다.
    st.error(f"라이브러리 임포트 오류가 발생했습니다: {e}")
    st.warning("⚠️ **심각한 환경 문제입니다.** Streamlit Cloud에서 캐시를 지웠는데도 이 오류가 계속된다면, GitHub에서 프로젝트를 **삭제 후 재배포**를 시도하거나, `google-genai`의 버전을 명시한 `requirements.txt`가 올바른지 다시 확인해야 합니다.")
    st.stop()
except Exception as e:
    st.error(f"예상치 못한 초기화 오류: {e}")
    st.stop()


# --- UI 설정 ---
st.set_page_config(page_title="Gemini API 오류 진단기", layout="centered")
st.title("Gemini API 오류 진단 및 수정기 🛠️")
st.markdown("Streamlit 환경에서 Gemini API 연결 상태를 확인하고, 발생 가능한 오류를 진단합니다.")

# --- API 키 로드 ---
api_key = None
try:
    # st.secrets에서 GEMINI_API_KEY를 안전하게 불러옵니다.
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("🚨 환경 변수 오류: Streamlit Secrets에서 'GEMINI_API_KEY'를 찾을 수 없습니다.")
    st.info("Streamlit Cloud 설정 (Settings -> Secrets)에서 API 키를 `GEMINI_API_KEY = \"YOUR_KEY\"` 형식으로 등록했는지 확인해주세요.")
    st.stop()

# --- 클라이언트 초기화 ---
client = None
if api_key:
    try:
        # 불러온 API 키로 Gemini 클라이언트를 초기화합니다.
        client = genai.Client(api_key=api_key)
        st.sidebar.success("✅ Gemini 클라이언트 초기화 완료.")
        st.sidebar.text("이제 AI 응답 테스트를 할 수 있습니다.")
    except Exception as e:
        st.error(f"클라이언트 초기화 중 예상치 못한 오류가 발생했습니다. 키 유효성을 확인해주세요: {e}")
        client = None 

# --- API 호출 및 오류 진단 ---
if client:
    model = 'gemini-2.5-flash'
    prompt = st.text_area(
        "테스트 프롬프트 (수정 가능)",
        "저는 Streamlit 앱 배포 오류를 성공적으로 해결했습니다. 이에 대해 축하하는 매우 신나는 문장 하나만 작성해 주세요.",
        height=100
    )
    
    st.info(f"사용 모델: **{model}**")

    if st.button("AI 응답 생성 및 오류 진단 테스트 시작 🚀"):
        st.subheader("진단 결과:")
        with st.spinner("응답을 생성하며 API 상태를 확인하는 중입니다. 문제가 있다면 오류 코드가 표시됩니다..."):
            try:
                # API 호출
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                st.success("🎉 API 호출 성공: 모든 설정이 올바릅니다.")
                st.subheader("Gemini 응답:")
                st.info(response.text)

            except (PermissionDenied, Unauthenticated) as e:
                st.error("🛑 권한/인증 오류 (HTTP 401/403): API 키 문제")
                st.warning("1. **API 키가 만료되거나 취소되지 않았는지** 확인해주세요.")
                st.warning("2. **Google Cloud Console에서 해당 프로젝트의 결제(Billing)가 활성화**되어 있는지 확인해주세요.")
                st.text(f"상세 오류: {e}")

            except ResourceExhausted as e:
                st.error("📈 할당량 초과 오류 (HTTP 429): 사용 제한 초과")
                st.warning("👉 **해결책**: API 사용량이 너무 많습니다. 잠시 후 다시 시도하거나, 할당량을 늘려주세요.")
                st.text(f"상세 오류: {e}")

            except APIError as e:
                st.error(f"⚠️ API 호출 중 일반 오류가 발생했습니다. (Gemini 서버 문제 또는 요청 형식 오류)")
                st.warning("👉 **해결책**: API 키에 IP 주소나 HTTP 참조 등의 **제한(Restrictions)**이 걸려 있다면 임시적으로 제거해 보세요.")
                st.text(f"상세 오류: {e}")

            except Exception as e:
                st.exception(f"❌ 예상치 못한 오류가 발생했습니다:")
                st.text(f"Python 실행 오류: {e}")
