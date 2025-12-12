import streamlit as st
from google import genai
from google.genai.errors import (
    PermissionDenied,
    ResourceExhausted,
    Unauthenticated,
    APIError
)
import time

# Streamlit 제목 설정
st.title("Gemini API 오류 진단 및 수정 애플리케이션")

# 1. st.secrets를 사용하여 API 키를 안전하게 불러옵니다.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("🚨 환경 변수 오류: Streamlit Secrets에서 'GEMINI_API_KEY'를 찾을 수 없습니다.")
    st.info("Streamlit Cloud 설정에서 API 키를 등록했는지 확인해주세요.")
    st.stop()

# 2. 불러온 API 키로 Gemini 클라이언트를 초기화합니다.
try:
    client = genai.Client(api_key=api_key)
    st.sidebar.success("✅ Gemini 클라이언트 초기화 완료.")
except Exception as e:
    st.error(f"클라이언트 초기화 중 예상치 못한 오류가 발생했습니다: {e}")
    st.stop()

# 3. 모델 설정 및 프롬프트
model = 'gemini-2.5-flash'
prompt = "저는 Gemini API 오류를 해결하는 중입니다. 이에 대해 격려하는 짧은 문장을 한국어로 작성해 주세요."
st.info(f"사용 모델: **{model}**")

if st.button("AI 응답 생성 및 오류 진단 테스트"):
    with st.spinner("응답을 생성하며 API 상태를 확인하는 중..."):
        try:
            # API 호출
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            st.subheader("🎉 AI 응답 성공")
            st.write(response.text)

        except (PermissionDenied, Unauthenticated) as e:
            # HTTP 401 (Unauthenticated) 또는 403 (PermissionDenied) 처리
            st.error("🛑 권한/인증 오류 (401/403): API 키가 유효하지 않거나, 해당 API에 대한 액세스 권한이 없습니다.")
            st.warning("👉 해결책: **API 키가 올바른지 다시 확인하고, Google Cloud Console에서 결제가 활성화되어 있는지 확인**해주세요.")
            st.text(f"상세 오류: {e}")
            
        except ResourceExhausted as e:
            # HTTP 429 (ResourceExhausted) 처리
            st.error("📈 할당량 초과 오류 (429): API 호출 한도(Quota)를 초과했습니다.")
            st.warning("👉 해결책: 잠시 후 다시 시도하거나, Google Cloud Console에서 할당량 설정을 확인해주세요.")
            st.text(f"상세 오류: {e}")

        except APIError as e:
            # 기타 일반적인 API 오류 (예: 잘못된 요청 형식, 서버 오류 등)
            st.error(f"⚠️ API 호출 중 일반 오류가 발생했습니다. 상세 오류: {e}")
            st.warning("👉 해결책: Streamlit Cloud에 배포한 후에도 이 오류가 계속된다면, API 키에 걸려있는 **IP 주소 제한**을 제거해 보세요.")
            
        except Exception as e:
            st.error(f"❌ 예상치 못한 Python/네트워크 오류가 발생했습니다: {e}")
            st.warning("👉 해결책: Streamlit Cloud의 로그를 확인하여 네트워크 연결 또는 라이브러리 설치 문제를 진단해주세요.")
