from elasticsearch import Elasticsearch
from elasticsearch import helpers
import pandas as pd
import json

# ✅ Elasticsearch 클라이언트 연결
es = Elasticsearch("http://localhost:9200", http_compress=True)
index_name = "stock_info"

# ✅ 기존 인덱스 삭제 후 다시 생성
if es.indices.exists(index=index_name):
    es.options(ignore_status=[400, 404]).indices.delete(index=index_name)

# ✅ 수정된 매핑 설정 (`suggest` 필드를 별도 필드로 분리)
optimized_mapping = {
    "settings": {
        "analysis": {
            "tokenizer": {
                "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 10,
                    "token_chars": ["letter", "digit", "whitespace"]
                }
            },
            "analyzer": {
                "korean_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_tokenizer",
                    "filter": ["lowercase", "nori_readingform", "nori_number"]
                },
                "edge_ngram_analyzer": {
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase"]
                }
            }
        }
    },
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

# ✅ 인덱스 생성
es.options(ignore_status=[400]).indices.create(index=index_name, body=optimized_mapping)

# ✅ KRX 데이터 크롤링 및 변환
def get_stock_info():
    base_url = "http://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(base_url, header=0, encoding='euc-kr')[0]

    # ✅ 필드명 변환
    column_mapping = {
        '회사명': 'company',
        '업종': 'industry',
        '상장일': 'founded_date'
    }

    # ✅ 컬럼명 변경 후 필요한 컬럼만 유지
    df = df.rename(columns=column_mapping)
    df = df[list(column_mapping.values())]

    # ✅ 결측값 제거
    df = df.dropna(subset=["company", "industry"])

    # ✅ NaN 값을 None으로 변환
    df = df.where(pd.notna(df), None)

    # ✅ 날짜 변환 (설립일)
    if "founded_date" in df.columns:
        df['founded_date'] = pd.to_datetime(df['founded_date'], errors='coerce').dt.strftime('%Y-%m-%d')

    return df

# ✅ 데이터 삽입 (배치 크기: 500)
df = get_stock_info()

if df.empty:
    print("❌ 데이터가 없습니다.")
else:
    json_records = df.to_dict(orient='records')

    # ✅ `suggest` 필드 추가 (별도 필드 사용)
    for record in json_records:
        if isinstance(record.get("company"), str):
            record["company_suggest"] = {"input": [record["company"]]}
        if isinstance(record.get("industry"), str):
            record["industry_suggest"] = {"input": [record["industry"]]}

    batch_size = 500
    failed_documents = []  # ❌ 실패한 문서 목록 저장

    for i in range(0, len(json_records), batch_size):
        batch = json_records[i:i + batch_size]
        action_list = [{"_op_type": "index", "_index": index_name, "_source": row} for row in batch]

        try:
            success, failed = helpers.bulk(es, action_list, stats_only=False, raise_on_error=False)
            print(f"✅ {success}개 데이터 삽입 완료")

            # ❌ 실패한 문서 확인 및 저장
            if failed:
                print(f"❌ {failed}개 문서 삽입 실패! 상세 오류 메시지 확인 중...")
                for doc, error in zip(batch, failed):
                    failed_documents.append({"document": doc, "error": error})
                    print(f"❌ 삽입 실패 문서: {json.dumps(doc, ensure_ascii=False, indent=2)}")
                    print(f"📌 오류 내용: {json.dumps(error, ensure_ascii=False, indent=2)}")

        except Exception as e:
            print(f"❌ 데이터 삽입 중 예외 발생: {str(e)}")

    # ✅ 실패한 문서 저장
    if failed_documents:
        with open("failed_documents.json", "w", encoding="utf-8") as f:
            json.dump(failed_documents, f, ensure_ascii=False, indent=4)
        print("📁 실패한 문서를 `failed_documents.json` 파일로 저장했습니다.")
