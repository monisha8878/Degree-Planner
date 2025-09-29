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
                 