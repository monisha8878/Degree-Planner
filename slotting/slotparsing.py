import pandas as pd

csv_file = "Courses_Offered.csv"

# Read CSV, skip first line (department header)
df = pd.read_csv(csv_file, skiprows=1)

# Strip column names and remove empty ones
df.columns = [col.strip() for col in df.columns]
df = df.loc[:, df.columns != '']

# Extract department from first line
with open(csv_file, encoding="utf-8") as f:
    first_line = f.readline().strip()
dept = first_line.split(":")[-1].strip()

# Add department column
df.insert(0, "Department", dept)

# Split course name and code
def split_course_name(course_str):
    if pd.isna(course_str):
        return pd.Series(["", ""])
    parts = course_str.rsplit("-", 1)
    if len(parts) == 2:
        return pd.Series([parts[0].strip(), parts[1].strip()])
    return pd.Series([course_str.strip(), ""])

df[["Course Name", "Course Code"]] = df["Course Name"].apply(split_course_name)

# Keep only relevant columns
df = df[["Course Code", "Course Name", "Slot Name"]]

# Remove rows with empty or null Course Code
df = df[df["Course Code"].notna() & (df["Course Code"] != "")]
df["Course Code"] = df["Course Code"].str.strip()

# Save to JSON
df.to_json("courses_clean.json", orient="records", indent=4)

print("JSON saved with", len(df), "courses")
