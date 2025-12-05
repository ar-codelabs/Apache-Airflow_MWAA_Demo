from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.models import Variable

from order_tasks.fetch_orders import fetch_orders_from_s3
from order_tasks.aggregate_orders import aggregate_order_data
from order_tasks.generate_bedrock_report import generate_report_with_bedrock

default_args = {
    'owner': 'mwaa-demo',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='daily_order_report_pipeline',
    default_args=default_args,
    description='Daily order processing with Bedrock report generation',
    schedule='@daily',  # schedule_interval â†’ schedule
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['demo', 'bedrock', 'orders'],
)
def daily_order_report_pipeline():
    
    @task
    def fetch_orders_task(**context):
        """S3°"""
        target_date = "2025-12-01"
        return fetch_orders_from_s3(target_date)
    
    @task
    def aggregate_orders_task(orders_data: list, **context):
        """cal"""
        return aggregate_order_data(orders_data)
    
    @task
    def generate_report_task(agg_result: dict, **context):
        """Bedrock"""
        target_date = "2025-12-01"
        return generate_report_with_bedrock(agg_result, target_date)
    
    # Task 
    orders = fetch_orders_task()
    aggregated = aggregate_orders_task(orders)
    report = generate_report_task(aggregated)

# DAG 
dag_instance = daily_order_report_pipeline()
