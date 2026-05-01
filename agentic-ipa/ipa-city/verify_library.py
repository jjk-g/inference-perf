import json
import os

with open('library/index.json', 'r') as f:
    index = json.load(f)

missing = []

def check_files(obj):
    if isinstance(obj, str):
        if not os.path.exists(obj):
            missing.append(obj)
    elif isinstance(obj, dict):
        for val in obj.values():
            check_files(val)

check_files(index)

if missing:
    print("Missing files:")
    for m in missing:
        print(f"  {m}")
else:
    print("All indexed files are present.")
