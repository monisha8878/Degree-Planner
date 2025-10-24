import json

# Load the clean courses JSON (from CSV)
with open("courses_clean.json", "r", encoding="utf-8") as f:
    clean_courses = json.load(f)

# Load the existing detailed data.json
with open("../data.json", "r", encoding="utf-8") as f:
    detailed_courses = json.load(f)

# Update data.json directly
for course in clean_courses:
    code = course["Course Code"].strip()
    slot = course["Slot Name"]

    if code in detailed_courses:
        detailed_courses[code]["slot"] = slot  # add or update slot

# Save the updated data.json
with open("../data.json", "w", encoding="utf-8") as f:
    json.dump(detailed_courses, f, indent=4, ensure_ascii=False)

print(f"Updated {len(clean_courses)} courses in data.json with slot info!")
