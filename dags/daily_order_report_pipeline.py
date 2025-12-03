from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.models import Variable
import sys
import os

# modules 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from order_tasks.fetch_orders import fetch_orders_from_s3
from order_tasks.aggregate_orders import aggregate_order_data
from order_tasks.generate_bedrock_report import generate_report_with_bedrock

default_args = {
    'owner': 'mwaa-demo',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='daily_order_report_pipeline',
    default_args=default_args,
    description='Daily order processing with Bedrock report generation',
    schedule_interval='@daily',
    catchup=False,
    tags=['demo', 'bedrock', 'orders'],
)
def daily_order_report_pipeline():
    
    @task
    def fetch_orders_task(**context):
        """S3에서 주문 데이터 가져오기"""
        # 고정 날짜 사용 (S3 파일과 매칭)
        target_date = "2025-12-01"
        return fetch_orders_from_s3(target_date)
    
    @task
    def aggregate_orders_task(orders_data: list, **context):
        """주문 데이터 집계"""
        return aggregate_order_data(orders_data)
    
    @task
    def generate_report_task(agg_result: dict, **context):
        """Bedrock을 사용한 리포트 생성"""
        # 고정 날짜 사용 (S3 파일과 매칭)
        target_date = "2025-12-01"
        return generate_report_with_bedrock(agg_result, target_date)
    
    # Task 의존성 정의
    orders = fetch_orders_task()
    aggregated = aggregate_orders_task(orders)
    report = generate_report_task(aggregated)
    
    orders >> aggregated >> report

dag_instance = daily_order_report_pipeline()