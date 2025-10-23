from ortools.sat.python import cp_model
import json
import re
from itertools import product
from dept import Electrical   # import your dept dictionary
from user import UserData


from minor_planner import MinorPlanner

CONFIG = {
    "TOTAL_TARGET_CREDITS": 150,   # EE degree requirement
    "CREDIT_SCALE": 10,            # scale to avoid floats in OR-Tools
    "MAX_HUL_PER_SEM": 2,
    "MIN_HUL_CREDITS":15,
    "MIN_DE_CREDITS":15,

     # MINOR SETTINGS
    "MINOR_TOTAL_CREDITS": 20,          # total credits required for a minor
    "MINOR_OC_CREDITS": 10,             # minimum open choice credits for a minor
    "MINOR_UNIQUE_CREDITS": 10,         # minimum unique credits (not shared with core) for a minor(electives)
    "MAX_MINOR_PER_SEM": 2,             # max minor courses per semester
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
with open("data.json", "r",encoding="utf-8") as f:
    all_courses = json.load(f)  # dict with course_code as key

# 2️⃣ Extract recommended courses semester-wise
recommended_courses = Electrical["recommended"]
dept_code = Electrical["code"]

selected_courses = {}                           # dict to hold final selected courses semester-wise

for sem_idx, course_list in enumerate(recommended_courses, start=1):  
    selected_courses[sem_idx] = []              # initialize list for this semester
    for course_code in course_list:             #course_list is list of course codes for that sem that are recommended
        if course_code in all_courses:
            # Parse prerequisites for core courses
            prereq_string = all_courses[course_code].get("prereqs", "")                 #get prereq string from course data
            all_courses[course_code]["prereqs_parsed"] = parse_prereqs(prereq_string)   #parse and store prereqs
            all_courses[course_code]["type"] = "Core"                                   #recommended courses are core
            selected_courses[sem_idx].append(all_courses[course_code])                  #add full course data to selected courses semester-wise
            
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
with open(output_file, "w",encoding="utf-8") as f:
    json.dump(selected_courses, f, indent=4)

print(f"✅ Department courses saved to '{output_file}'")
print(f"✅ Prerequisites parsed for all courses")



"""user= UserData(name="Snehal",current_semester=3,EE_courses=selected_courses,completed_corecourses= ['ELL101',   'PYL101',   'MCP100','MTL100','COL100','PYP100','MCP101','APL100','CML101','MTL101','CMP100','ELP101'])
user.print_summary(debug=True)
with open("EE_courses.json", "w") as f:
    json.dump(user.EE_courses, f, indent=4)
#making a list of remaining courses """
# Corrected User Initialization in planner.py

user = UserData(
    name="Snehal",
    current_semester=5,  # You're STARTING semester 5 (not in it yet)
    EE_courses=selected_courses,
    
    # ALL courses completed in semesters 1-4
    completed_corecourses=[
        # Semester 1
        'ELL101', 'PYL101', 'MCP100', 'MTL100', 'COL100',
        'PYP100', 'MCP101',
        
        # Semester 2
        'APL100', 'CML101', 'MTL101', 'CMP100',
        
        # Semester 3
        'ELL205', 'ELL203', 'ELL201', 'COL106', 'ELL202', 'ELP101',
        
        # Semester 4
        'ELL211', 'ELL212', 'ELL225', 'ELP203', 'ELP212', 'ELP225',
        
        # Add any other CORE courses you've completed
    ],
    
    completed_hul=[
        'HUL260',  # Add any HUL courses completed in sem 1-4
    ],
    
    completed_DE=[
        # Add any DE courses completed
    ],
    
    completed_minor=[
        'COL100',  # This was in your major, counts for minor too
        'COL106',  # This was in your major, counts for minor too
    ],
    
    minor_type="CS",
    min_credits=18,
    max_credits=24
)

# Print to verify
print(f"\n{'='*70}")
print(f"USER PROFILE VERIFICATION")
print(f"{'='*70}")
print(f"Name: {user.name}")
print(f"Starting Semester: {user.current_semester}")
print(f"Completed Core Courses: {len(user.completed_corecourses)}")
print(f"Completed HUL: {len(user.completed_hul)}")
print(f"Completed DE: {len(user.completed_DE)}")
print(f"Completed Minor: {len(user.completed_minor)}")
print(f"Minor Type: {user.minor_type}")
print(f"{'='*70}\n")

user.print_summary(debug=True)

courses_left = {}

# Build set of all completed courses from all tracking methods
all_completed_codes = set(user.completed_corecourses)
all_completed_codes.update(user.completed_hul)
all_completed_codes.update(user.completed_DE)

# ============================================================
# BUILD courses_left DICTIONARY - CORRECTED VERSION
# ============================================================

print("\n" + "="*70)
print("📋 BUILDING courses_left")
print("="*70)

courses_left = {}

# Build set of all completed courses
all_completed_codes = set(user.completed_corecourses)
all_completed_codes.update(user.completed_hul)
all_completed_codes.update(user.completed_DE)

print(f"Current semester: {user.current_semester}")
print(f"Completed courses: {len(all_completed_codes)}")

# STEP 1: Add courses to ALL future semesters for flexibility
for sem, courses in selected_courses.items():
    for course in courses:
        code = course["code"]
        ctype = course.get("type", "")
        
        # Skip if already completed
        if code in all_completed_codes:
            continue
        
        # Add to ALL future semesters (gives solver flexibility)
        for future_sem in range(user.current_semester, 9):
            if future_sem not in courses_left:
                courses_left[future_sem] = []
            
            # Only add if not already present
            if not any(c["code"] == code for c in courses_left[future_sem]):
                courses_left[future_sem].append(course)

print(f"✅ All incomplete courses added to semesters {user.current_semester}-8")
print("="*70 + "\n")

# Save courses_left
output_file = "courses_left.json"
with open(output_file, "w",encoding="utf-8") as f:
    json.dump(courses_left, f, indent=4)

print(f"✅ Courses left saved to '{output_file}'")

# Count UNIQUE courses per type
unique_core = set()
unique_hul = set()
unique_de = set()

for sem, courses in courses_left.items():
    for c in courses:
        if c.get("type") == "Core":
            unique_core.add(c["code"])
        elif c.get("type", "").startswith("HUL"):
            unique_hul.add(c["code"])
        elif c.get("type") == "DE":
            unique_de.add(c["code"])

print(f"\n📊 Unique Courses Available:")
print(f"  Core: {len(unique_core)} courses")
print(f"  HUL: {len(unique_hul)} courses")
print(f"  DE: {len(unique_de)} courses")

print(f"\n  Per-semester breakdown:")
for sem in sorted(courses_left.keys()):
    hul_count = sum(1 for c in courses_left[sem] if c.get("type", "").startswith("HUL"))
    de_count = sum(1 for c in courses_left[sem] if c.get("type") == "DE")
    core_count = sum(1 for c in courses_left[sem] if c.get("type") == "Core")
    total_count = len(courses_left[sem])
    print(f"    Semester {sem}: {total_count} courses ({core_count} Core, {hul_count} HUL, {de_count} DE)")

"""# STEP 1: Build courses_left for all semesters
for sem, courses in selected_courses.items():
    target_sem = sem if sem >= user.current_semester else user.current_semester
    
    for course in courses:
        code = course["code"]
        ctype = course.get("type", "")
        
        # Skip if already completed (checks all types)
        if code in all_completed_codes:
            continue
        
        # Add to courses_left
        courses_left.setdefault(target_sem, []).append(course)

# STEP 2: Find incomplete core courses from past semesters
incomplete_core_courses = []

for sem, courses in selected_courses.items():
    if sem < user.current_semester:
        for course in courses:
            code = course["code"]
            ctype = course.get("type", "")
            
            if ctype == "Core" and code not in all_completed_codes:
                incomplete_core_courses.append(course)
                print(f"Found incomplete/failed course: {code} from semester {sem}")
# STEP 1: Build courses_left - Core courses go to ALL future semesters
for sem, courses in selected_courses.items():
    for course in courses:
        code = course["code"]
        ctype = course.get("type", "")
        
        # Skip if already completed
        if code in all_completed_codes:
            continue
        
        # For CORE courses: Add to ALL future semesters (flexible scheduling)
        if ctype == "Core":
            for future_sem in range(user.current_semester, 9):
                if future_sem not in courses_left:
                    courses_left[future_sem] = []
                
                # Only add if not already there
                if not any(c["code"] == code for c in courses_left[future_sem]):
                    courses_left[future_sem].append(course)
        
        # For electives (HUL, DE): Also add to all future semesters
        elif ctype in ["DE", "HUL2XX", "HUL3XX"]:
            for future_sem in range(user.current_semester, 9):
                if future_sem not in courses_left:
                    courses_left[future_sem] = []
                
                if not any(c["code"] == code for c in courses_left[future_sem]):
                    courses_left[future_sem].append(course)
        
        # For other course types from past semesters: put in current semester
        else:
            target_sem = sem if sem >= user.current_semester else user.current_semester
            courses_left.setdefault(target_sem, []).append(course)

print("✅ Core courses added to ALL future semesters (flexible scheduling)")


# STEP 3: Add failed courses to all future semesters
for sem in range(user.current_semester, 9):
    if sem not in courses_left:
        courses_left[sem] = []
    
    for failed_course in incomplete_core_courses:
        code = failed_course["code"]
        if not any(c["code"] == code for c in courses_left[sem]):
            courses_left[sem].append(failed_course)""" 
# Save courses_left
output_file = "courses_left.json"
with open(output_file, "w") as f:
    json.dump(courses_left, f, indent=4)


print(f"\n✅ Courses left saved to '{output_file}'")
print(f"\n📊 Summary:")

# Count UNIQUE courses per type
unique_core = set()
unique_hul = set()
unique_de = set()

for sem, courses in courses_left.items():
    for c in courses:
        if c.get("type") == "Core":
            unique_core.add(c["code"])
        elif c.get("type", "").startswith("HUL"):
            unique_hul.add(c["code"])
        elif c.get("type") == "DE":
            unique_de.add(c["code"])

print(f"  Unique courses available:")
print(f"    Core: {len(unique_core)} courses")
print(f"    HUL: {len(unique_hul)} courses")
print(f"    DE: {len(unique_de)} courses")

print(f"\n  Per-semester breakdown:")
for sem in sorted(courses_left.keys()):
    hul_count = sum(1 for c in courses_left[sem] if c.get("type", "").startswith("HUL"))
    de_count = sum(1 for c in courses_left[sem] if c.get("type") == "DE")
    core_count = sum(1 for c in courses_left[sem] if c.get("type") == "Core")
    total_count = len(courses_left[sem])
    print(f"    Semester {sem}: {total_count} courses ({core_count} Core, {hul_count} HUL, {de_count} DE)")
# Save courses_left
# ============================================================
# DIAGNOSTIC: Check Core Course Distribution
# ============================================================

print("\n" + "="*70)
print("🔍 DIAGNOSTIC: Core Course Credits Per Semester")
print("="*70)

for sem in sorted(courses_left.keys()):
    core_courses = [c for c in courses_left[sem] if c.get("type") == "Core"]
    core_credits = sum(c["credits"] for c in core_courses)
    
    print(f"\n  Semester {sem}:")
    print(f"     Core courses: {len(core_courses)}")
    print(f"     Core credits: {core_credits}")
    
    if core_credits > 24:
        print(f"     ⚠️  PROBLEM: Core alone exceeds max 24 credits!")
    elif core_credits > 20:
        print(f"     ⚠️  WARNING: Core takes {core_credits} credits, leaving only {24-core_credits} for electives")
    else:
        print(f"     ✅ OK: {24-core_credits} credits available for HUL/DE/Minor")
    
    if core_courses:
        print(f"     Courses:")
        for c in core_courses:
            print(f"       • {c['code']}: {c['name']} ({c['credits']} cr)")

print("="*70 + "\n")


# ============================================================
# MINOR INTEGRATION
# ============================================================

# Select a minor (or set to None)
SELECTED_MINOR = "Computer Science"  # Change this

if SELECTED_MINOR:
    print("\n" + "="*70)
    print(f"🎓 INTEGRATING MINOR: {SELECTED_MINOR}")
    print("="*70)
    
    # Initialize minor planner
    mp = MinorPlanner()
    
    # Get minor requirements
    minor_req = mp.get_minor_requirements(SELECTED_MINOR)               #ntegrates the minor courses into the remaining courses you need (courses_left).
    if minor_req:
        print(f"\n📋 Minor Requirements:")
        print(f"   Total: {minor_req['total_required']} credits")
        print(f"   Core: {minor_req['core_required']} credits")
        print(f"   Elective: {minor_req['elective_required']} credits")
        print(f"   OC allowance: {minor_req['oc_allowance']} credits")
        print(f"   Need unique: {minor_req['unique_required']} credits")
    
    # Add minor courses to courses_left
    courses_left, overlap_info = mp.add_minor_to_courses_left(
        SELECTED_MINOR,
        courses_left,
        selected_courses,  # Your EE program courses
        user.current_semester,
        parse_prereqs      # Your parse_prereqs function
    )
    
    # Save updated courses_left
    with open("courses_left.json", "w",encoding="utf-8") as f:
        json.dump(courses_left, f, indent=4)
    
    # Update user
    user.selected_minor = SELECTED_MINOR                #courses_left: Updated dictionary including minor courses
    user.overlap_info = overlap_info                     #overlap_info: Information about any overlapping courses currently being done and also in scope of minor  
    
    print("\n Updated Summary (with minor):")
    for sem in sorted(courses_left.keys()):
        core_count = sum(1 for c in courses_left[sem] if c.get("type") == "Core")
        hul_count = sum(1 for c in courses_left[sem] if c.get("type", "").startswith("HUL"))
        de_count = sum(1 for c in courses_left[sem] if c.get("type") == "DE")
        minor_count = sum(1 for c in courses_left[sem] if c.get("type", "").startswith("Minor"))
        
        print(f"  Sem {sem}: {len(courses_left[sem])} courses " +
              f"({core_count} Core, {hul_count} HUL, {de_count} DE, {minor_count} Minor)")
    
    print("="*70 + "\n")
else:
    mp = None
    minor_req = None
    overlap_info = None



# creation of boolean variables for all courses_sem Eg: ELL202_sem3 - yes or no 
# we create a dictionary course_var in which we add tuple:bool var as key:value pair e.g. (3, "ELL202"): BoolVar("ELL202_sem3"),
# ============================================================
# CONSTRAINT 1: SEMESTER CREDIT LIMITS WITH EXTENDED CREDITS
# Replace your existing CONSTRAINT 1 section with this entire block
# ============================================================

model = cp_model.CpModel()
course_vars = {}

# ============================================================
# CREATE ALL COURSE VARIABLES FIRST
# ============================================================
print("\n📋 Creating course variables...")
total_vars = 0
for sem, courses in courses_left.items():
    for course in courses:
        code = course["code"]
        course_vars[(sem, code)] = model.NewBoolVar(f"{code}_sem{sem}")
        total_vars += 1

print(f"✅ Created {total_vars} course variables across {len(courses_left)} semesters")
print(f"   Average {total_vars // len(courses_left)} variables per semester\n")

# ============================================================
# CONSTRAINT 1: SEMESTER CREDIT LIMITS WITH EXTENDED CREDITS
# ============================================================

print("="*70)
print("📋 CONSTRAINT 1: Semester Credit Limits (with Extended Credits)")
print("="*70)

extended_semester_vars = {}

for sem, courses in courses_left.items():
    total_credits = 0
    
    for course in courses:
        code = course["code"]
        total_credits += course_vars[(sem, code)] * int(course["credits"] * CONFIG["CREDIT_SCALE"])
    
    # Minimum credits constraint
    model.Add(total_credits >= user.min_credits * CONFIG["CREDIT_SCALE"])
    
    # Maximum credits with extended credit rules
    if sem > 2:
        # After semester 2, can use up to 26.5 credits
        model.Add(total_credits <= int(26.5 * CONFIG["CREDIT_SCALE"]))
        
        # Track if using extended credits
        extended_semester_vars[sem] = model.NewBoolVar(f"extended_sem{sem}")
        
        # If not using extended, max is 24
        model.Add(total_credits <= 24 * CONFIG["CREDIT_SCALE"]).OnlyEnforceIf(
            extended_semester_vars[sem].Not()
        )
    else:
        # Strict 24 limit for semesters 1-2
        model.Add(total_credits <= 24 * CONFIG["CREDIT_SCALE"])

# Maximum 2 semesters can use extended credits
if extended_semester_vars:
    model.Add(sum(extended_semester_vars.values()) <= 2)
    print(f"   ✅ Semester credit limits applied")
    print(f"   ✅ At most 2 semesters can exceed 24 credits (up to 26.5)")

print("="*70 + "\n")

# ============================================================
# CONSTRAINT 2 (UPDATED): Total Credits with Flexibility
# Also update your CONSTRAINT 2 to allow some flexibility
# ============================================================

print("📋 CONSTRAINT 2: Total Credit Target (with flexibility)")

total_target_credits = CONFIG["TOTAL_TARGET_CREDITS"]

# Compute credits already completed
credits_done = 0
seen_courses = set()

for sem, courses in user.EE_courses.items():
    for course in courses:
        code = course["code"]
        if code in seen_courses:
            continue

        if code in user.completed_corecourses or code in user.completed_hul or code in user.completed_DE:
            credits_done += course["credits"]
            seen_courses.add(code)

print(f"   Credits completed: {credits_done}")
print(f"   Total target: {total_target_credits}")

# Target credits for remaining semesters
remaining_target_credits = int((total_target_credits - credits_done) * CONFIG["CREDIT_SCALE"])

# Create sum across all remaining semesters
total_remaining_credits = 0
for (sem, code), var in course_vars.items():
    for course in courses_left[sem]:
        if course["code"] == code:
            total_remaining_credits += var * int(course["credits"] * CONFIG["CREDIT_SCALE"])
            break

# Allow small flexibility: 150-159 credits total
# This is because with discrete course credits, hitting exactly 150 might be impossible
model.Add(total_remaining_credits >= remaining_target_credits)
model.Add(total_remaining_credits <= remaining_target_credits + int(9 * CONFIG["CREDIT_SCALE"]))

print(f"   Remaining needed: {remaining_target_credits / CONFIG['CREDIT_SCALE']} credits")
print(f"   Allowed range: {remaining_target_credits / CONFIG['CREDIT_SCALE']}-{(remaining_target_credits + int(9 * CONFIG['CREDIT_SCALE'])) / CONFIG['CREDIT_SCALE']} credits")
print(f"   ✅ Some flexibility to account for discrete course credits\n")


# ============================================================
# VERIFICATION: Check feasibility with new limits
# ============================================================

print("🔍 Feasibility Check with Extended Credits:")

num_sems = len([s for s in courses_left.keys() if s > 2])  # Semesters after sem 2
num_extended_allowed = 2

# Calculate capacity
normal_sems = num_sems - num_extended_allowed  # Semesters with 24 limit
extended_sems = min(num_extended_allowed, num_sems)  # Semesters with 26.5 limit

min_possible = num_sems * user.min_credits
max_possible = (normal_sems * 24) + (extended_sems * 26.5)

target_needed = remaining_target_credits / CONFIG['CREDIT_SCALE']

print(f"   Semesters after sem 2: {num_sems}")
print(f"   Normal capacity: {normal_sems} × 24 = {normal_sems * 24}")
print(f"   Extended capacity: {extended_sems} × 26.5 = {extended_sems * 26.5}")
print(f"   Total capacity: {min_possible} - {max_possible} credits")
print(f"   Target needed: {target_needed} credits")

if target_needed > max_possible:
    print(f"   ❌ STILL INFEASIBLE: Need {target_needed - max_possible} more credits!")
    print(f"      → Consider: Reduce minor requirements or extend to more semesters")
else:
    print(f"   ✅ FEASIBLE with extended credits")

print()
"""for sem, courses in courses_left.items():
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
model.Add(total_remaining_credits >= remaining_target_credits)""" #sets the min credit limit instead of setting exact value like in previous lineconfig

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
# Constraint 5: Every course must be taken AT MOST once across the degree
# (Core courses exactly once, others at most once)

print("\n📋 Applying Constraint 5: Course Uniqueness")

# Collect all unique course codes across all semesters
all_course_codes = {course["code"] for sem in courses_left.values() for course in sem}

core_count = 0
other_count = 0

for code in all_course_codes:
    # Gather all variables for this course across all semesters
    course_vars_list = [var for (s, c), var in course_vars.items() if c == code]

    if len(course_vars_list) > 1:
        # Determine course type
        course_type = next(
            (course.get("type") for sem in courses_left.values() for course in sem if course["code"] == code),
            None
        )

        if course_type == "Core":
            model.Add(sum(course_vars_list) == 1)
            core_count += 1
        else:
            model.Add(sum(course_vars_list) <= 1)
            other_count += 1

print(f"✅ Applied uniqueness constraint to {core_count + other_count} courses "
      f"({core_count} core, {other_count} electives)\n")

"""for sem, courses in courses_left.items():
    for course in courses:
        if course.get("type") == "Core":
            code = course["code"]

            # gather this course across all semesters
            core_vars = [
                var for (s, c), var in course_vars.items() if c == code
            ]

            if core_vars:  # only if found
                model.Add(sum(core_vars) == 1)"""


# Add these constraints after CONSTRAINT 4 (prerequisites) and before CONSTRAINT 5 (core courses)

# CONSTRAINT 6: Minimum HUL credits = 15 across all semesters
min_hul_credits=CONFIG["MIN_HUL_CREDITS"]
hul_credit_vars = []
for (sem, code), var in course_vars.items():
    # Find course data
    course_data = None
    for c in courses_left[sem]:
        if c["code"] == code:
            course_data = c
            break
    
    if course_data and course_data.get("type", "").startswith("HUL"):
        # Add this course's scaled credits if selected
        hul_credit_vars.append(var * int(course_data["credits"] * CONFIG["CREDIT_SCALE"]))

# Account for already completed HUL credits
hul_credits_done = sum(
    course["credits"] for sem, courses in user.EE_courses.items()
    for course in courses
    if course["code"] in user.completed_hul
)
remaining_hul_needed = int((min_hul_credits - hul_credits_done) * CONFIG["CREDIT_SCALE"])

if hul_credit_vars and remaining_hul_needed > 0:
    model.Add(sum(hul_credit_vars) >= remaining_hul_needed)
    print(f"✅ Added HUL credit constraint: min {remaining_hul_needed / CONFIG['CREDIT_SCALE']} more credits needed (total 15)")
elif remaining_hul_needed <= 0:
    print(f"✅ HUL credits already satisfied: {hul_credits_done} completed")

# CONSTRAINT 7: Minimum DE credits = 10 across all semesters
min_de_credits=CONFIG["MIN_DE_CREDITS"]
de_credit_vars = []
for (sem, code), var in course_vars.items():
    # Find course data
    course_data = None
    for c in courses_left[sem]:
        if c["code"] == code:
            course_data = c
            break
    
    if course_data and course_data.get("type") == "DE":
        # Add this course's scaled credits if selected
        de_credit_vars.append(var * int(course_data["credits"] * CONFIG["CREDIT_SCALE"]))

# Account for already completed DE credits
de_credits_done = sum(
    course["credits"] for sem, courses in user.EE_courses.items()
    for course in courses
    if course["code"] in user.completed_DE
)
remaining_de_needed = int((min_de_credits - de_credits_done) * CONFIG["CREDIT_SCALE"])

if de_credit_vars and remaining_de_needed > 0:
    model.Add(sum(de_credit_vars) >= remaining_de_needed)
    print(f"✅ Added DE credit constraint: min {remaining_de_needed / CONFIG['CREDIT_SCALE']} more credits needed (total 10)")
elif remaining_de_needed <= 0:
    print(f"✅ DE credits already satisfied: {de_credits_done} completed")

# ============================================================
# MINOR CONSTRAINTS
# ============================================================

if SELECTED_MINOR and minor_req:
    print("\n" + "="*70)
    print("🎯 Adding Minor Constraints")
    print("="*70)
    
    # Collect minor course variables
    minor_core_vars = []
    minor_elec_vars = []
    minor_all_credits = []
    
    for (sem, code), var in course_vars.items():
        for c in courses_left[sem]:
            if c["code"] == code and c.get("type", "").startswith("Minor"):
                scaled_credits = var * int(c["credits"] * CONFIG["CREDIT_SCALE"])
                
                if c.get("type") == "Minor_Core":
                    minor_core_vars.append(var)
                    minor_all_credits.append(scaled_credits)
                elif c.get("type") == "Minor_Elective":
                    minor_elec_vars.append(var)
                    minor_all_credits.append(scaled_credits)
                break
    
    print(f"   Found {len(minor_core_vars)} core + {len(minor_elec_vars)} elective courses")
    
    if minor_all_credits:
        # CONSTRAINT: Minimum unique minor credits (10 credits)
        unique_required = CONFIG["MINOR_UNIQUE_CREDITS"]
        min_scaled = int(unique_required * CONFIG["CREDIT_SCALE"])
        
        model.Add(sum(minor_all_credits) >= min_scaled)
        print(f"   ✅ Minimum {unique_required} unique minor credits")
        print(f"      (+ {CONFIG['MINOR_OC_CREDITS']} from OC = {CONFIG['MINOR_TOTAL_CREDITS']} total)")
        
        # CONSTRAINT: Core requirements
        if minor_req["core_required"] > 0:
            core_credits = [
                var * int(c["credits"] * CONFIG["CREDIT_SCALE"])
                for (sem, code), var in course_vars.items()
                for c in courses_left[sem]
                if c["code"] == code and c.get("type") == "Minor_Core"
            ]
            
            if core_credits:
                core_scaled = int(minor_req["core_required"] * CONFIG["CREDIT_SCALE"])
                model.Add(sum(core_credits) >= core_scaled)
                print(f"   ✅ Minimum {minor_req['core_required']} core credits")
        
        # CONSTRAINT: Max minor courses per semester
        max_per_sem = CONFIG["MAX_MINOR_PER_SEM"]
        for sem in courses_left.keys():
            sem_minor_vars = [
                var for (s, code), var in course_vars.items()
                if s == sem
                for c in courses_left[sem]
                if c["code"] == code and c.get("type", "").startswith("Minor")
            ]
            if sem_minor_vars:
                model.Add(sum(sem_minor_vars) <= max_per_sem)
        
        print(f"   ✅ Max {max_per_sem} minor courses per semester")
    
    print("="*70)






















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










"""
Diagnostic tool to identify which constraint is causing infeasibility
Run this BEFORE the solver to check if your constraints are realistic
"""

def diagnose_constraints(user, courses_left, CONFIG, course_vars):
    """
    Analyze all constraints and identify potential conflicts
    """
    print("\n" + "="*70)
    print("🔬 CONSTRAINT DIAGNOSTICS")
    print("="*70)
    
    # Basic info
    credits_done = 36.0  # Your completed credits
    total_target = CONFIG["TOTAL_TARGET_CREDITS"]
    remaining_needed = total_target - credits_done
    
    num_sems = len(courses_left.keys())
    min_per_sem = user.min_credits
    max_per_sem = user.max_credits
    
    print(f"\n📊 Basic Setup:")
    print(f"   Semesters remaining: {num_sems}")
    print(f"   Credits needed: {remaining_needed}")
    print(f"   Per-semester range: {min_per_sem} - {max_per_sem}")
    print(f"   Total capacity: {num_sems * min_per_sem} - {num_sems * max_per_sem}")
    
    # Check 1: Is target achievable?
    min_possible = num_sems * min_per_sem
    max_possible = num_sems * max_per_sem
    
    print(f"\n✓ Check 1: Total Credits Feasibility")
    if remaining_needed < min_possible:
        print(f"   ❌ PROBLEM: Need {remaining_needed} but minimum is {min_possible}")
        print(f"      → You'll be forced to take more credits than needed")
        print(f"      → SOLUTION: Reduce min_credits or adjust target")
    elif remaining_needed > max_possible:
        print(f"   ❌ PROBLEM: Need {remaining_needed} but maximum is {max_possible}")
        print(f"      → Can't fit all required credits")
        print(f"      → SOLUTION: Increase max_credits or extend semesters")
    else:
        print(f"   ✅ FEASIBLE: {remaining_needed} fits in range {min_possible}-{max_possible}")
    
    # Check 2: Core courses
    print(f"\n✓ Check 2: Core Courses")
    core_by_sem = {}
    total_core_credits = 0
    
    for sem, courses in courses_left.items():
        core_courses = [c for c in courses if c.get("type") == "Core"]
        core_credits = sum(c["credits"] for c in core_courses)
        core_by_sem[sem] = core_credits
        total_core_credits += core_credits
    
    print(f"   Total mandatory core credits: {total_core_credits}")
    
    for sem in sorted(core_by_sem.keys()):
        credits = core_by_sem[sem]
        if credits > 0:
            status = "⚠️" if credits > max_per_sem else "✓"
            print(f"   {status} Sem {sem}: {credits} credits core (max: {max_per_sem})")
            if credits > max_per_sem:
                print(f"      ❌ PROBLEM: Core alone exceeds semester max!")
    
    # Check 3: HUL requirements
    print(f"\n✓ Check 3: HUL Requirements")
    hul_completed = 0  # You haven't completed any HUL
    hul_needed = CONFIG["MIN_HUL_CREDITS"] - hul_completed
    
    hul_available = 0
    for sem, courses in courses_left.items():
        hul_courses = [c for c in courses if c.get("type", "").startswith("HUL")]
        hul_available += len(hul_courses)
    
    print(f"   Need: {hul_needed} credits")
    print(f"   HUL courses available: {hul_available} courses")
    print(f"   Max HUL per semester: {CONFIG['MAX_HUL_PER_SEM']}")
    print(f"   Max possible: {num_sems * CONFIG['MAX_HUL_PER_SEM']} courses = ~{num_sems * CONFIG['MAX_HUL_PER_SEM'] * 4} credits")
    
    if hul_needed > num_sems * CONFIG['MAX_HUL_PER_SEM'] * 4:
        print(f"   ❌ PROBLEM: Can't take enough HUL courses!")
    else:
        print(f"   ✅ FEASIBLE")
    
    # Check 4: DE requirements
    print(f"\n✓ Check 4: DE Requirements")
    de_completed = 0
    de_needed = CONFIG["MIN_DE_CREDITS"] - de_completed
    
    de_available = 0
    for sem, courses in courses_left.items():
        de_courses = [c for c in courses if c.get("type") == "DE"]
        de_available += len(de_courses)
    
    print(f"   Need: {de_needed} credits")
    print(f"   DE courses available: {de_available} courses")
    
    if de_needed > 0 and de_available == 0:
        print(f"   ❌ PROBLEM: Need DE but none available!")
    else:
        print(f"   ✅ FEASIBLE")
    
    # Check 5: Minor requirements
    print(f"\n✓ Check 5: Minor Requirements")
    print(f"   Need: {CONFIG['MINOR_UNIQUE_CREDITS']} unique credits")
    print(f"   Max per semester: {CONFIG['MAX_MINOR_PER_SEM']}")
    
    minor_available = 0
    for sem, courses in courses_left.items():
        minor_courses = [c for c in courses if c.get("type", "").startswith("Minor")]
        minor_available += len(minor_courses)
    
    print(f"   Minor courses available: {minor_available} courses")
    
    max_minor_credits = num_sems * CONFIG['MAX_MINOR_PER_SEM'] * 4  # Assuming 4 credits per course
    if CONFIG['MINOR_UNIQUE_CREDITS'] > max_minor_credits:
        print(f"   ❌ PROBLEM: Can't take enough minor courses!")
    else:
        print(f"   ✅ FEASIBLE")
    
    # Check 6: Combined feasibility
    print(f"\n✓ Check 6: Combined Requirements")
    min_required = total_core_credits + hul_needed + de_needed + CONFIG['MINOR_UNIQUE_CREDITS']
    
    print(f"   Minimum to satisfy all:")
    print(f"      Core: {total_core_credits}")
    print(f"      HUL: {hul_needed}")
    print(f"      DE: {de_needed}")
    print(f"      Minor: {CONFIG['MINOR_UNIQUE_CREDITS']}")
    print(f"      Total: {min_required}")
    print(f"   Target: {remaining_needed}")
    
    if min_required > remaining_needed:
        print(f"   ❌ PROBLEM: Minimum requirements ({min_required}) exceed target ({remaining_needed})!")
        print(f"      Overage: {min_required - remaining_needed} credits")
    else:
        print(f"   ✅ FEASIBLE: Have {remaining_needed - min_required} credits of flexibility")
    
    # Check 7: Semester-by-semester feasibility
    print(f"\n✓ Check 7: Semester Feasibility")
    for sem in sorted(courses_left.keys()):
        core_cr = sum(c["credits"] for c in courses_left[sem] if c.get("type") == "Core")
        
        if core_cr > max_per_sem:
            print(f"   ❌ Sem {sem}: {core_cr} core credits > max {max_per_sem}")
        elif core_cr > min_per_sem:
            print(f"   ⚠️  Sem {sem}: {core_cr} core credits leaves only {max_per_sem - core_cr} for electives")
        else:
            print(f"   ✅ Sem {sem}: {core_cr} core credits, {min_per_sem - core_cr}-{max_per_sem - core_cr} for electives")
    
    # Summary
    print(f"\n" + "="*70)
    print("📋 SUMMARY")
    print("="*70)
    
    issues = []
    
    if remaining_needed < min_possible or remaining_needed > max_possible:
        issues.append("Total credit target infeasible")
    
    if any(core_by_sem[sem] > max_per_sem for sem in core_by_sem):
        issues.append("Core courses exceed semester max")
    
    if min_required > remaining_needed:
        issues.append("All requirements exceed total target")
    
    if issues:
        print("❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n💡 SUGGESTED FIXES:")
        print("   1. Increase user.max_credits from 24 to 26-28")
        print("   2. Reduce CONFIG['TOTAL_TARGET_CREDITS'] if overestimated")
        print("   3. Temporarily disable minor constraints to test")
        print("   4. Check if some core courses are duplicated")
    else:
        print("✅ All basic checks passed!")
        print("   If solver still fails, check prerequisites and course availability")
    
    print("="*70 + "\n")


# ============================================================
# HOW TO USE THIS DIAGNOSTIC TOOL
# ============================================================

# Add this line RIGHT BEFORE solver.Solve(model) in your main code:
# diagnose_constraints(user, courses_left, CONFIG, course_vars)
#solver : dont edit below this line 


#---------dont edit below this line ------------------
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
"""for sem in sorted(semester_plan.keys()):
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

    print(f"👉 Total Credits: {total_credits}")"""
# ============================================================
# ENHANCED OUTPUT WITH MINOR TRACKING
# ============================================================

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    minor_courses_taken = []
    
    # Collect minor courses
    for (sem, code), var in course_vars.items():
        if solver.Value(var):
            for course in courses_left[sem]:
                if course["code"] == code and course.get("type", "").startswith("Minor"):
                    minor_courses_taken.append({
                        "semester": sem,
                        "code": code,
                        "name": course["name"],
                        "credits": course["credits"],
                        "type": course.get("type")
                    })
                    break
    
    # Print semester-wise plan
    print("\n" + "="*70)
    print("📅 SEMESTER-WISE PLAN")
    print("="*70)
    
    for sem in sorted(semester_plan.keys()):
        print(f"\n{'='*70}")
        print(f"📘 SEMESTER {sem}")
        print(f"{'='*70}")
        
        # Categorize courses
        core = [c for c in semester_plan[sem] if c.get("type") == "Core"]
        de = [c for c in semester_plan[sem] if c.get("type") == "DE"]
        hul = [c for c in semester_plan[sem] if c.get("type", "").startswith("HUL")]
        minor_core = [c for c in semester_plan[sem] if c.get("type") == "Minor_Core"]
        minor_elec = [c for c in semester_plan[sem] if c.get("type") == "Minor_Elective"]
        
        # Print Core courses
        if core:
            print(f"\n  🔵 CORE COURSES:")
            for c in core:
                print(f"    • {c['code']}: {c['name']} ({c['credits']} cr)")
                if c.get('prereqs'):
                    print(f"      Prereqs: {c['prereqs']}")
        
        # Print Minor courses
        if minor_core or minor_elec:
            print(f"\n  🟢 MINOR COURSES ({SELECTED_MINOR}):")
            for c in minor_core:
                print(f"    • {c['code']}: {c['name']} ({c['credits']} cr) [CORE]")
                if c.get('prereqs'):
                    print(f"      Prereqs: {c['prereqs']}")
            for c in minor_elec:
                print(f"    • {c['code']}: {c['name']} ({c['credits']} cr) [ELECTIVE]")
                if c.get('prereqs'):
                    print(f"      Prereqs: {c['prereqs']}")
        
        # Print Department Electives
        if de:
            print(f"\n  🟡 DEPARTMENT ELECTIVES:")
            for c in de:
                print(f"    • {c['code']}: {c['name']} ({c['credits']} cr)")
        
        # Print Humanities
        if hul:
            print(f"\n  🟣 HUMANITIES:")
            for c in hul:
                print(f"    • {c['code']}: {c['name']} ({c['credits']} cr)")
        
        # Total credits for semester
        total = sum(c['credits'] for c in semester_plan[sem])
        print(f"\n  {'─'*66}")
        print(f"  📊 Total Credits: {total}")
        if total > 24:
            print(f"      ⚠️  Extended credits (normal max is 24)")
        print(f"  {'─'*66}")
    
    # Minor completion summary
    if SELECTED_MINOR and minor_courses_taken:
        print("\n" + "="*70)
        print(f"🎓 MINOR COMPLETION SUMMARY: {SELECTED_MINOR}")
        print("="*70)
        
        # Calculate credits
        core_cr = sum(c["credits"] for c in minor_courses_taken if c["type"] == "Minor_Core")
        elec_cr = sum(c["credits"] for c in minor_courses_taken if c["type"] == "Minor_Elective")
        total_scheduled = core_cr + elec_cr
        
        print(f"\n  📊 Credits Breakdown:")
        print(f"     Core scheduled: {core_cr} / {minor_req['core_required']} " +
              ("✅" if core_cr >= minor_req['core_required'] else "❌"))
        print(f"     Elective scheduled: {elec_cr} / {minor_req['elective_required']} " +
              ("✅" if elec_cr >= minor_req['elective_required'] else "❌"))
        print(f"     Unique credits scheduled: {total_scheduled}")
        print(f"     OC credits allowance: {CONFIG['MINOR_OC_CREDITS']}")
        print(f"     TOTAL: {total_scheduled} + {CONFIG['MINOR_OC_CREDITS']} = {total_scheduled + CONFIG['MINOR_OC_CREDITS']} / 20")
        
        # Show overlap info
        if overlap_info and overlap_info['overlapping']:
            print(f"\n  ⚠️  Note: {len(overlap_info['overlapping'])} courses excluded due to overlap:")
            for code in overlap_info['overlapping']:
                print(f"       - {code}")
        
        # Check completion
        if total_scheduled >= CONFIG['MINOR_UNIQUE_CREDITS']:
            print(f"\n  🎉 MINOR REQUIREMENTS SATISFIED!")
            print(f"     You have {total_scheduled} unique minor credits")
            print(f"     Plus {CONFIG['MINOR_OC_CREDITS']} from OC = {total_scheduled + CONFIG['MINOR_OC_CREDITS']} total")
        else:
            remaining = CONFIG['MINOR_UNIQUE_CREDITS'] - total_scheduled
            print(f"\n  ⚠️  Need {remaining} more unique credits")
        
        # Semester-wise breakdown
        print(f"\n  📅 Semester-wise Minor Courses:")
        for sem in sorted(set(c["semester"] for c in minor_courses_taken)):
            sem_courses = [c for c in minor_courses_taken if c["semester"] == sem]
            sem_credits = sum(c["credits"] for c in sem_courses)
            print(f"     Semester {sem} ({sem_credits} credits):")
            for c in sem_courses:
                label = "CORE" if c["type"] == "Minor_Core" else "ELECTIVE"
                print(f"       • {c['code']}: {c['name']} [{label}]")
        
        print("="*70)


