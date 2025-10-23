import json

# Open JSON file with UTF-8 encoding
with open("data.json", "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

print(data)
