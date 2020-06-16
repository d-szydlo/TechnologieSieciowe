#!/usr/bin/python

import threading
import sys
from time import sleep, time
from random import uniform, randint
from math import exp

col_count = 0

def generate_msg():
    return ''.join([str(randint(0,1)) for _ in range(8)])

class Network(object):
    def __init__(self):
        self.channel = ['-' for _ in range(50)]
        self.collison_detected = False
        self.transmitting = False
        self.jam_sent = False
        self.lock = threading.Lock()
    
    def set_occupied(self):
        self.transmitting = True
        print("Kanal zajety")
    
    def set_free(self):
        self.transmitting = False
        print("Kanal wolny")

    def set_collision(self):
        self.collison_detected = True
        print("Wykryto kolizje")

    def set_collision_removal(self):
        self.collison_detected = False
        print("Kolizja usunieta")

    def clear_channel(self):
        for i in range(50):
            self.channel[i] = '-'

    def propagate(self, start, data, num):
        self.lock.acquire()
        for i in (0,1):
            if data[i] > -1 and data[i] < 50:
                if self.channel[data[i]] == '-' or (i == 1 and data[i] == start) or num > 0:
                    self.channel[data[i]] = data[2]
                    if num == 7 and data[i] != start:
                        if i == 0:
                            self.channel[data[i]+1] = '-'
                        else:
                            self.channel[data[i]-1] = '-'
                else:
                    if not self.jam_sent:
                        global col_count
                        col_count += 1
                        self.jam_sent = True
                    self.lock.release()
                    self.set_collision()
                    sleep(uniform(exp(0.125*col_count), exp(0.25*col_count)))
                    self.lock.acquire()
                    if self.jam_sent:
                        self.send_jam(start)
                        self.jam_sent = False                   
                    self.set_collision_removal()
                    self.set_free()
                    self.lock.release()
                    return False
            elif data[i] == -1:
                self.channel[0] = '-'
            elif data[i] == 50:             
                self.channel[49] = '-'
        self.lock.release()
        return True

    def send_jam(self, start):
        for i in range(8):
            if start + i < 50:
                self.channel[start+i] = '2'
            if start - i > 0:
                self.channel[start-i] = '2'
            self.display()
        left = start - 8
        right = start + 8
        while left + 8 > -1 or right - 8 < 50:
            if left > -1:
                self.channel[left] = '2'
            if left + 8 > -1:
                self.channel[left+8] = '-'
            if right < 50:
                self.channel[right] = '2'
            if right - 8 < 50:
                self.channel[right-8] = '-'
            left -= 1
            right += 1
            self.display()

    def display(self):
        for ch in self.channel:
            print(ch, end=' ')
        print()
                    
def transmit(user_id, index, t, msg_count, color):
    reset = '\u001b[0m'
    print('{}User {}{} rozpoczyna z parametrami:\n\tindeks: {}\n\tliczba wiadomosci do nadania: {}\n'.format(color, user_id, reset, index, msg_count))
    start = time()
    global network
    max_attempt = 4
    msg_sent = 0
    while time() - start < t:
        activate = randint(0, 1)
        if activate and msg_count - msg_sent > 0:
            attempt = 1
            print('{}User {}:{} rozpoczecie proby {} transmisji wiadomosci nr {}'.format(color, user_id, reset, attempt, msg_sent+1))
            msg = generate_msg()
            while attempt < max_attempt:
                if network.collison_detected:
                    print('{}User {}:{} proba {} wyslania wiadomosci {} zakonczona niepowodzeniem, obecna kolizja'.format(color, user_id, reset, attempt, msg_sent+1))
                    attempt += 1
                    sleep(uniform(1.0, 2.0))
                    continue
                elif network.transmitting:
                    print('{}User {}:{} proba {} wyslania wiadomosci {} zakonczona niepowodzeniem, kanal zajety'.format(color, user_id, reset, attempt, msg_sent+1))
                    attempt += 1
                    continue
                else:
                    bits = [[index, index, bit] for bit in msg]
                    counter = 1
                    sleep(0.001)
                    network.set_occupied()
                    while bits[-1][0] >= -1 or bits[-1][1] <= 50:
                        for i in range(min(len(msg), counter)):
                            success = network.propagate(index, bits[i], i)
                            bits[i][0] -= 1
                            bits[i][1] += 1
                            col = network.collison_detected
                            if not success or col:
                                break
                        counter += 1
                        network.display()
                        if not success or col:
                            break
                    if not success or col:
                        print('{}User {}:{} proba {} wyslania wiadomosci {} zakonczona niepowodzeniem, kolizja z innymi danymi'.format(color, user_id, reset, attempt, msg_sent+1))
                        attempt += 1
                        sleep(uniform(1.0, 2.0))
                    else:
                        print('{}User {}:{} proba {} wyslania wiadomosci {} zakonczona powodzeniem'.format(color, user_id, reset, attempt, msg_sent+1))
                        network.set_free()
                        msg_sent += 1
                        attempt = 4

def main():
    if len(sys.argv) == 1:
        print('Nie podano czasu trwania symulacji!')
        sys.exit(1)
    try:
        t = int(sys.argv[1])
    except:
        print('{} nie jest liczba calkowita!'.format(sys.argv[1]))
        sys.exit(1)
    users = []
    indices = [9, 24, 39]
    colors = ['\u001b[38;5;14m', '\u001b[38;5;183m', '\u001b[38;5;93m']
    for user_id in range(3):
        msg_count = randint(1, 5)
        user = threading.Thread(target=transmit, args=(user_id+1, indices[user_id], t, msg_count, colors[user_id],))
        users.append(user)

    lock = threading.Lock()
    lock.acquire()
    for thread in users:
        thread.start()
    lock.release()
    
    for thread in users:
        thread.join()


if __name__ == '__main__':
    network = Network()
    main()
