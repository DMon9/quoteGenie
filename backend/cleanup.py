import os

files_to_remove = [
    "test_quote_model.py",
    "test_import.py"
]

for f in files_to_remove:
    path = f"c:\\Users\\user\\quoteGenie\\backend\\{f}"
    if os.path.exists(path):
        os.remove(path)
        print(f"Removed {f}")
