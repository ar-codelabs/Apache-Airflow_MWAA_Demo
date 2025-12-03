# API Trigger 사용법

이 디렉토리에는 Airflow DAG를 외부에서 트리거하기 위한 HTTP 요청 예시가 포함되어 있습니다.

## 파일 설명

- `trigger_local.http`: 로컬 Airflow 환경용 API 호출
- `trigger_mwaa.http`: AWS MWAA 환경용 API 호출

## 로컬 환경 사용법

### 1. 기본 트리거
```bash
curl -X POST "http://localhost:8080/api/v1/dags/daily_order_report_pipeline/dagRuns" \
  -H "Authorization: Basic $(echo -n 'airflow:airflow' | base64)" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 2. 특정 날짜로 트리거
```bash
curl -X POST "http://localhost:8080/api/v1/dags/daily_order_report_pipeline/dagRuns" \
  -H "Authorization: Basic $(echo -n 'airflow:airflow' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "conf": {
      "date": "2025-01-01",
      "requested_by": "external-system"
    }
  }'
```

## MWAA 환경 사용법

### 1. CLI Token 생성
```bash
aws mwaa create-cli-token --name mwaa-demo-env --region us-east-1
```

### 2. DAG 트리거
```bash
# Token을 환경변수로 설정
export MWAA_CLI_TOKEN="your-cli-token-here"
export MWAA_WEBSERVER_URL="d2764627-a281-4cef-a44a-85f4f783121d-vpce.c68.airflow.us-east-1.on.aws"

curl -X POST "https://${MWAA_WEBSERVER_URL}/api/v1/dags/daily_order_report_pipeline/dagRuns" \
  -H "Authorization: Bearer ${MWAA_CLI_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "conf": {
      "date": "2025-01-01",
      "requested_by": "production-system"
    }
  }'
```

## 응답 예시

### 성공 응답
```json
{
  "dag_id": "daily_order_report_pipeline",
  "dag_run_id": "manual__2025-01-01T10:00:00+00:00",
  "execution_date": "2025-01-01T10:00:00+00:00",
  "state": "queued",
  "conf": {
    "date": "2025-01-01",
    "requested_by": "external-system"
  }
}
```

### 오류 응답
```json
{
  "detail": "DAG with dag_id: 'daily_order_report_pipeline' not found",
  "status": 404,
  "title": "DAG not found",
  "type": "about:blank"
}
```

## 주의사항

1. **인증**: 로컬 환경은 Basic Auth, MWAA는 CLI Token 사용
2. **권한**: MWAA CLI Token 생성을 위해서는 적절한 IAM 권한 필요
3. **네트워크**: MWAA 웹서버 URL은 VPC 내부에서만 접근 가능할 수 있음
4. **Rate Limiting**: API 호출 빈도 제한 고려