# -*- coding: utf-8 -*-
# Streamlit, Google Gemini API를 사용한 애플리케이션

import streamlit as st
from google import genai
# 가장 안정적인 임포트 방식을 사용합니다.
try:
    from google.genai import (
        PermissionDenied,
        ResourceExhausted,
        Unauthenticated,
        APIError
    )
except ImportError as e:
    # 패키지 버전 문제 발생 시 사용자에게 안내합니다.
    st.error(f"라이브러리 임포트 오류가 발생했습니다: {e}")
    st.warning("`google-genai` 패키지 버전이 너무 낮거나 올바르게 설치되지 않았을 수 있습니다. `requirements.txt` 파일을 확인하고 **google-genai>=0.14.0**으로 설정했는지 확인해주세요.")
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
    st.stop() # 키가 없으면 실행을 중지합니다.

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
        client = None # 클라이언트 초기화 실패 시 None으로 설정

# --- API 호출 및 오류 진단 ---
if client:
    # 3. 모델 설정 및 프롬프트
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
                # HTTP 401 (Unauthenticated) 또는 403 (PermissionDenied) 처리
                st.error("🛑 권한/인증 오류 (HTTP 401/403): API 키 문제")
                st.warning("1. **API 키가 만료되거나 취소되지 않았는지** 확인해주세요.")
                st.warning("2. **Google Cloud Console에서 해당 프로젝트의 결제(Billing)가 활성화**되어 있는지 확인해주세요. 결제 없이는 작동하지 않습니다.")
                st.text(f"상세 오류: {e}")

            except ResourceExhausted as e:
                # HTTP 429 (ResourceExhausted) 처리
                st.error("📈 할당량 초과 오류 (HTTP 429): 사용 제한 초과")
                st.warning("👉 **해결책**: API 사용량이 너무 많습니다. 잠시 후 다시 시도하거나, Google Cloud Console에서 할당량을 늘려주세요.")
                st.text(f"상세 오류: {e}")

            except APIError as e:
                # 기타 일반적인 API 오류
                st.error(f"⚠️ API 호출 중 일반 오류가 발생했습니다. (Gemini 서버 문제 또는 요청 형식 오류)")
                st.warning("👉 **해결책**: API 키에 IP 주소나 HTTP 참조 등의 **제한(Restrictions)**이 걸려 있다면 임시적으로 제거해 보세요. Streamlit Cloud의 서버 IP는 계속 변하기 때문입니다.")
                st.text(f"상세 오류: {e}")

            except Exception as e:
                st.exception(f"❌ 예상치 못한 오류가 발생했습니다:")
                st.text(f"Python 실행 오류: {e}")
