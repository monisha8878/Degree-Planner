import pandas as pd

# Allowed slots
allowed_slots = set("ABHJCDEFMKL")

csv_files = ["Courses_Offered_1.csv", "Courses_Offered_2.csv"]
all_dfs = []

for csv_file in csv_files:
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
    df = df[["Department", "Course Code", "Course Name", "Slot Name"]]
    
    # Remove rows with empty or null Course Code
    df = df[df["Course Code"].notna() & (df["Course Code"] != "")]
    df["Course Code"] = df["Course Code"].str.strip()
    
    # ✅ Keep only courses with allowed slots
    df = df[df["Slot Name"].isin(allowed_slots)]
    
    all_dfs.append(df)

# Combine all files into a single DataFrame
combined_df = pd.concat(all_dfs, ignore_index=True)

# Save to JSON
combined_df.to_json("courses_clean.json", orient="records", indent=4)

print("JSON saved with", len(combined_df), "courses")
