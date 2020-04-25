#!/usr/bin/env python
import os, traceback
import argparse
import qrcode
from data2qr import *

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

def write_file_script(filename, content):
    eof_str = 'EOF'
    while eof_str in content:
        eof_str = f'{eof_str}{random.choice(string.ascii_letters + string.digits)}'
    script = f"""cat <<{eof_str} | head -n-1 > {filename}
{content}
{eof_str}"""
    return script

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
        if os.path.exists(decoded_filename):
            raise Exception(f'file {decoded_filename} already exists')
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

            decoded_filename = args.out_filename
            if os.path.exists(decoded_filename):
                raise Exception(f'file {decoded_filename} already exists')
            with open(decoded_filename, 'w') as f:
                f.write(decoded_content)
        except:
            traceback.print_exc()

