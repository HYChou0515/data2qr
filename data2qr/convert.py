import os
import bz2
import qrcode
from PIL import Image
from pyzbar import pyzbar
import math

__all__ = ['data2code', 'code2qrcode', 'qrcode2code', 'code2data']

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

QRCODE_MAX_DICT={
        qrcode.constants.ERROR_CORRECT_L: 1852,
        qrcode.constants.ERROR_CORRECT_M: 1032,
        qrcode.constants.ERROR_CORRECT_Q: 644,
        qrcode.constants.ERROR_CORRECT_H: 490,
}

def _default_image_name_generator(nr_imgs):
    fmt = '%%0%dd.png' % (int(math.floor(math.log10(nr_imgs)))+1)
    for i in range(nr_imgs):
        yield fmt % i

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

def code2qrcode(encoded, image_name_generator=None):
    ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_Q
    QRCODE_MAX = QRCODE_MAX_DICT[ERROR_CORRECT]
    chunks = [encoded[i:i+QRCODE_MAX] for i in range(0, len(encoded), QRCODE_MAX)]
    image_names =image_name_generator if image_name_generator is not None else _default_image_name_generator(len(chunks))
    rt_names = []
    for chunk, image_name in zip(chunks, image_names):
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT)
        qr.add_data(chunk)
        if os.path.exists(image_name):
            raise os.error(f'File "{image_name}" exists')
        qr.make_image().save(image_name, 'png')
        rt_names.append(image_name)
    return rt_names

def qrcode2code(img_name):
    img = Image.open(img_name)
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

