import socket
s=socket.socket()
s.settimeout(5)
s.connect(('127.0.0.1',8000))
print('ok')
