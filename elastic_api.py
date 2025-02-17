from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

# ✅ Elasticsearch 클라이언트 연결
client = Elasticsearch('http://localhost:9200')

def check_index_exists(index_name):
    """✅ 해당 인덱스가 존재하는지 확인하는 함수"""
    return client.indices.exists(index=index_name)

def create_index_if_not_exists(index_name, mapping=None):
    """✅ 인덱스가 존재하지 않으면 생성"""
    if not check_index_exists(index_name):
        client.indices.create(index=index_name, body=mapping if mapping else {})

def save_search_query(query_text):
    """✅ 사용자의 검색어를 `search_logs` 인덱스에 저장 (timestamp 포함)"""
    log_index = "search_logs"
    
    # ✅ `search_logs` 인덱스가 없으면 자동 생성
    create_index_if_not_exists(log_index)

    doc = {
        "query_text": query_text,
        "timestamp": datetime.utcnow()
    }
    client.index(index=log_index, body=doc)

def get_top_search_terms(size=10):
    """✅ 가장 많이 검색된 키워드 10개 반환"""
    log_index = "search_logs"
    
    if not check_index_exists(log_index):
        return []

    s = Search(index=log_index).using(client)
    s.aggs.bucket("top_searches", "terms", field="query_text.keyword", size=size)
    
    response = s.execute()

    if hasattr(response, "aggregations") and "top_searches" in response.aggregations:
        return [bucket.key for bucket in response.aggregations.top_searches.buckets]

    return []

def get_corrected_query(index_name, field_name, query_text):
    """✅ 오타 교정 (Auto-correct) 기능 - `completion` 필드 활용"""

    # ✅ `suggest` 필드 존재 여부 확인
    mapping = client.indices.get_mapping(index=index_name)
    if f"{field_name}.suggest" not in mapping[index_name]["mappings"]["properties"][field_name]["fields"]:
        print(f"⚠️ '{field_name}.suggest' 필드가 존재하지 않습니다. 원본 검색어 사용")
        return query_text  

    # ✅ `completion` 필드 기반 자동완성 검색
    suggest_query = {
        "suggest": {
            "text": query_text,
            "completion_suggest": {
                "completion": {
                    "field": f"{field_name}.suggest",
                    "size": 3,
                    "skip_duplicates": True
                }
            }
        }
    }

    response = client.search(index=index_name, body=suggest_query)

    if "suggest" in response and "completion_suggest" in response["suggest"]:
        suggestions = response["suggest"]["completion_suggest"]
        if suggestions and suggestions[0]["options"]:
            corrected_text = suggestions[0]["options"][0]["text"]
            print(f"🔄 자동 수정된 검색어: {corrected_text}")
            return corrected_text

    return query_text  
  # 수정된 검색어가 없으면 기존 검색어 반환

def search_nori_index_with_suggest(index_name, field_names, query_text):
    """
    ✅ 검색 개선:
    - `match_phrase_prefix` 추가 → "삼성" 입력 시 "삼성전자", "삼성바이오" 검색 가능
    - `fuzzy` 검색 추가 → 유사한 단어도 검색 가능
    - `wildcard`, `prefix` 유지 → 짧은 단어 검색 지원
    - `completion` 필드가 있을 경우 자동완성 검색 실행
    """
    if not check_index_exists(index_name):
        return {"error": f"Index '{index_name}'가 존재하지 않습니다. 데이터를 먼저 생성하세요!"}

    if isinstance(field_names, str):
        field_names = [field_names]

    # ✅ 오타 교정 수행
    corrected_text = get_corrected_query(index_name, field_names[0], query_text)
    if corrected_text != query_text:
        query_text = corrected_text

    # ✅ 검색 우선순위 적용
    query = Q("bool", should=[
        Q("match_phrase_prefix", **{field: query_text}) for field in field_names
    ], minimum_should_match=1)

    # ✅ `fuzzy` 검색 추가 (유사한 단어도 검색 가능)
    query |= Q("bool", should=[
        Q("match", **{field: {"query": query_text, "fuzziness": "AUTO"}}) for field in field_names
    ])

    # ✅ `wildcard` 추가 (짧은 단어 검색 가능)
    query |= Q("bool", should=[
        Q("wildcard", **{f"{field}.keyword": f"*{query_text}*"}) for field in field_names
    ])

    # ✅ `prefix` 검색 추가 (단어 시작 부분만 입력해도 검색 가능)
    query |= Q("bool", should=[
        Q("prefix", **{f"{field}.keyword": query_text}) for field in field_names
    ])

    # ✅ `completion` 기반 자동 완성 검색 추가 (존재하는 경우에만 실행)
    mapping = client.indices.get_mapping(index=index_name)
    if f"{field_names[0]}.suggest" in mapping[index_name]["mappings"]["properties"][field_names[0]]["fields"]:
        query |= Q("bool", should=[
            Q("match", **{f"{field}.suggest": query_text}) for field in field_names
        ])

    s = Search(index=index_name).using(client).query(query)
    response = s.execute()

    # ✅ 검색어 저장 (실시간 인기 검색어 추적)
    save_search_query(query_text)

    return response
