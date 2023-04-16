import socket
import threading
import sys
sys.path.insert(0, '../lib')
from game_new import Avalon


host = '127.0.0.1'
port = 1235
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
clients = {}
nicknames = []


def broadcast(message):
    for nickname, client in clients.items():
        client.send(message)


def server_handle(avalon):
    while True:
        with threading.Lock():
            avalon.server_run()


def client_handle(nickname, avalon):
    input_ = None
    while True:
        try:
            with threading.Lock():
                msg = avalon.client_run(nickname, input_)
            if not msg:
                input_ = None
                continue
            clients[nickname].send(msg.encode('utf-8'))
            data = clients[nickname].recv(1024)
            nn, input_ = data.decode('utf-8').split(':')
            input_ = input_.strip()
            print(input_)

        except:
            clients[nickname].close()
            del clients[nickname]
            broadcast('{} left!'.format(nickname).encode('utf-8'))
            nicknames.remove(nickname)
            break


def admin_handle(admin):
    has_percival = False
    has_morgana = False
    has_mordred = False
    has_oberon = False
    has_lake_lady = False
    while True:
        _, msg = clients[admin].recv(1024).decode('utf-8').split(':')
        if msg.strip().startswith('CREATE'):
            if '-all' in msg:
                has_percival = True
                has_morgana = True
                has_mordred = True
                has_oberon = True
                has_lake_lady = True
            if '-percival' in msg:
                has_percival = True
            if '-morgana' in msg:
                has_morgana = True
            if '-mordred' in msg:
                has_mordred = True
            if '-oberon' in msg:
                has_oberon = True
            avalon = Avalon(nicknames,
                            has_percival=has_percival,
                            has_morgana=has_morgana,
                            has_mordred=has_mordred,
                            has_oberon=has_oberon,
                            has_lake_lady=has_lake_lady)

            for nn in nicknames:
                thread = threading.Thread(target=client_handle, args=(nn, avalon,))
                thread.start()

            thread = threading.Thread(target=server_handle, args=(avalon,))
            thread.start()

def receive():
    admin = ''
    while True:
        client, address = server.accept()
        print("Connected with {}".format(str(address)))

        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients[nickname] = client

        print("Nickname is {}".format(nickname))
        broadcast("{} joined!".format(nickname).encode('utf-8'))

        client.send('Connected to server!'.encode('utf-8'))

        if not admin:
            admin = nickname
            client.send('You are the admin!\n'.encode('utf-8'))
            thread = threading.Thread(target=admin_handle, args=(admin,))
            thread.start()


receive()
