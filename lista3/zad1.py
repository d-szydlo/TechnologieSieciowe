#!/usr/bin/python3

from random import randint
from zlib import crc32

def generate_message():
    with open('z.txt', 'w') as f:
        msg = ''
        for _ in range(5):
            msg += '{0:b}'.format(randint(2**31, 2**32-1))
        f.write(msg)

def encode_msg(msg):
    crc = '{0:b}'.format(crc32(msg.encode()))
    msg = '0'*(32-len(crc)) + crc + msg
    encoded = ''
    counter = 0
    for bit in msg:
        if bit == '1':
            counter += 1
            encoded += '1'
            if counter == 5:
                encoded += '0'
                counter = 0
        else:
            encoded += '0'
            counter = 0
    return '01111110' + encoded + '01111110'

def decode_msg(msg):
    msg = msg[8:-8]
    decoded = ''
    counter = 0
    for bit in msg:
        if bit == '0':
            if counter != 5:
                decoded += '0'
            counter = 0
        else:
            decoded += '1'
            counter += 1
    plain = decoded[32:]
    crc = decoded[:32]
    check_crc = '{0:b}'.format(crc32(plain.encode()))
    check_crc = '0'*(32-len(check_crc)) + check_crc
    if check_crc != crc:
        return "error"
    else:
        return plain

def main():
    generate_message()
    with open('z.txt', 'r') as f:
        encoded = encode_msg(f.read())
    with open('w.txt', 'w') as f:
        f.write(encoded)
    with open('w.txt', 'r') as f:
        decoded = decode_msg(f.read())
        print(decoded)
        

if __name__ == '__main__':
    main()