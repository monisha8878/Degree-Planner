from ortools.sat.python import cp_model
import json
import re
from itertools import product
from dept import Electrical   # import your dept dictionary
from user import UserData

CONFIG = {
    "TOTAL_TARGET_CREDITS": 150,   # EE degree requirement
    "CREDIT_SCALE": 10,            # scale to avoid floats in OR-Tools
    "MAX_HUL_PER_SEM": 2
}


def parse_prereqs(prereq_string):
    """
    Parse prerequisite string into list of lists.
    
    Input: "[ELL101 and ELL202 and (ELL211 or ELL231)]"
    Output: [['ELL101', 'ELL202', 'ELL211'], ['ELL101', 'ELL202', 'ELL231']]
    
    Logic:
    - 'and' means the course is required in all combinations
    - 'or' within parentheses creates alternative paths
    """
    if not prereq_string or prereq_string.strip() in ["", "[]", "None"]:
        return []
    
    # Remove outer brackets if present
    prereq_string = prereq_string.strip()
    if prereq_string.startswith('[') and prereq_string.endswith(']'):
        prereq_string = prereq_string[1:-1]
    
    # Find all course codes (alphanumeric pattern)
    course_pattern = r'[A-Z]{3}\d{3}'
    
    # Split by 'and' to get main required courses and OR groups
    and_parts = re.split(r'\s+and\s+', prereq_string)
    
    required_courses = []  # Courses that must be in all combinations
    or_groups = []  # Groups of alternatives
    
    for part in and_parts:
        part = part.strip()
        
        # Check if this part contains an OR group (has parentheses)
        if '(' in part and ')' in part:
            # Extract content within parentheses
            match = re.search(r'\((.*?)\)', part)
            if match:
                or_content = match.group(1)
                # Split by 'or' to get alternatives
                alternatives = re.split(r'\s+or\s+', or_content)
                # Extract course codes from each alternative
                or_group = [re.findall(course_pattern, alt)[0] for alt in alternatives if re.findall(course_pattern, alt)]
                if or_group:
                    or_groups.append(or_group)
            else:
                # Malformed parentheses, treat as regular courses
                courses = re.findall(course_pattern, part)
                required_courses.extend(courses)
        else:
            # This is a required course (no parentheses)
            courses = re.findall(course_pattern, part)
            required_courses.extend(courses)
    
    # Generate all combinations
    if not or_groups:
        # No OR groups, just return required courses
        return [required_courses] if required_courses else []
    
    # Create cartesian product of OR groups
    combinations = list(product(*or_groups))
    
    # Add required courses to each combination
    result = []
    for combo in combinations:
        combination = required_courses + list(combo)
        result.append(combination)
    
    return result


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
            # Parse prerequisites for core courses
            prereq_string = all_courses[course_code].get("prereqs", "")
            all_courses[course_code]["prereqs_parsed"] = parse_prereqs(prereq_string)
            all_courses[course_code]["type"] = "Core"
            selected_courses[sem_idx].append(all_courses[course_code])
            
        elif course_code == "DE":
            for de_code in Electrical["courses"]["DE"]:
                if de_code in all_courses:
                    # Parse prerequisites for DE courses
                    prereq_string = all_courses[de_code].get("prereqs", "")
                    all_courses[de_code]["prereqs_parsed"] = parse_prereqs(prereq_string)
                    all_courses[de_code]["type"] = "DE"
                    selected_courses[sem_idx].append(all_courses[de_code])

        elif course_code == "HUL2XX":         
            # dynamically find all courses whose code starts with HUL2
            for code, course_data in all_courses.items():
                if code.startswith("HUL2"):
                    # Parse prerequisites for HUL2XX courses
                    prereq_string = course_data.get("prereqs", "")
                    course_data["prereqs_parsed"] = parse_prereqs(prereq_string)
                    course_data["type"] = "HUL2XX"
                    selected_courses[sem_idx].append(course_data)
                    
        elif course_code == "HUL3XX":         
            # dynamically find all courses whose code starts with HUL3
            for code, course_data in all_courses.items():
                if code.startswith("HUL3"):
                    # Parse prerequisites for HUL3XX courses
                    prereq_string = course_data.get("prereqs", "")
                    course_data["prereqs_parsed"] = parse_prereqs(prereq_string)
                    course_data["type"] = "HUL3XX"
                    selected_courses[sem_idx].append(course_data)
        else:
            print(f"⚠ Warning: {course_code} not found in data.json")

# 3️⃣ Save to a JSON file (optional)
output_file = f"{dept_code}_courses_data.json"
with open(output_file, "w") as f:
    json.dump(selected_courses, f, indent=4)

print(f"✅ Department courses saved to '{output_file}'")
print(f"✅ Prerequisites parsed for all courses")



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

# CONSTRAINT 4: PREREQS SHOULD COME BEFORE ACTUAL COURSE 
for (sem, code), var in course_vars.items():
    course_data = None
    for c in courses_left[sem]:
        if c["code"] == code:
            course_data = c
            break
    
    if course_data is None:
        continue
    
    prereqs_parsed = course_data.get("prereqs_parsed", [])
    
    if not prereqs_parsed:
        continue
    
    # For each prerequisite path, check if all courses in that path are satisfied
    path_constraints = []
    
    for prereq_path in prereqs_parsed:
        # Check if this path can be satisfied
        prereq_vars_in_path = []
        all_prereqs_satisfiable = True
        
        for prereq_code in prereq_path:
            # Check if prereq is already completed
            if (prereq_code in user1.completed_corecourses or 
                prereq_code in user1.completed_hul or 
                prereq_code in user1.completed_DE):
                # Prereq already done - automatically satisfied
                continue
            
            # Check if prereq is in a future semester (can be scheduled)
            prereq_found = False
            for sem_p in range(1, sem):
                if (sem_p, prereq_code) in course_vars:
                    prereq_vars_in_path.append(course_vars[(sem_p, prereq_code)])
                    prereq_found = True
                    break
            
            if not prereq_found:
                # Prereq not completed and not available in earlier semesters
                all_prereqs_satisfiable = False
                break
        
        # If this path is satisfiable
        if all_prereqs_satisfiable:
            if len(prereq_vars_in_path) == 0:
                # All prereqs already completed - path is automatically satisfied
                path_var = model.NewBoolVar(f'path_{code}_sem{sem}_completed')
                model.Add(path_var == 1)  # Always satisfied
                path_constraints.append(path_var)
            elif len(prereq_vars_in_path) > 0:
                # Some prereqs need to be scheduled
                path_var = model.NewBoolVar(f'path_{code}_sem{sem}_{prereq_path}')
                
                # path_var == 1 iff all remaining prereqs are taken
                model.AddMinEquality(path_var, prereq_vars_in_path)
                
                path_constraints.append(path_var)
    
    # If taking this course, at least one path must be satisfied
    if path_constraints:
        model.Add(sum(path_constraints) >= var)
                 





























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


