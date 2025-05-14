import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:5000/api"

def make_request(i):
    try:
        response = requests.get(URL)
        print(f"[{i+1}] Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{i+1}] ERRO: {e}")

# Disparar 15 requisições simultâneas (mais que o limite de 10)
with ThreadPoolExecutor(max_workers=15) as executor:
    for i in range(15):
        executor.submit(make_request, i)
