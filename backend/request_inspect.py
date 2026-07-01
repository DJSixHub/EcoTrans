import urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:8000/api/metadata/routes') as resp:
        print(resp.status)
        print(resp.read().decode())
except Exception as e:
    import traceback
    traceback.print_exc()
