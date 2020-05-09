import os
import numpy as np
import bz2
import qrcode
from PIL import Image
from pyzbar import pyzbar
from joblib import Parallel, delayed
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

def info(s):
    print(s)

D = []
D.extend([chr(ord('0')+i) for i in range(10)])
D.extend([chr(ord('A')+i) for i in range(26)])
D.extend([' ', '$', '%', '*', '+', '-', '.', '/', ':'])
D = np.array(D)
IDX_D = {D[i]: i for i in range(len(D))}

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
    byte_array=bz2.compress(s)
    bits = ''.join(map(lambda bt: bin(bt)[2:].zfill(8), byte_array))
    bits = bits.zfill(len(bits) + (-len(bits)%5)) # padding zero so len(bits) % 5 == 0
    np_num32 = [int(bits[i:i+5], 2) for i in range(0, len(bits), 5)]
    encoded = ''.join(D[np_num32])
    return encoded

def code2qrcode(encoded, image_name_generator=None, n_jobs=1):
    ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_L
    QRCODE_MAX = QRCODE_MAX_DICT[ERROR_CORRECT]
    chunks = [encoded[i:i+QRCODE_MAX] for i in range(0, len(encoded), QRCODE_MAX)]
    image_names =image_name_generator if image_name_generator is not None else _default_image_name_generator(len(chunks))
    rt_names = []
    def to_qrcode_1(_chunk, _image_name, _i):
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT)
        qr.add_data(_chunk)
        if os.path.exists(_image_name):
            raise os.error(f'File "{_image_name}" exists')
        qr.make_image().save(_image_name, 'png')
        rt_names.append(_image_name)
        info(f'{_i}/{len(chunks)}')
    Parallel(n_jobs=n_jobs, require='sharedmem')(
        delayed(to_qrcode_1)(chunk, image_name, i)
        for i, (chunk, image_name) in enumerate(zip(chunks, image_names))
    )
    return rt_names

def qrcode2code(img_name):
    img = Image.open(img_name)
    data = pyzbar.decode(img)
    return data[0].data.decode('utf-8')

def code2data(encoded):
    encoded = encoded.replace('\n','')
    num32_arr = [IDX_D[c] for c in encoded]
    bits = ''.join([bin(x)[2:].zfill(5) for x in num32_arr])
    bits = bits[len(bits)%8:]  # remove padding
    bit8_array = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return bz2.decompress(bytes([int(byte, 2) for byte in bit8_array]))

