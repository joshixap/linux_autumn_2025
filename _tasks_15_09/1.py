from functools import reduce

students = [
    {"name": "Alice", "age": 20, "grades": [85, 90, 88, 92]},
    {"name": "Bob", "age": 22, "grades": [78, 89, 76, 85]},
    {"name": "Charlie", "age": 21, "grades": [92, 95, 88, 94]}
]

target_age = None
# фильтрация по возрасту (target_age != None)
filtered_students = list(filter(lambda s: s["age"] == target_age if target_age is not None else True, students))

# средний балл для каждого
def average(grades):
    return sum(grades) / len(grades) if grades else 0

students_with_avg = list(map(lambda s: {**s, "avg_grade": average(s["grades"])}, filtered_students))

# средний балл по всем студентам
if students_with_avg:
    overall_avg = reduce(lambda acc, s: acc + s["avg_grade"], students_with_avg, 0) / len(students_with_avg)
else:
    overall_avg = 0

# макс средний балл
if students_with_avg:
    max_avg = max(map(lambda s: s["avg_grade"], students_with_avg))


# найти студента с максимальным средним баллом
top_students = list(filter(lambda s: s["avg_grade"] == max_avg, students_with_avg))

print("All students with their average grades:")
for s in students_with_avg:
    print(f"{s['name']} (age {s['age']}): average grade = {s['avg_grade']:.2f}")

print(f"\nAverage grade for all filtered students: {overall_avg:.2f}")

print("Students with the highest average grade:")
for s in top_students:
    print(f"{s['name']} (age {s['age']}): average grade = {s['avg_grade']:.2f}")
