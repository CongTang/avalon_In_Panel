import sys
import threading
import random
sys.path.insert(0, '../lib')
from game import Avalon
dummy_names = ['Allan', 'Bob', 'Curtis', 'Danny', 'Evan', 'Frank', 'Gibson', 'Harry', 'Issac', 'Jake']


def server_handle(avalon):
    with threading.Lock():
        avalon.server_run()
    return


def client_handle(nickname, avalon):
    open(f'../log/{nickname}', 'w').close()
    input_ = None
    while True:
        with threading.Lock():
            msg = avalon.client_run(nickname, input_)
        if not msg:
            input_ = None
            continue
        with open(f'../log/{nickname}', 'a') as record:
            record.write(f'{msg} \n')

        random_input = gen_random_input()
        input_ = random.choice(random_input)
        with open(f'../log/{nickname}', 'a') as record:
            record.write(f'{input_} \n')
        if avalon.end_game:
            return


def gen_random_input():
    random_input = list()

    for i in range(10):
        random_input.append(str(i))

    for _ in range(5):
        l = list()
        for _ in range(2):
            l.append(random.choice([str(i) for i in list(range(5)) if str(i) not in l]))
        random_input.append(' '.join(l))

    for _ in range(5):
        l = list()
        for _ in range(3):
            l.append(random.choice([str(i) for i in list(range(7)) if str(i) not in l]))
        random_input.append(' '.join(l))

    return random_input


if __name__ == '__main__':
    avalon = Avalon(dummy_names[:2],
                    has_percival=False,
                    has_morgana=False,
                    has_mordred=False,
                    has_oberon=False,
                    has_lake_lady=True,
                    n_ai=3)

    for nn in dummy_names[:2]:
        thread = threading.Thread(target=client_handle, args=(nn, avalon,))
        thread.start()

    thread = threading.Thread(target=server_handle, args=(avalon,))
    thread.start()
    thread.join()
