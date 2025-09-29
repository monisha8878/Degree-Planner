class UserData:
    def __init__(self, name="Student",dept= "EE1", current_semester=1,EE_courses=None, completed_corecourses=None,completed_hul=None,completed_DE=None, num_semesters=8, 
                 min_credits=15, max_credits=24, preferences=None):#preference is a dictionary that stores course vs interest for user 
        self.name = name
        self.dept= dept
        self.current_semester = current_semester
        self.num_semesters= num_semesters
        self.min_credits = min_credits
        self.max_credits = max_credits
        self.preferences = preferences if preferences else {} 
        self.EE_courses = EE_courses if EE_courses else {} 
        self.completed_hul=completed_hul if completed_hul else[]
        self.completed_DE=completed_DE if completed_DE else[]
         # Optional course preferences else use empty dictionary

        # Populate completed_courses
        if completed_corecourses is not None:
            # User provided completed courses
            self.completed_corecourses = completed_corecourses
        else:
            # Auto-fill from EE_courses for previous semesters
            self.completed_corecourses = []
            if EE_courses:
                for sem in range(1, current_semester):
                    for course in EE_courses.get(sem, []):
                        # Only add courses of type 'core'
                        if course.get("type") == "Core":
                            self.completed_corecourses.append(course["code"])


    def add_completed_corecourse(self, course_code):
        if course_code not in self.completed_corecourses:
            self.completed_corecourse.append(course_code)
    
    def remove_completed_corecourse(self, course_code):
        if course_code in self.completed_corecourses:
            self.completed_corecourses.remove(course_code)


    def add_completed_hulcourse(self, course_code):
        if course_code not in self.completed_hul:
            self.completed_hul.append(course_code)
    def remove_completed_hulcourse(self, course_code):
        if course_code in self.completed_hul:
            self.completed_hul.remove(course_code)

    def add_completed_DEcourse(self, course_code):
        if course_code not in self.completed_DE:
            self.completed_DE.append(course_code)
    
    def remove_completed_DEcourse(self, course_code):
        if course_code in self.completed_DE:
            self.completed_DE.remove(course_code)


   
    def update_preferences(self, course_code, score):
        self.preferences[course_code] = score

    def print_summary(self):
        all_completed=self.completed_corecourses+self.completed_DE+self.completed_hul
        print(f"Name: {self.name}")
        print(f"Current Semester: {self.current_semester}")
        print(f"Completed Courses: {all_completed}")
        print(f"Credit Limits: {self.min_credits}-{self.max_credits}")
        if self.preferences:
            print(f"Preferences: {self.preferences}")
    