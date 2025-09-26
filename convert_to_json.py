import json
from data import courses 
with open("degree_plan.json", "w") as json_file:
    json.dump(courses, json_file, indent=4)

print("Dictionary successfully converted to degree_plan.json")