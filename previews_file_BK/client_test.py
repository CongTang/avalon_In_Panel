import socket
import threading

nickname = input("Choose your nickname: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 1235))


def receive():
    while True:
        message = client.recv(1024).decode('utf-8')
        if message == 'NICK':
            client.send(nickname.encode('utf-8'))

        else:
            print(message)


def write():
    while True:
        message = input('')
        client.send('{}: {}'.format(nickname, message).encode('utf-8'))


receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

