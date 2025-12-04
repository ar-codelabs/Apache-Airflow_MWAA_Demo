# 🚀 MWAA + Bedrock 기반 데모 파이프라인

AWS MWAA(Managed Workflows for Apache Airflow)와 Amazon Bedrock을 활용한 일일 주문 데이터 처리 및 AI 리포트 생성 파이프라인입니다.

## 📋 프로젝트 개요

매일 S3에 저장된 주문 데이터를 처리하여 집계하고, Amazon Bedrock의 LLM을 사용해 자연어 요약 리포트를 생성하는 데모 파이프라인입니다.

### 🎯 주요 기능

- **S3 데이터 처리**: RAW 주문 JSON 파일 읽기
- **데이터 집계**: 상품별/매장별/카테고리별 매출 및 주문수 집계
- **AI 리포트 생성**: Bedrock Claude를 사용한 마크다운 형식의 상세 분석 리포트
- **자동화**: 일일 스케줄 실행 및 외부 API 트리거 지원
- **CI/CD**: GitHub Actions를 통한 자동 배포

## 🏗️ 아키텍처

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   S3 RAW    │───▶│     MWAA     │───▶│   Bedrock LLM   │
│ Order Data  │    │   Pipeline   │    │  Report Gen     │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  S3 Reports  │
                   │   (.md)      │
                   └──────────────┘
```

## 📊 DAG 구성

### DAG ID: `daily_order_report_pipeline`

#### Task 흐름
1. **fetch_orders_task**: S3에서 주문 데이터 읽기
2. **aggregate_orders_task**: 데이터 집계 처리 (상품별/매장별/카테고리별)
3. **generate_report_task**: Bedrock으로 마크다운 형식 AI 리포트 생성

#### 데이터 흐름
```
raw/orders_20251201.json → 집계 처리 → Bedrock 분석 → reports/report_20251201.md
```

## 📁 디렉토리 구조

```
.
├── .github/workflows/              # GitHub Actions
│   └── github-actions-sync-to-s3.yml
├── dags/                           # Airflow DAG 파일
│   └── daily_order_report_pipeline.py                     
│   └── order_tasks/                # Python 모듈
│       ├── __init__.py
│       ├── fetch_orders.py         # S3 데이터 읽기
│       ├── aggregate_orders.py     # 데이터 집계
│       └── generate_bedrock_report.py  # Bedrock 리포트 생성
├── docker/                         # 커스텀 Docker 이미지
│   ├── Dockerfile.mwaa_custom
│   └── requirements.txt
├── local/                          # 로컬 개발 환경
│   ├── docker-compose.yml
│   └── .env                        # 환경 변수 (템플릿)
├── api-trigger/                    # API 트리거 예시
│   ├── trigger_local.http
│   ├── trigger_mwaa.http
│   └── README_API_TRIGGER.md
├── sample_data_orders_20251201.json # 샘플 데이터
├── README.md
└── .gitignore
```

## 🔧 환경 설정

### 필수 AWS 리소스

| 리소스 | 설명 |
|--------|------|
| **MWAA 환경** | Apache Airflow 관리형 서비스 |
| **S3 버킷** | DAG 파일 및 데이터 저장용 |
| **ECR 리포지토리** | 커스텀 Docker 이미지 저장소 (선택사항) |
| **Bedrock 액세스** | Claude 3 Sonnet 모델 활성화 |
| **IAM 권한** | S3, Bedrock, ECR 접근 권한 |

### 환경 변수 설정

`local/.env` 파일을 복사하여 실제 값으로 수정:

```bash
# AWS 설정
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-here
AWS_SECRET_ACCESS_KEY=your-secret-key-here
MWAA_DAG_BUCKET=your-s3-bucket-name
RAW_DATA_PREFIX=raw/
REPORT_DATA_PREFIX=reports/
BEDROCK_REGION=us-east-1
SAMPLE_ORDER_FILE=orders_20251201.json
```

## 🐳 로컬 개발 환경 실행

### 1. 환경 준비
```bash
cd local/
export AIRFLOW_UID=$(id -u)
```

### 2. 환경 변수 설정
`local/.env` 파일에서 실제 AWS 자격증명으로 수정

### 3. Airflow 실행
```bash
docker compose up -d
```

### 4. 웹 UI 접속
- URL: http://localhost:8080
- 계정: `airflow` / `airflow`

### 5. 샘플 데이터 S3 업로드
```bash
aws s3 cp sample_data_orders_20251201.json s3://your-bucket-name/raw/orders_20251201.json
```

### 6. DAG 테스트
1. 웹 UI에서 `daily_order_report_pipeline` DAG 확인
2. DAG 활성화 (토글 스위치)
3. 수동 실행 또는 API 트리거 사용

### 7. 환경 정리
```bash
docker compose down -v
```

## 🚀 GitHub Actions CI/CD 설정

### 1. GitHub Secrets 설정

Repository → Settings → Secrets and variables → Actions에서 추가:

```
AWS_ACCESS_KEY_ID: your-access-key
AWS_SECRET_ACCESS_KEY: your-secret-key
MWAA_DAG_BUCKET: your-s3-bucket-name
```

### 2. 자동 배포 흐름
1. `main` 브랜치에 push
2. GitHub Actions 자동 실행
3. `dags/`디렉토리를 S3에 동기화
4. MWAA가 자동으로 변경사항 반영

## 🔌 API 트리거 사용법

### 로컬 환경
```bash
curl -X POST "http://localhost:8080/api/v1/dags/daily_order_report_pipeline/dagRuns" \
  -H "Authorization: Basic $(echo -n 'airflow:airflow' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"conf": {"date": "2025-12-01"}}'
