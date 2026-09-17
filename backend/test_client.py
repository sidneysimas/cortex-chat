import sys, requests

message = sys.argv[1] if len(sys.argv) > 1 else "Qual é a capital da França?"
response = requests.post("http://127.0.0.1:8001/send_message", json={"message": message})
print(response.json())
