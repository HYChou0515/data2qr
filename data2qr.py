#!/usr/bin/env python
import bz2
import qrcode

"""
This program effectively encodes and transforms data to QR code.

Encoding work flow:
    ascii string --to-byte-array-->--bz2-compress--> byte array (bit256 array)
    --to-int--> large int --re-partition-by-45--> bit45 array --using-D--> encoded array
    --get-chunks-if-to-large--> QR Codes

Decoding work flow: assume imcoming is one long string in char set D
    long string --using-D--> large int --to-binary--> bits
    --padding--> bits with length be a multiple of 8 --8-bits-a-chunk--> byte array
    --bz2-decompress--> decoded byte array --decode-ascii--> ascii string
"""

ENCODE_METHOD = 'ascii'
D = []
D.extend([chr(ord('0')+i) for i in range(10)])
D.extend([chr(ord('A')+i) for i in range(26)])
D.extend([' ', '$', '%', '*', '+', '-', '.', '/', ':'])

def data2code(s):
    byte_array=bz2.compress(s.encode(ENCODE_METHOD))
    bits = ''.join(map(lambda bt: bin(bt)[2:].zfill(8), byte_array))
    bignum = int(bits, 2)
    bit45_array = []
    while bignum > 0:
        bit45_array.append(bignum%45)
        bignum = bignum // 45
    encoded = ''.join([D[bit45] for bit45 in bit45_array])
    return encoded

def code2qrcode(encoded):
    QRCODE_MAX = 4295
    chunks = [encoded[i:i+QRCODE_MAX] for i in range(0, len(encoded), QRCODE_MAX)]
    for i, chunk in enumerate(chunks):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(chunk)
        qr.make_image().save('%d.png' % i, 'png')

def code2data(encoded):
    encoded = encoded.replace('\n','')
    bignum = 0
    for ch in encoded[::-1]:
        bignum *= 45
        bignum += D.index(ch)

    bits = bin(bignum)[2:]
    bits = bits.zfill(len(bits)+8-len(bits)%8) # padding until be a multiple of 8
    bit8_array = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return bz2.decompress(bytes([int(byte, 2) for byte in bit8_array])).decode(ENCODE_METHOD)

def write_file_script(filename, content):
    script = """
with open('%s.encode', 'w') as f:
    f.write(\"\"\"%s\"\"\")
""" % (filename, content)
    return script

if __name__ == '__main__':
    import os, traceback
    import argparse
    import qrcode

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='mode',
        type=str, choices=['encode', 'decode'],
        action='store', default='encode',
        help='covert mode')
    #positional arguments
    parser.add_argument('filenames', nargs='*', type=str,
        help='file names')

    args = parser.parse_args()

    if args.mode == 'encode':
        big_str = ''
        for filename in args.filenames:
            with open(filename, 'r') as f:
                content = f.read()
            script = write_file_script(filename, content)
            big_str += script
        encoded_str = data2code(big_str)
        code2qrcode(encoded_str)
    elif args.mode == 'decode':
        for filename in args.filenames:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                decoded_content = code2data(content)

                decoded_filename = filename+'.decode'
                if os.path.isfile(decoded_filename):
                    raise Exception('file \'%s\' already exists')
                with open(decoded_filename, 'w') as f:
                    f.write(decoded_content)
            except:
                traceback.print_exc()
