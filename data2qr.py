#!/usr/bin/env python
import bz2
import qrcode
from PIL import Image
from pyzbar import pyzbar
import cv2 as cv
import math

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

def get_image_name_format(nr_imgs):
    return '%%0%dd.png' % (int(math.floor(math.log10(nr_imgs)))+1)

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
    #QRCODE_MAX = 4295
    QRCODE_MAX = 1000
    chunks = [encoded[i:i+QRCODE_MAX] for i in range(0, len(encoded), QRCODE_MAX)]
    img_fmt = get_image_name_format(len(chunks))
    for i, chunk in enumerate(chunks):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(chunk)
        qr.make_image().save(img_fmt % i, 'png')

def qrcode2code(img_name):
    img = cv.imread(img_name, 0)
#    img = Image.open(img_name)
    #img = cv.resize(img,None,fx=5,fy=5)
    print(img)
    cv.imshow('',img)
    import time
    time.sleep(10)
    data = pyzbar.decode(img)
    return data[0].data.decode('utf-8')

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
    script = """cat <<EOF > %s
%s
EOF""" % (filename, content)
    return script

if __name__ == '__main__':
    import os, traceback
    import argparse
    import qrcode

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='mode',
        type=str, choices=['encode', 'decode', 'decode-raw'],
        action='store', default='encode',
        help='covert mode')
    parser.add_argument('-o', dest='out_filename',
        type=str,
        action='store', default='a.out',
        help='output file name')
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
        decoded_filename = args.out_filename
        try:
            if os.path.isfile(decoded_filename):
                raise Exception('file \'%s\' already exists' % decoded_filename)
            contents = []
            for filename in args.filenames:
                contents.append(qrcode2code(filename))
            decoded_content = code2data(''.join(contents))
            with open(decoded_filename, 'a') as f:
                f.write(decoded_content)
        except:
            traceback.print_exc()
    elif args.mode == 'decode-raw':
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

