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



user= UserData(name="Monisha",current_semester=2,EE_courses=selected_courses,completed_corecourses= ['ELL101',   'PYL101',   'MCP100','MTL100'])
user.print_summary(debug=True)
with open("EE_courses.json", "w") as f:
    json.dump(user.EE_courses, f, indent=4)
#making a list of remaining courses 
#       NEED TO CHANGE THIS CODE COMPLETELY - INCORRECT LOGIC 

# Replace the courses_left building section (lines 100-170) with this:

# Replace the courses_left building section with this:

courses_left = {}

# STEP 1: Build courses_left for all semesters normally
for sem, courses in selected_courses.items():
    target_sem = sem if sem >= user.current_semester else user.current_semester
    
    # ... your existing slot counting logic ...
    
    for course in courses:
        code = course["code"]
        ctype = course.get("type", "")
        
        # Skip completed courses
        if ctype == "Core" and code in user.completed_corecourses:
            continue
        if ctype.startswith("HUL") and code in user.completed_hul:
            continue
        if ctype == "DE" and code in user.completed_DE:
            continue
        
        # ... your HUL/DE filtering logic ...
        
        courses_left.setdefault(target_sem, []).append(course)

# STEP 2: Find all incomplete core courses from past semesters
incomplete_core_courses = []

for sem, courses in selected_courses.items():
    if sem < user.current_semester:  # Past semesters only
        for course in courses:
            code = course["code"]
            ctype = course.get("type", "")
            
            # If it's a core course and NOT completed, it's failed/incomplete
            if ctype == "Core" and code not in user.completed_corecourses:
                incomplete_core_courses.append(course)
                print(f"⚠️ Found incomplete/failed course: {code} from semester {sem}")

# STEP 3: Add these failed courses to ALL future semesters
for sem in range(user.current_semester, 9):  # Assuming max 8 semesters
    if sem not in courses_left:
        courses_left[sem] = []
    
    for failed_course in incomplete_core_courses:
        code = failed_course["code"]
        # Check if not already in this semester
        if not any(c["code"] == code for c in courses_left[sem]):
            courses_left[sem].append(failed_course)
            print(f"   → Added {code} as option to semester {sem}")

# Save courses_left
output_file = "courses_left.json"
with open(output_file, "w") as f:
    json.dump(courses_left, f, indent=4)

print(f"\n✅ Courses left saved to '{output_file}'")
print(f"\n📊 Summary:")
for sem in sorted(courses_left.keys()):
    hul_count = sum(1 for c in courses_left[sem] if c.get("type", "").startswith("HUL"))
    de_count = sum(1 for c in courses_left[sem] if c.get("type") == "DE")
    core_count = sum(1 for c in courses_left[sem] if c.get("type") == "Core")
    print(f"  Semester {sem}: {len(courses_left[sem])} courses ({core_count} Core, {hul_count} HUL, {de_count} DE)")
# Save courses_left

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
    model.Add(total_credits >= user.min_credits*CONFIG["CREDIT_SCALE"])
    model.Add(total_credits <= user.max_credits*CONFIG["CREDIT_SCALE"])

#total credits condition = should be 150 
# Total target credits for EE degree
#CONSTRAINT 2 
total_target_credits = CONFIG["TOTAL_TARGET_CREDITS"]


# Compute credits already completed
credits_done = 0
seen_courses = set()  # track codes we've already counted

for sem, courses in user.EE_courses.items():
    for course in courses:
        code = course["code"]
        if code in seen_courses:
            continue  # skip duplicates

        if code in user.completed_corecourses or code in user.completed_hul or code in user.completed_DE:
            credits_done += course["credits"]
            seen_courses.add(code)

print("Credits done:", credits_done)

            
# Save user.EE_courses to a file



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
            if (prereq_code in user.completed_corecourses or 
                prereq_code in user.completed_hul or 
                prereq_code in user.completed_DE):
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
                 

# Constraint 5 : every core course must be taken exactly once across the degree
for sem, courses in courses_left.items():
    for course in courses:
        if course.get("type") == "Core":
            code = course["code"]

            # gather this course across all semesters
            core_vars = [
                var for (s, c), var in course_vars.items() if c == code
            ]

            if core_vars:  # only if found
                model.Add(sum(core_vars) == 1)






















# RIGHT BEFORE solver.Solve(model)
print("\n🔍 PRE-SOLVE DEBUG:")
print(f"Semesters to plan: {sorted(courses_left.keys())}")
print(f"Total credits already done: {credits_done}")
print(f"Remaining credits needed: {remaining_target_credits / CONFIG['CREDIT_SCALE']}")
print(f"Min/Max credits per semester: {user.min_credits} - {user.max_credits}")

# Calculate if solution is even possible
num_future_sems = len(courses_left.keys())
min_possible = num_future_sems * user.min_credits
max_possible = num_future_sems * user.max_credits
target_needed = remaining_target_credits / CONFIG['CREDIT_SCALE']

print(f"\n📊 Feasibility check:")
print(f"  Future semesters: {num_future_sems}")
print(f"  Possible credit range: {min_possible} - {max_possible}")
print(f"  Target needed: {target_needed}")

if target_needed < min_possible:
    print("  ❌ PROBLEM: Need too few credits (will exceed minimum)")
elif target_needed > max_possible:
    print("  ❌ PROBLEM: Need too many credits (can't fit in max limits)")
else:
    print("  ✅ Feasible range")

# Count available courses per semester
for sem in sorted(courses_left.keys()):
    total_available = sum(c["credits"] for c in courses_left[sem])
    core_credits = sum(c["credits"] for c in courses_left[sem] if c.get("type") == "Core")
    print(f"\n  Sem {sem}: {len(courses_left[sem])} courses, {total_available} total credits")
    print(f"    Core (mandatory): {core_credits} credits")


#solver : dont edit below this line 
solver = cp_model.CpSolver()

status = solver.Solve(model)

# CHECK SOLVER STATUS
if status == cp_model.OPTIMAL:
    print("✅ Optimal solution found!")
elif status == cp_model.FEASIBLE:
    print("⚠️ Feasible solution found (not optimal)")
elif status == cp_model.INFEASIBLE:
    print("❌ NO SOLUTION EXISTS - Constraints are impossible to satisfy!")
    print("\n🔍 Debugging info:")
    print(f"  - Completed credits: {credits_done}")
    print(f"  - Remaining target: {remaining_target_credits / CONFIG['CREDIT_SCALE']}")
    print(f"  - User min/max per sem: {user.min_credits} - {user.max_credits}")
else:
    print(f"❓ Unknown status: {status}")

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


