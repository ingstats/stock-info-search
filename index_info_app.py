import streamlit as st
import pandas as pd
import plotly.express as px
from elastic_api import search_nori_index_with_suggest, check_index_exists, get_top_search_terms, get_corrected_query

st.title("📊 기업 정보 검색")

index_name = "stock_info"  # ✅ 인덱스명 변경

# ✅ 검색 필드 선택 (회사명 또는 산업군)
search_field = st.sidebar.radio("검색할 필드를 선택하세요", ["회사명", "산업군"])
field_mapping = {"회사명": "company", "산업군": "industry"}  # ✅ 필드명 변환
selected_field = field_mapping[search_field]  # ✅ Elasticsearch에서 사용하는 필드명 적용

# ✅ 검색어 입력창
query_text = st.sidebar.text_input("🔎 검색어 입력", value="")
# ✅ 인기 검색어 추천 기능 추가
top_search_terms = get_top_search_terms()
if top_search_terms:
    st.sidebar.subheader("🔥 인기 검색어")
    for term in top_search_terms:
        if st.sidebar.button(term):
            query_text = term  

# ✅ 검색 버튼 추가
if st.sidebar.button("🔍 검색 실행"):
    if not query_text.strip():
        st.warning("❗ 검색어를 입력하세요!")
    elif not check_index_exists(index_name):
        st.error(f"❌ 인덱스 '{index_name}'가 존재하지 않습니다. 데이터를 먼저 생성하세요!")
    else:
        response = search_nori_index_with_suggest(index_name, [selected_field], query_text)

        if "error" in response:
            st.error(response["error"])
        elif response.hits.total.value > 0:
            source_data = [hit["_source"] for hit in response.to_dict()["hits"]["hits"]]
            df = pd.DataFrame(source_data)

            # ✅ 검색 결과 개수 표시
            st.metric(label="검색 결과 개수", value=len(df))

            # ✅ 검색 결과 차트 (산업군 분포)
            if "industry" in df.columns:
                fig = px.bar(df, x="industry", title="📈 검색된 산업군 분포")
                st.plotly_chart(fig)

            # ✅ 결과 표 출력
            st.dataframe(df)
        else:
            st.warning("🔍 검색 결과가 없습니다.")