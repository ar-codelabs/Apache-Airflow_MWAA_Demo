import boto3
import json
import logging
from airflow.models import Variable

logger = logging.getLogger(__name__)

def fetch_orders_from_s3(target_date: str) -> list:
    """
    S3에서 주문 데이터를 가져오는 함수
    
    Args:
        target_date: YYYY-MM-DD 형식의 날짜 (사용하지 않음, 고정 파일 사용)
    
    Returns:
        list: 주문 데이터 리스트
    """
    try:
        # Airflow Variables에서 S3 설정 가져오기
        bucket_name = Variable.get("MWAA_DAG_BUCKET", default_var="mwaa-demo-bucket-01")
        raw_prefix = Variable.get("RAW_DATA_PREFIX", default_var="raw/")
        sample_file = Variable.get("SAMPLE_ORDER_FILE", default_var="orders_20251201.json")
        
        # 고정 파일명 사용
        file_key = f"{raw_prefix}{sample_file}"
        
        logger.info(f"Fetching orders from s3://{bucket_name}/{file_key}")
        
        # S3 클라이언트 생성
        s3_client = boto3.client('s3')
        
        # 파일 다운로드
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        orders_data = json.loads(response['Body'].read().decode('utf-8'))
        
        logger.info(f"Successfully fetched {len(orders_data)} orders")
        return orders_data
        
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        # 테스트용 mock 데이터 반환
        return [
            {"order_id": "001", "product": "Product A", "amount": 100, "quantity": 2, "store": "Store 1"},
            {"order_id": "002", "product": "Product B", "amount": 150, "quantity": 1, "store": "Store 2"},
            {"order_id": "003", "product": "Product A", "amount": 100, "quantity": 3, "store": "Store 1"},
        ]