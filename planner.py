from ortools.sat.python import cp_model

import json
from dept import Electrical   # import your dept dictionary
from user import UserData
CONFIG = {
    "TOTAL_TARGET_CREDITS": 150,   # EE degree requirement
    "CREDIT_SCALE": 10  ,          # scale to avoid floats in OR-Tools
    "MAX_HUL_PER_SEM" : 2

}






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
courses_left = {}
#making a list of remaining courses 


for sem, courses in selected_courses.items():
    remaining = []
    for course in courses:
        code = course["code"]
        course_type = course.get("type", "")
        
        # Skip if already completed
        if ((course_type == "Core" and code in getattr(user1, "completed_corecourses", [])) or
            (course_type.startswith("HUL") and code in getattr(user1, "completed_hul", [])) or
            (course_type == "DE" and code in getattr(user1, "completed_DE", []))):
            continue
        
        remaining.append(course)
    
    if remaining!=[]:
        courses_left[sem] = remaining

model = cp_model.CpModel()
course_vars = {}
# creation of boolean variables for all courses_sem Eg: ELL202_sem3 - yes or no 
# we create a dictionary course_var in which we add tuple:bool var as key:value pair e.g. (3, "ELL202"): BoolVar("ELL202_sem3"),
for sem, courses in courses_left.items():
    for course in courses:
        code = course["code"]
        course_vars[(sem, code)] = model.NewBoolVar(f"{code}_sem{sem}")

#courses which are left add them to satisfy credits 
# CONSTRAINT 1
for sem, courses in courses_left.items():
    total_credits = 0
    for course in courses:
        code = course["code"]
        total_credits += course_vars[(sem, code)] *int(course["credits"]*CONFIG["CREDIT_SCALE"]) #scale since model doesnt directly support float
    
    # Hard constraints for semester credits
    model.Add(total_credits >= user1.min_credits*CONFIG["CREDIT_SCALE"])
    model.Add(total_credits <= user1.max_credits*CONFIG["CREDIT_SCALE"])

#total credits condition = should be 150 
# Total target credits for EE degree
#CONSTRAINT 2 
total_target_credits = CONFIG["TOTAL_TARGET_CREDITS"]


# Compute credits already completed
credits_done = 0
for sem, courses in user1.EE_courses.items(): #EE_courses is the selected courses- means EE1 me net courses
    for course in courses:
        code = course["code"]
        # Only count if the student has completed it
        if code in user1.completed_corecourses or code in user1.completed_hul or code in user1.completed_DE:
            credits_done += course["credits"]


# Target credits for remaining semesters
remaining_target_credits = int((total_target_credits - credits_done) * CONFIG["CREDIT_SCALE"])  # scale by CONFIG["CREDIT_SCALE"]
#  Create one big sum across all remaining semesters and equate this sum to remaining credits 
total_remaining_credits = 0
for (sem, code), var in course_vars.items(): 

    # find course data again
    for course in courses_left[sem]:
        if course["code"] == code:
            total_remaining_credits += var * int(course["credits"] * CONFIG["CREDIT_SCALE"])
            break

#  Add constraint: all selected courses must exactly match remaining target credits
model.Add(total_remaining_credits == remaining_target_credits)

#CONSTRAINT 3 
# max of 2 hul courses per sem 
for sem, courses in courses_left.items():
    hul_vars = []
    for course in courses:
        code = course["code"]
        if course.get("type", "").startswith("HUL"):
            hul_vars.append(course_vars[(sem, code)])
    
    # Constraint: sum of HUL course selection <= MAX_HUL_PER_SEM
    if hul_vars:
        model.Add(sum(hul_vars) <= CONFIG["MAX_HUL_PER_SEM"])

#CONSTRAINT 4 
# PREREQS SHOULD COME BEFORE ACTUAL COURSE 
for (sem, code), var in course_vars.items(): 

    # find course data again
    for course in courses_left[sem]:
        course_data = None
        for c in courses_left[sem]:
            if c["code"] == code:
                course_data = c
                break
        if course_data is not  None and course_data.get("prereqs"):
             for prereq_code in course_data["prereqs"]:
                prereq_found = False
                for sem_p, courses in courses_left.items():
                    for c in courses:
                        if c["code"] == prereq_code:
                            prereq_var = course_vars[(sem_p, prereq_code)]
                            prereq_found = True
                            # Add constraint: if we take this course, we must take the prereq
                            model.Add(var <= prereq_var)
                            # Add constraint: prereq must happen in an earlier semester
                            model.Add(sem_p * prereq_var < sem * var)
                            break
                    if prereq_found:
                        break
                 






#solver : dont edit below this line 
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Create a dictionary to collect courses per semester
# Create a dictionary to collect courses per semester with full info
semester_plan = {}

for (sem, code), var in course_vars.items():
    if solver.Value(var):
        if sem not in semester_plan:
            semester_plan[sem] = []
        
        # Get full course info from courses_left
        for course in courses_left[sem]:
            if course["code"] == code:
                # Append the full course dictionary
                semester_plan[sem].append(course)
                break

# Print grouped by semester with all details
for sem in sorted(semester_plan.keys()):
    print(f"\n📘 Semester {sem}")
    total_credits = 0
    for course in semester_plan[sem]:
        code = course.get("code", "")
        name = course.get("name", "Unknown Course")
        credits = course.get("credits", 0)
        prereqs= course.get("prereqs",[])
        #desc = course.get("description", "No description available.")
        ctype = course.get("type", "Unknown")

        total_credits += credits
        print(f"  - {code}: {name} ({credits} credits, Type: {ctype}), Prerequisites: {prereqs}")
        #print(f"      {desc}")

    print(f"👉 Total Credits: {total_credits}")


