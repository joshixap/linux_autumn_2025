from functools import reduce

orders = [
    {"order_id": 1, "customer_id": 101, "amount": 150.0},
    {"order_id": 2, "customer_id": 102, "amount": 200.0},
    {"order_id": 3, "customer_id": 101, "amount": 75.0},
    {"order_id": 4, "customer_id": 103, "amount": 100.0},
    {"order_id": 5, "customer_id": 101, "amount": 50.0},
]

target_customer_id = 101

# фильтрация заказов для определённого клиента
filtered_orders = list(filter(lambda o: o["customer_id"] == target_customer_id, orders))

# подсчёт общей суммы заказов
total_amount = reduce(lambda acc, o: acc + o["amount"], filtered_orders, 0)

# подсчёт средней стоимости заказов
average_amount = total_amount / len(filtered_orders) if filtered_orders else 0

print(f"Orders for customer {target_customer_id}:")
for order in filtered_orders:
    print(f"Order ID: {order['order_id']}, Amount: {order['amount']}")

print(f"Total amount of orders: {total_amount}")
print(f"Average order amount: {average_amount}")