```

### MWAA 환경
```bash
# CLI Token 생성
aws mwaa create-cli-token --name your-mwaa-env --region us-east-1

# DAG 트리거
curl -X POST "https://your-mwaa-webserver-url/api/v1/dags/daily_order_report_pipeline/dagRuns" \
  -H "Authorization: Bearer your-cli-token" \
  -H "Content-Type: application/json" \
  -d '{"conf": {"date": "2025-12-01"}}'
```

## 🤖 Bedrock 리포트 생성

### 사용 모델
- **모델**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **출력 형식**: Markdown (.md)

### 생성되는 리포트 내용
- 📊 매출 요약 (총 매출, 주문수, 평균 주문금액)
- 🏪 지역별 매출 현황 (매출 순서대로 정렬된 테이블)
- 📦 상품별 성과 (테이블 형식)
- 💳 결제 트렌드 분석
- 💡 비즈니스 인사이트 및 개선 제안

### Fallback 처리
Bedrock 호출 실패 시 기본 마크다운 템플릿으로 리포트 생성

## 🛠️ 트러블슈팅

### 일반적인 문제

#### 1. Bedrock 권한 오류
IAM 사용자/역할에 다음 권한 추가:
- `bedrock:InvokeModel`
- `bedrock:GetFoundationModel`

#### 2. S3 접근 오류
IAM 사용자/역할에 다음 권한 추가:
- `s3:GetObject`
- `s3:PutObject`
- `s3:ListBucket`

#### 3. Docker 메모리 부족
Docker Desktop에서 메모리 할당 증가 (최소 4GB)

### 로그 확인
- **로컬**: Airflow 웹 UI → DAG → Task → Logs
- **MWAA**: CloudWatch Logs에서 확인

## 📊 샘플 데이터 형식

```json
[
  {
    "order_id": "ORD-20250101-0001",
    "order_date": "2025-01-01T09:12:00+09:00",
    "customer_id": "CUST-001",
    "store_id": "STORE-SEOUL-01",
    "items": [
      {
        "product_id": "PROD-1001",
        "product_name": "테스트 상품 A",
        "category": "FOOD",
        "unit_price": 12000,
        "quantity": 2
      }
    ],
    "payment_method": "CARD",
    "total_amount": 27000,
    "currency": "KRW",
    "status": "PAID"
  }
]
```

## 🏗️ 커스텀 Docker 이미지 (선택사항)

### 1. 이미지 빌드
```bash
cd docker/
docker build -f Dockerfile.mwaa_custom -t mwaa-demo-custom .
```

### 2. ECR에 푸시
```bash
# ECR 로그인
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

# 태그 및 푸시
docker tag mwaa-demo-custom:latest your-account.dkr.ecr.us-east-1.amazonaws.com/mwaa-demo-custom-image:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/mwaa-demo-custom-image:latest
```


---

## 📝 라이선스

이 프로젝트는 데모 및 학습 목적으로 제작되었습니다.
