import json
from dept import Electrical   # import your dept dictionary
from user import UserData

# 1️⃣ Load master data JSON
with open("data.json", "r") as f:
    all_courses = json.load(f)  # dict with course_code as key

# 2️⃣ Extract recommended courses semester-wise
recommended_courses = Electrical["recommended"]
dept_code = Electrical["code"]

selected_courses = {}

for sem_idx, course_list in enumerate(recommended_courses, start=1):
    selected_courses[sem_idx] = []
    for course_code in course_list:
        if course_code in all_courses:
            all_courses[course_code]["type"]="Core"
            selected_courses[sem_idx].append(all_courses[course_code])
        elif course_code== "DE":
            for de_code in Electrical["courses"]["DE"]:
                if de_code in all_courses:
                    all_courses[de_code]["type"]="DE"
                    selected_courses[sem_idx].append(all_courses[de_code])

        elif course_code=="HUL2XX":         
            # dynamically find all courses whose code starts with HUL2
            for code, course_data in all_courses.items():
                if code.startswith("HUL2"):
                    course_data["type"]="HUL2XX"
                    selected_courses[sem_idx].append(course_data)
        elif course_code=="HUL3XX":         
            # dynamically find all courses whose code starts with HUL2
            for code, course_data in all_courses.items():
                if code.startswith("HUL3"): #method in python to find string starts with what 
                    course_data["type"]="HUL3XX"
                    selected_courses[sem_idx].append(course_data)
        else:
            print(f"⚠ Warning: {course_code} not found in data.json")

# 3️⃣ Save to a JSON file (optional)
output_file = f"{dept_code}_courses_data.json"
with open(output_file, "w") as f:
    json.dump(selected_courses, f, indent=4)

print(f"✅ Department courses saved to '{output_file}'")

# 4️⃣ Now selected_courses can be used in OR-Tools
# Example: just print for verification
#print(json.dumps(selected_courses, indent=2))

user1= UserData(name="Monisha",current_semester=3,EE_courses=selected_courses)
user1.print_summary()