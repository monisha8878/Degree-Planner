class UserData:
    def __init__(self, name="Student", dept="EE1", current_semester=1, EE_courses=None, 
                  completed_corecourses=None, completed_hul=None, completed_DE=None, 
                 num_semesters=8, min_credits=15, max_credits=24, preferences=None,
                 completed_hul_sem=None, completed_DE_sem=None):
        """
        completed_hul_sem: dict mapping semester -> list of HUL courses completed in that sem
        completed_DE_sem: dict mapping semester -> list of DE courses completed in that sem
        """
        self.name = name
        self.dept = dept
        self.current_semester = current_semester
        self.num_semesters = num_semesters
        self.min_credits = min_credits
        self.max_credits = max_credits
        self.preferences = preferences if preferences else {} 
        self.EE_courses = EE_courses if EE_courses else {} 
        self.completed_hul = completed_hul if completed_hul else []
        self.completed_DE = completed_DE if completed_DE else []
        self.completed_hul_sem = completed_hul_sem if completed_hul_sem else {}
        self.completed_DE_sem = completed_DE_sem if completed_DE_sem else {}

        # Populate completed_courses
        if completed_corecourses is not None:
            self.completed_corecourses = completed_corecourses
        else:
            self.completed_corecourses = []
            if EE_courses:
                for sem in range(1, current_semester):
                    for course in EE_courses.get(sem, []):
                        if course.get("type") == "Core":
                            self.completed_corecourses.append(course["code"])

    def add_completed_corecourse(self, course_code):
        if course_code not in self.completed_corecourses:
            self.completed_corecourses.append(course_code)  # Fixed typo
    
    def remove_completed_corecourse(self, course_code):
        if course_code in self.completed_corecourses:
            self.completed_corecourses.remove(course_code)

    def add_completed_hulcourse(self, course_code, semester=None):
        """Add a completed HUL course, optionally tracking which semester"""
        if course_code not in self.completed_hul:
            self.completed_hul.append(course_code)
        if semester is not None:
            if semester not in self.completed_hul_sem:
                self.completed_hul_sem[semester] = []
            if course_code not in self.completed_hul_sem[semester]:
                self.completed_hul_sem[semester].append(course_code)
    
    def remove_completed_hulcourse(self, course_code):
        if course_code in self.completed_hul:
            self.completed_hul.remove(course_code)
        # Also remove from semester tracking
        for sem in self.completed_hul_sem:
            if course_code in self.completed_hul_sem[sem]:
                self.completed_hul_sem[sem].remove(course_code)

    def add_completed_DEcourse(self, course_code, semester=None):
        """Add a completed DE course, optionally tracking which semester"""
        if course_code not in self.completed_DE:
            self.completed_DE.append(course_code)
        if semester is not None:
            if semester not in self.completed_DE_sem:
                self.completed_DE_sem[semester] = []
            if course_code not in self.completed_DE_sem[semester]:
                self.completed_DE_sem[semester].append(course_code)
    
    def remove_completed_DEcourse(self, course_code):
        if course_code in self.completed_DE:
            self.completed_DE.remove(course_code)
        # Also remove from semester tracking
        for sem in self.completed_DE_sem:
            if course_code in self.completed_DE_sem[sem]:
                self.completed_DE_sem[sem].remove(course_code)

    def is_course_completed_in_past(self, course_code):
        """Check if a course was completed in a past semester"""
        all_completed = (self.completed_corecourses + 
                        self.completed_DE + 
                        self.completed_hul)
        return course_code in all_completed

    def get_available_courses_for_semester(self, semester):
        """
        Get available courses for a specific semester, filtering out:
        - Courses already completed in PAST semesters
        - But keeping HUL/DE available for FUTURE planning if not yet completed
        """
        if semester not in self.EE_courses:
            return []
        
        available = []
        for course in self.EE_courses[semester]:
            course_code = course["code"]
            course_type = course.get("type", "")
            
            # For past semesters: remove if completed
            if semester < self.current_semester:
                if course_type == "Core" and course_code in self.completed_corecourses:
                    continue
                if course_type == "HUL" and course_code in self.completed_hul:
                    continue
                if course_type == "DE" and course_code in self.completed_DE:
                    continue
            
            # For current and future semesters: 
            # - Remove Core courses if already completed
            # - Keep HUL/DE even if some were completed (user might need more)
            else:
                if course_type == "Core" and course_code in self.completed_corecourses:
                    continue
                # Don't remove HUL/DE from future - user might need multiple
            
            available.append(course)
        
        return available

    def update_preferences(self, course_code, score):
        self.preferences[course_code] = score

    def print_summary(self, debug=False):
        all_completed = (self.completed_corecourses + 
                        self.completed_DE + 
                        self.completed_hul)
        
        # Calculate total credits completed
        total_credits = 0
        found_courses = []
        not_found_courses = []
        
        if self.EE_courses:
            for completed_code in all_completed:
                found = False
                for sem, courses in self.EE_courses.items():
                    for course in courses:
                        if course["code"] == completed_code:
                            credits = course.get("credits", 0)
                            total_credits += credits
                            found_courses.append(f"{completed_code} ({credits} credits)")
                            found = True
                            break
                    if found:
                        break
                
                if not found:
                    not_found_courses.append(completed_code)
        
        print(f"Name: {self.name}")
        print(f"Current Semester: {self.current_semester}")
        print(f"Completed Courses: {len(all_completed)} courses")
        print(f"Total Credits Completed: {total_credits}")
        print(f"Completed HUL by semester: {self.completed_hul_sem}")
        print(f"Completed DE by semester: {self.completed_DE_sem}")
        print(f"Credit Limits: {self.min_credits}-{self.max_credits}")
        
        if debug:
            print(f"\n🔍 Debug Info:")
            print(f"Found courses with credits:")
            for fc in found_courses:
                print(f"  - {fc}")
            if not_found_courses:
                print(f"\n⚠️ Courses not found in EE_courses (not counted):")
                for nfc in not_found_courses:
                    print(f"  - {nfc}")
        
        if self.preferences:
            print(f"Preferences: {self.preferences}")