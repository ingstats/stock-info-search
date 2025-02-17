# 📊 기업 정보 검색 시스템

이 프로젝트는 **Elasticsearch**와 **Streamlit**을 활용하여 기업 정보를 검색하는 시스템입니다. 사용자는 기업명 또는 산업군을 검색하여 관련 정보를 조회할 수 있으며, 인기 검색어 추천 및 오타 자동 교정 기능을 제공합니다.

---

## 🚀 주요 기능

### ✅ 1. 기업 정보 검색
- 기업명 또는 산업군을 입력하여 관련 기업 정보를 검색할 수 있습니다.
- 검색어 자동완성 및 오타 교정 기능이 포함되어 있습니다.

### ✅ 2. 인기 검색어 추천
- 사용자의 검색 로그를 저장하고, 가장 많이 검색된 키워드를 추천합니다.

### ✅ 3. 검색 결과 시각화
- 검색된 기업의 산업군 분포를 **Plotly** 그래프를 사용하여 시각적으로 표현합니다.

### ✅ 4. Elasticsearch 기반 검색 최적화
- **Nori 형태소 분석기**와 **edge n-gram 분석기**를 적용하여 한국어 검색 성능을 최적화하였습니다.
- **completion 필드**를 활용하여 검색어 자동완성을 지원합니다.

---

## 📁 프로젝트 구조

```
📂 streamlit-search
├── elastic_api.py       # Elasticsearch API 및 검색 기능
├── elastic_bulk.py      # 데이터 크롤링 및 Elasticsearch 인덱싱
├── index_info_app.py    # Streamlit 기반 UI 및 검색 기능
└── README.md            # 프로젝트 설명서 (현재 파일)
```

---

## 🛠️ 기술 스택

- **Backend**: Elasticsearch, Python
- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **Visualization**: Plotly

---

## 🔧 실행 방법

### 1️⃣ Elasticsearch 실행
먼저 **Elasticsearch 서버**를 실행해야 합니다.

```bash
# Elasticsearch 실행 (Docker 사용 시)
docker run -d -p 9200:9200 -e "discovery.type=single-node" elasticsearch:7.17.5
```

또는 직접 설치한 경우 실행합니다.

```bash
# Elasticsearch 실행 (Linux)
./bin/elasticsearch
```

### 2️⃣ 데이터 크롤링 및 인덱싱

KRX 기업 정보를 크롤링하고 Elasticsearch에 저장합니다.

```bash
python elastic_bulk.py
```

### 3️⃣ Streamlit 실행

아래 명령어를 실행하여 **Streamlit 웹 애플리케이션**을 실행합니다.

```bash
streamlit run index_info_app.py
```

이후 **로컬 웹 브라우저**에서 실행된 웹 애플리케이션을 확인할 수 있습니다.

---

## 🏗️ Elasticsearch 데이터 구조

Elasticsearch의 인덱스(`stock_info`)는 다음과 같은 구조로 정의됩니다.

### ✅ 매핑 (Mappings)

```json
{
  "mappings": {
    "properties": {
      "company": {
        "type": "text",
        "analyzer": "edge_ngram_analyzer",
        "search_analyzer": "korean_analyzer",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "company_suggest": {
        "type": "completion"
      },
      "industry": {
        "type": "text",
        "analyzer": "edge_ngram_analyzer",
        "search_analyzer": "korean_analyzer",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "industry_suggest": {
        "type": "completion"
      },
      "founded_date": {"type": "date", "format": "yyyy-MM-dd"}
    }
  }
}
```

---

## 🧐 문제 해결 (Troubleshooting)

### ❌ `document_parsing_exception` 오류 해결

```json
"reason": "failed to parse field [company] of type [text] in document with id ..."
```

✅ **원인**: `company.suggest` 필드가 `company` 필드에 포함되어 발생한 오류.
✅ **해결 방법**: `company.suggest`를 별도의 `company_suggest` 필드로 분리.

### ❌ `no mapping found for field [company.suggest]` 오류 해결

✅ **원인**: Elasticsearch 매핑에서 `company.suggest` 필드가 존재하지 않음.
✅ **해결 방법**: `company_suggest` 필드를 `completion` 타입으로 추가.

```json
"company_suggest": {"type": "completion"}
```

---

## 📌 참고 문서

- **Elasticsearch 공식 문서**: [https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- **Streamlit 공식 문서**: [https://docs.streamlit.io/](https://docs.streamlit.io/)
- **KRX 기업 정보**: [http://kind.krx.co.kr/](http://kind.krx.co.kr/)

---

## 👨‍💻 개발자

- **이름**: ingstats
- **프로젝트 기여 방법**: Pull Request를 통해 기능 추가 가능

✅ **문의 사항**이 있으면 언제든지 연락 주세요! 😊

