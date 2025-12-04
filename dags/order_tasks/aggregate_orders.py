import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

def aggregate_order_data(orders_data: list) -> dict:
    """
    주문 데이터를 집계하는 함수
    
    Args:
        orders_data: 주문 데이터 리스트
    
    Returns:
        dict: 집계된 데이터
    """
    try:
        logger.info(f"Aggregating {len(orders_data)} orders")
        
        # 집계 변수 초기화
        product_sales = defaultdict(lambda: {'revenue': 0, 'quantity': 0})
        store_sales = defaultdict(lambda: {'revenue': 0, 'orders': 0})
        category_sales = defaultdict(lambda: {'revenue': 0, 'quantity': 0})
        payment_methods = defaultdict(int)
        total_revenue = 0
        total_orders = len(orders_data)
        
        # 주문 데이터 집계
        for order in orders_data:
            order_amount = order.get('total_amount', 0)
            store_id = order.get('store_id', 'Unknown')
            payment_method = order.get('payment_method', 'Unknown')
            
            # 매장별 집계
            store_sales[store_id]['revenue'] += order_amount
            store_sales[store_id]['orders'] += 1
            
            # 결제 방법별 집계
            payment_methods[payment_method] += 1
            
            # 전체 매출
            total_revenue += order_amount
            
            # 상품별 집계 (items 배열 처리)
            for item in order.get('items', []):
                product_name = item.get('product_name', 'Unknown')
                category = item.get('category', 'Unknown')
                unit_price = item.get('unit_price', 0)
                quantity = item.get('quantity', 0)
                item_revenue = unit_price * quantity
                
                # 상품별 집계
                product_sales[product_name]['revenue'] += item_revenue
                product_sales[product_name]['quantity'] += quantity
                
                # 카테고리별 집계
                category_sales[category]['revenue'] += item_revenue
                category_sales[category]['quantity'] += quantity
        
        # 베스트셀러 TOP 3 (매출 기준)
        top_products = sorted(
            product_sales.items(), 
            key=lambda x: x[1]['revenue'], 
            reverse=True
        )[:3]
        
        # 결과 구성
        result = {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'product_sales': dict(product_sales),
            'store_sales': dict(store_sales),
            'category_sales': dict(category_sales),
            'payment_methods': dict(payment_methods),
            'top_products': top_products,
            'average_order_value': total_revenue / total_orders if total_orders > 0 else 0
        }
        
        logger.info(f"Aggregation completed. Total revenue: {total_revenue}")
        return result
        
    except Exception as e:
        logger.error(f"Error aggregating orders: {str(e)}")
        raise