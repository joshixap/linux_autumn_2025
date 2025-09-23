from functools import reduce

users = [
    {"name": "Alice", "expenses": [100, 50, 75, 200]},
    {"name": "Bob", "expenses": [50, 75, 80, 100]},
    {"name": "Charlie", "expenses": [200, 300, 50, 150]},
    {"name": "David", "expenses": [100, 200, 300, 400]},
]

def total_expenses(expenses):
    return sum(expenses)

# общая сумма > 300
filtered_users = list(filter(lambda u: total_expenses(u["expenses"]) > 300, users))

# считаем общую сумму расходов для каждого
users_with_total = list(map(lambda u: {**u, "total_expenses": total_expenses(u["expenses"])}, filtered_users))

# сумма расходов всех отфильтрованных юзеров
overall_expenses = reduce(lambda acc, u: acc + u["total_expenses"], users_with_total, 0)

print("Filtered users with their total expenses:")
for u in users_with_total:
    print(f"{u['name']}: total expenses = {u['total_expenses']}")

print(f"Overall total expenses: {overall_expenses}")
