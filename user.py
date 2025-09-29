class UserData:
    def __init__(self, name="Student",dept= "EE1", current_semester=1,EE_courses=None, completed_courses=None, num_semesters=8, 
                 min_credits=15, max_credits=24, preferences=None):#preference is a dictionary that stores course vs interest for user 
        self.name = name
        self.dept= dept
        self.current_semester = current_semester
        self.num_semesters= num_semesters
        self.min_credits = min_credits
        self.max_credits = max_credits
        self.preferences = preferences if preferences else {} 
        self.EE_courses = EE_courses if EE_courses else {} 
         # Optional course preferences else use empty dictionary

        # Populate completed_courses
        if completed_courses is not None:
            # User provided completed courses
            self.completed_courses = completed_courses
        else:
            # Auto-fill from EE_courses for previous semesters
            self.completed_courses = []
            if EE_courses:
                for sem in range(1, current_semester):
                    for course in EE_courses.get(sem, []):
                        # Only add courses of type 'core'
                        if course.get("type") == "Core":
                            self.completed_courses.append(course["code"])


    def add_completed_course(self, course_code):
        if course_code not in self.completed_courses:
            self.completed_courses.append(course_code)

    def remove_completed_course(self, course_code):
        if course_code in self.completed_courses:
            self.completed_courses.remove(course_code)

    def update_preferences(self, course_code, score):
        self.preferences[course_code] = score

    def print_summary(self):
        print(f"Name: {self.name}")
        print(f"Current Semester: {self.current_semester}")
        print(f"Completed Courses: {self.completed_courses}")
        print(f"Credit Limits: {self.min_credits}-{self.max_credits}")
        if self.preferences:
            print(f"Preferences: {self.preferences}")
    