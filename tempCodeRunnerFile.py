course_vars = {}
# creation of boolean variables for all courses_sem Eg: ELL202_sem3 - yes or no 
# we create a dictionary course_var in which we add tuple:bool var as key:value pair e.g. (3, "ELL202"): BoolVar("ELL202_sem3"),


for course_code in set(c["code"] for sem_courses in courses_left.values() for c in sem_courses):
    # For each uncompleted course, allow it to be scheduled in any remaining semester
    for sem in range(user1.current_semester, user1.num_semesters + 1):
        course_vars[(sem, course_code)] = model.NewBoolVar(f"{course_code}_sem{sem}")
