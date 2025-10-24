'''
import re
from itertools import product

def parse_prereq_string(prereq_str):
    # remove brackets and spaces
    s = prereq_str.strip("[] ").replace(" ", "")
    
    # split by AND
    and_parts = re.split(r"and", s)
    
    # store all options
    options = []
    
    for part in and_parts:
        if "(" in part and ")" in part:
            # OR part
            or_part = part.strip("()").split("or")
            options.append(or_part)
        else:
            options.append([part])
    
    # generate all combinations of AND+OR
    prereq_lists = [list(p) for p in product(*options)]
    
    return prereq_lists

# Example
prereq_str = "[ELL101 and ELL202 and (ELL211 or ELL231)]"
print(parse_prereq_string(prereq_str))

'''

import re
from itertools import product

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
            or_content = re.search(r'\((.*?)\)', part).group(1)
            # Split by 'or' to get alternatives
            alternatives = re.split(r'\s+or\s+', or_content)
            # Extract course codes from each alternative
            or_group = [re.findall(course_pattern, alt)[0] for alt in alternatives if re.findall(course_pattern, alt)]
            if or_group:
                or_groups.append(or_group)
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


# Example usage and testing
if __name__ == "__main__":
    test_cases = [
        "[ELL101 and ELL202 and (ELL211 or ELL231)]",
        "[CSL101]",
        "[MTL100 and (CSL101 or ELL101)]",
        "[CSL201 and CSL202 and (CSL211 or CSL231 or CSL241)]",
        "[]",
        "[ELL101 and ELL102 and ELL103]"
    ]
    
    print("Testing prerequisite parser:\n")
    for test in test_cases:
        result = parse_prereqs(test)
        print(f"Input:  {test}")
        print(f"Output: {result}\n")



