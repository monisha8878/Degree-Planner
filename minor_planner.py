import json

class MinorPlanner:
    def __init__(self, minors_json_path="minors.json", all_courses_path="data.json"):
        """Initialize minor planner with minors data AND full course catalog"""
        with open(minors_json_path, "r",encoding="utf-8") as f:
            self.minors_data = json.load(f)                   # Load minors data from minors.json into python dictionary
        self.minors = self.minors_data["minors"]
        
        # Load data.json to get prerequisites
        with open(all_courses_path, "r",encoding="utf-8") as f:
            self.all_courses = json.load(f)
    
    def list_available_minors(self):
        """List all available minors"""
        print("\n📚 Available Minors:")
        for i, minor in enumerate(self.minors, 1):  #Prints all available minors with their name and department, enumerate(self.minors, 1) numbers them starting from 1.
            print(f"{i}. {minor['name']} ({minor['department']})")
        return self.minors                          #self.minors is just the list of minors from the file.
    
    def get_minor_by_name(self, minor_name):
        """Get minor details by name"""
        for minor in self.minors:
            if minor["name"].lower() == minor_name.lower(): # Case-insensitive match, Does this minor’s name match what the user typed, ignoring case?
                return minor
        return None
    def get_minor_requirements(self, minor_name):
        minor = self.get_minor_by_name(minor_name)
        if not minor:
            return None

        # Handle core credits (number or range)
        core_required = 0
        if "core_credits_required" in minor:
            core_required = minor["core_credits_required"]
        elif "core_credits_required_range" in minor:
            # Take the minimum as default
            core_required = int(min(map(int, minor["core_credits_required_range"].split("-"))))

        elective_required = minor.get("elective_credits_required", 0)

        return {
            "core_required": core_required,
            "elective_required": elective_required,
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
        minor = self.get_minor_by_name(minor_name)          # Get the minor dictionary of minor_name if it exists
        if not minor:
            return None
        
        result = {'core': [], 'elective': []}               # Initialize result dictionary with empty lists for core and elective courses
        
        # Process core courses
        for course in minor.get("core_courses", []):         # Iterate over each core course in the minor
            code = course["code"]
            
            # Get full data from data.json if available
            if code in self.all_courses:
                full_course = self.all_courses[code].copy()   # Make a copy of the course dictionary from all_courses
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
            full_course["type"] = "Minor_Core"                # Tag course type as Minor_Core
            full_course["minor_name"] = minor_name            # Add minor name for reference
            result['core'].append(full_course)                  # Append to core courses list
        
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
            full_course["scheduled"] = False
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
        # Mark specific electives as already scheduled
        
        # Add non-overlapping courses to future semesters
        courses_added = 0
        
        for sem in range(current_semester, 9):
            if sem not in courses_left:                                     # Initialize semester if not present
                courses_left[sem] = []
            
            # Add core courses (non-overlapping only)
            for course in minor_courses['core']:
                if course["code"] in overlap_info['non_overlapping_codes']: # Only add if not overlapping
                    # Parse prereqs using your function
                    prereq_string = course.get("prereqs", "")
                    course["prereqs_parsed"] = parse_prereqs_func(prereq_string)
                    
                    # Add if not duplicate
                    if not any(c["code"] == course["code"] for c in courses_left[sem]):     # Check for duplicates before adding to semester
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
















