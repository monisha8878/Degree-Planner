import json
from dept import Electrical

# Load data
with open("data.json", "r") as f:
    all_courses = json.load(f)

# Check semester 3 courses
print("Semester 3 recommended courses:")
sem3_courses = Electrical["recommended"][2]  # 0-indexed, so [2] is sem 3

for code in sem3_courses:
    if code in all_courses:
        course = all_courses[code]
        print(f"  ✅ {code}: {course['name']} ({course['credits']} cr)")
    else:
        print(f"  ❌ {code}: NOT FOUND in data.json")

print("\nChecking specific courses:")
for code in ["ELL205", "ELL211", "ELL225"]:
    if code in all_courses:
        print(f"  ✅ {code} exists in data.json")
    else:
        print(f"  ❌ {code} MISSING from data.json")
