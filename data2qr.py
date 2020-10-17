#!/usr/bin/env python
import os, traceback
import argparse
from data2qr import *

parser = argparse.ArgumentParser()
parser.add_argument('-m', dest='mode',
    type=str, choices=['encode', 'd2q', 'decode', 'q2d', 'decode-raw'],
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

def write_file_script(filename, byte_arr):
    content = data2code(byte_arr)
    script = f"""
mkdir -p $(dirname {filename})
python -c 'from data2qr import *; f=open("{filename}", "wb"); f.write(code2data("{content}")); f.close()'
"""
    return script

if args.mode in ('encode', 'd2q'):
    big_str = ''
    for filename in args.filenames:
        with open(filename, 'rb') as f:
            content = f.read()
        script = write_file_script(filename, content)
        big_str += script
    encoded_str = data2code(big_str.encode('ascii'))
    code2qrcode(encoded_str, n_jobs=-1)
elif args.mode in ('decode', 'q2d'):
    decoded_filename = args.out_filename
    try:
        if os.path.exists(decoded_filename):
            raise Exception(f'file {decoded_filename} already exists')
        contents = []
        for filename in args.filenames:
            contents.append(qrcode2code(filename))
        decoded_content = code2data(''.join(contents)).decode('ascii')
        with open(decoded_filename, 'a') as f:
            f.write(decoded_content)
    except:
        traceback.print_exc()
elif args.mode == 'decode-raw':
    decoded_filename = args.out_filename
    if os.path.exists(decoded_filename):
        raise Exception(f'file {decoded_filename} already exists')
    for filename in args.filenames:
        try:
            with open(filename, 'r') as f:
                content = f.read()
            decoded_content = code2data(content).decode('ascii')

            with open(decoded_filename, 'a') as f:
                f.write(decoded_content)
        except:
            traceback.print_exc()

