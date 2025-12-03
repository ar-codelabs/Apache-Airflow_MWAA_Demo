import boto3
import json
import logging
from airflow.models import Variable

logger = logging.getLogger(__name__)

def generate_report_with_bedrock(agg_result: dict, target_date: str) -> str:
    """
    Bedrock을 사용하여 리포트를 생성하는 함수
    
    Args:
        agg_result: 집계된 주문 데이터
        target_date: 대상 날짜
    
    Returns:
        str: 생성된 리포트 텍스트
    """
    try:
        # AWS 설정
        bedrock_region = Variable.get("BEDROCK_REGION", default_var="us-east-1")
        bucket_name = Variable.get("MWAA_DAG_BUCKET", default_var="mwaa-demo-bucket-01")
        report_prefix = Variable.get("REPORT_DATA_PREFIX", default_var="reports/")
        
        logger.info(f"Generating Bedrock report for {target_date}")
        
        # Bedrock 클라이언트 생성
        logger.info(f"Creating Bedrock client for region: {bedrock_region}")
        bedrock_client = boto3.client("bedrock-runtime", region_name=bedrock_region)
        logger.info("Bedrock client created successfully")
        
        # 프롬프트 생성 (지역별 매출 테이블 포함)
        prompt = f"""다음은 {target_date} 일일 매출 데이터입니다:

총 매출: {agg_result['total_revenue']:,}원
총 주문수: {agg_result['total_orders']}건
평균 주문금액: {agg_result['average_order_value']:,.0f}원

매장별 매출:
{_format_store_sales(agg_result['store_sales'])}

상품별 매출:
{_format_product_sales(agg_result['product_sales'])}

이 데이터를 기반으로 Markdown 형식의 매출 리포트를 작성해주세요. 다음 내용을 포함해주세요:
1. # 제목 (날짜 포함)
2. ## 매출 요약
3. ## 지역별 매출 현황 (매출 순서대로 정렬된 테이블)
4. ## 상품별 성과 (테이블)
5. ## 인사이트

전체 800자 이내로 작성해주세요."""

        # Bedrock 호출
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        logger.info("Calling Bedrock API...")
        import time
        start_time = time.time()
        
        try:
            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(body)
            )
            logger.info(f"Bedrock API call took {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Bedrock API call failed after {time.time() - start_time:.2f} seconds: {str(e)}")
            raise e
        
        logger.info("Bedrock API call successful, parsing response...")
        response_body = json.loads(response["body"].read())
        report_text = response_body["content"][0]["text"]
        logger.info(f"Generated report length: {len(report_text)} characters")
        
        logger.info("Bedrock report generated successfully")
        
        # S3에 리포트 저장
        _save_report_to_s3(report_text, target_date, bucket_name, report_prefix)
        
        return report_text
        
    except Exception as e:
        logger.error(f"Error generating Bedrock report: {str(e)}")
        # Fallback 리포트 생성
        fallback_report = _generate_fallback_report(agg_result, target_date)
        logger.info("Using fallback report due to Bedrock error")
        return fallback_report

def _format_product_sales(product_sales: dict) -> str:
    """상품별 매출 포맷팅"""
    lines = []
    for product, data in product_sales.items():
        lines.append(f"- {product}: {data['revenue']:,}원 ({data['quantity']}개)")
    return "\n".join(lines)

def _format_store_sales(store_sales: dict) -> str:
    """매장별 매출 포맷팅"""
    lines = []
    for store, data in store_sales.items():
        lines.append(f"- {store}: {data['revenue']:,}원 ({data['orders']}건)")
    return "\n".join(lines)

def _format_top_products(top_products: list) -> str:
    """베스트셀러 포맷팅"""
    lines = []
    for i, (product, data) in enumerate(top_products, 1):
        lines.append(f"{i}. {product}: {data['revenue']:,}원")
    return "\n".join(lines)

def _format_category_sales(category_sales: dict) -> str:
    """카테고리별 매출 포맷팅"""
    lines = []
    for category, data in category_sales.items():
        lines.append(f"- {category}: {data['revenue']:,}원 ({data['quantity']}개)")
    return "\n".join(lines)

def _format_payment_methods(payment_methods: dict) -> str:
    """결제 방법별 포맷팅"""
    lines = []
    for method, count in payment_methods.items():
        lines.append(f"- {method}: {count}건")
    return "\n".join(lines)

def _save_report_to_s3(report_text: str, target_date: str, bucket_name: str, report_prefix: str):
    """리포트를 S3에 저장"""
    try:
        s3_client = boto3.client('s3')
        date_str = target_date.replace('-', '')
        file_key = f"{report_prefix}report_{date_str}.md"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=report_text.encode('utf-8'),
            ContentType='text/plain; charset=utf-8'
        )
        
        logger.info(f"Report saved to s3://{bucket_name}/{file_key}")
        
    except Exception as e:
        logger.error(f"Error saving report to S3: {str(e)}")

def _generate_fallback_report(agg_result: dict, target_date: str) -> str:
    """Bedrock 실패 시 fallback 리포트 생성 (Markdown 형식)"""
    top_product = agg_result['top_products'][0] if agg_result['top_products'] else ('N/A', {'revenue': 0})
    return f"""# {target_date} 일일 매출 리포트

## 매출 요약
- **총 매출**: {agg_result['total_revenue']:,}원
- **총 주문수**: {agg_result['total_orders']}건
- **평균 주문금액**: {agg_result['average_order_value']:,.0f}원

## 베스트셀러 TOP 1
| 순위 | 상품명 | 매출액 |
|------|------|--------|
| 1 | {top_product[0]} | {top_product[1]['revenue']:,}원 |

## 인사이트
안정적인 매출 흐름을 보이고 있습니다.

> ⚠️ 이 리포트는 Bedrock 서비스 오류로 인해 기본 템플릿으로 생성되었습니다."""