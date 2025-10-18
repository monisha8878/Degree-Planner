import json

class MinorPlanner:
    def __init__(self, minors_json_path="minors.json", all_courses_path="data.json"):
        """Initialize minor planner with minors data AND full course catalog"""
        with open(minors_json_path, "r") as f:
            self.minors_data = json.load(f)
        self.minors = self.minors_data["minors"]
        
        # Load data.json to get prerequisites
        with open(all_courses_path, "r") as f:
            self.all_courses = json.load(f)
    
    def list_available_minors(self):
        """List all available minors"""
        print("\n�� Available Minors:")
        for i, minor in enumerate(self.minors, 1):
            print(f"{i}. {minor['name']} ({minor['department']})")
        return self.minors
    
    def get_minor_by_name(self, minor_name):
        """Get minor details by name"""
        for minor in self.minors:
            if minor["name"].lower() == minor_name.lower():
                return minor
        return None
    
    def get_minor_requirements(self, minor_name):
        """Get credit requirements for a minor"""
        minor = self.get_minor_by_name(minor_name)
        if not minor:
            return None
        
        return {
            "core_required": minor.get("core_credits_required", 0),
            "elective_required": minor.get("elective_credits_required", 0),
            "total_required": 20,
            "oc_allowance": 10,
            "unique_required": 10,
            "note": minor.get("note", "")
        }
    
    def get_minor_courses_with_full_data(self, minor_name):
        """
        Get minor courses WITH prerequisites from data.json
        
        Returns: {
            'core': [course_objects_with_prereqs],
            'elective': [course_objects_with_prereqs]
        }
        """
        minor = self.get_minor_by_name(minor_name)
        if not minor:
            return None
        
        result = {'core': [], 'elective': []}
        
        # Process core courses
        for course in minor.get("core_courses", []):
            code = course["code"]
            
            # Get full data from data.json if available
            if code in self.all_courses:
                full_course = self.all_courses[code].copy()
            else:
                # Fallback to minors.json data
                full_course = {
                    "code": code,
                    "name": course.get("name", ""),
                    "credits": course.get("credits", 0),
                    "prereqs": "",
                    "hours": {
                        "lecture": course.get("lecture", 0),
                        "tutorial": course.get("tutorial", 0),
                        "practical": course.get("practical", 0)
                    }
                }
            
            # Tag as minor course
            full_course["type"] = "Minor_Core"
            full_course["minor_name"] = minor_name
            result['core'].append(full_course)
        
        # Process elective courses
        for course in minor.get("elective_courses", []):
            code = course["code"]
            
            if code in self.all_courses:
                full_course = self.all_courses[code].copy()
            else:
                full_course = {
                    "code": code,
                    "name": course.get("name", ""),
                    "credits": course.get("credits", 0),
                    "prereqs": "",
                    "hours": {
                        "lecture": course.get("lecture", 0),
                        "tutorial": course.get("tutorial", 0),
                        "practical": course.get("practical", 0)
                    }
                }
            
            full_course["type"] = "Minor_Elective"
            full_course["minor_name"] = minor_name
            result['elective'].append(full_course)
        
        return result
    
    def detect_overlap_with_program(self, minor_name, program_courses):
        """
        Detect branch-specific overlaps
        
        For EE/CS/MT: COL106 is Core/DE → overlaps → doesn't count
        For Chemical/Civil: COL106 not in program → doesn't overlap → counts
        
        Args:
            minor_name: Name of the minor
            program_courses: Dict of {sem: [courses]} from student's program
        
        Returns:
            {
                'overlapping': [course_codes],
                'overlapping_credits': total,
                'non_overlapping_codes': [codes]
            }
        """
        minor = self.get_minor_by_name(minor_name)
        if not minor:
            return None
        
        # Collect all program course codes (Core and DE only)
        program_codes = set()
        for sem, courses in program_courses.items():
            for course in courses:
                ctype = course.get("type", "")
                # Only Core and Department Electives count as overlaps
                if ctype in ["Core", "DE"]:
                    program_codes.add(course["code"])
        
        # Check minor courses for overlaps
        overlapping = []
        overlapping_credits = 0
        non_overlapping = []
        
        all_minor_courses = minor.get("core_courses", []) + minor.get("elective_courses", [])
        
        for course in all_minor_courses:
            code = course["code"]
            if code in program_codes:
                overlapping.append(code)
                overlapping_credits += course.get("credits", 0)
            else:
                non_overlapping.append(code)
        
        return {
            'overlapping': overlapping,
            'overlapping_credits': overlapping_credits,
            'non_overlapping_codes': non_overlapping
        }
    
    def add_minor_to_courses_left(self, minor_name, courses_left, program_courses, 
                                  current_semester, parse_prereqs_func):
        """
        Add minor courses to courses_left for planning
        - Excludes overlapping courses
        - Parses prereqs using your parse_prereqs function
        - Adds to all future semesters
        
        Returns:
            (updated_courses_left, overlap_info)
        """
        # Get minor courses with full data from data.json
        minor_courses = self.get_minor_courses_with_full_data(minor_name)
        if not minor_courses:
            print(f"⚠️ Minor '{minor_name}' not found")
            return courses_left, None
        
        # Detect branch-specific overlaps
        overlap_info = self.detect_overlap_with_program(minor_name, program_courses)
        
        if overlap_info and overlap_info['overlapping']:
            print(f"\n⚠️  Overlap Detection:")
            print(f"   {len(overlap_info['overlapping'])} courses overlap with your program:")
            for code in overlap_info['overlapping']:
                print(f"     ❌ {code} (already in your Core/DE)")
            print(f"   Overlapping credits: {overlap_info['overlapping_credits']}")
            print(f"   ⚠️  These DON'T count toward the 20-credit minor!")
        
        # Add non-overlapping courses to future semesters
        courses_added = 0
        
        for sem in range(current_semester, 9):
            if sem not in courses_left:
                courses_left[sem] = []
            
            # Add core courses (non-overlapping only)
            for course in minor_courses['core']:
                if course["code"] in overlap_info['non_overlapping_codes']:
                    # Parse prereqs using your function
                    prereq_string = course.get("prereqs", "")
                    course["prereqs_parsed"] = parse_prereqs_func(prereq_string)
                    
                    # Add if not duplicate
                    if not any(c["code"] == course["code"] for c in courses_left[sem]):
                        courses_left[sem].append(course)
                        if sem == current_semester:
                            courses_added += 1
            
            # Add elective courses (non-overlapping only)
            for course in minor_courses['elective']:
                if course["code"] in overlap_info['non_overlapping_codes']:
                    prereq_string = course.get("prereqs", "")
                    course["prereqs_parsed"] = parse_prereqs_func(prereq_string)
                    
                    if not any(c["code"] == course["code"] for c in courses_left[sem]):
                        courses_left[sem].append(course)
                        if sem == current_semester:
                            courses_added += 1
        
        print(f"\n✅ Added {courses_added} unique minor courses to semester {current_semester}")
        print(f"   (Available in all semesters {current_semester}-8)")
        
        return courses_left, overlap_info


# Test
if __name__ == "__main__":
    mp = MinorPlanner()
    mp.list_available_minors()
    
    # Test get_minor_requirements
    req = mp.get_minor_requirements("Computer Science")
    if req:
        print(f"\n✅ Testing get_minor_requirements:")
        print(f"   Core: {req['core_required']}")
        print(f"   Total: {req['total_required']}")
