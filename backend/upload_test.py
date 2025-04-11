import requests

# Change this if your app is hosted elsewhere
url = "http://localhost:8000/api/upload"
file_path = "testdb/testdb.csv"

with open(file_path, "rb") as f:
    files = {"file": ("testdb.csv", f, "text/csv")}
    response = requests.post(url, files=files)

print(response.status_code)
print(response.json())
