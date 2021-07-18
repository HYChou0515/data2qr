import os
import numpy as np
import bz2
import cv2
import qrcode
from PIL import Image
from pyzbar import pyzbar
import math

__all__ = ['data2code', 'code2qrcode', 'qrcode2code', 'qrcode2code_v2', 'code2data']

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
CODE_SEP1 = '@'
CODE_SEP2 = '#'

QRCODE_MAX_DICT={
        qrcode.constants.ERROR_CORRECT_L: 1852,
        qrcode.constants.ERROR_CORRECT_M: 1032,
        qrcode.constants.ERROR_CORRECT_Q: 644,
        qrcode.constants.ERROR_CORRECT_H: 490,
}

def _default_image_name_generator(prefix=None):
    fmt = '%d.png'
    if prefix is not None:
        fmt = prefix + fmt
    i = 0
    while True:
        yield fmt % i
        i += 1

def _bits_to_code(bits):
    bits = bits.zfill(len(bits) + (-len(bits)%5)) # padding zero so len(bits) % 5 == 0
    np_num32 = [int(bits[i:i+5], 2) for i in range(0, len(bits), 5)]
    encoded = ''.join(D[np_num32])
    return encoded

def data2code(s):
    byte_array=bz2.compress(s)
    bits = ''.join(map(lambda bt: bin(bt)[2:].zfill(8), byte_array))
    return _bits_to_code(bits)

def code2qrcode(encoded, image_name_generator=None, prefix=None, prepend_idx=False, n_jobs=1):
    ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_M
    QRCODE_MAX = QRCODE_MAX_DICT[ERROR_CORRECT]
    if prepend_idx:
        def prepended_chunk(encoded):
            st = 0
            id_chunk = 0
            while st < len(encoded):
                encoded_id = _bits_to_code(bin(id_chunk)[2:])
                ed = st + QRCODE_MAX - len(encoded_id) - 1
                code_sep = CODE_SEP1 if ed < len(encoded) else CODE_SEP2
                yield encoded_id + code_sep + encoded[st:ed]
                st = ed
                id_chunk += 1
        chunks = prepended_chunk(encoded)
    else:
        chunks = (encoded[i:i+QRCODE_MAX] for i in range(0, len(encoded), QRCODE_MAX))
    image_names =image_name_generator if image_name_generator is not None else _default_image_name_generator(prefix=prefix)

    def to_qrcode_1(_chunk, _image_name, _i):
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT)
        qr.add_data(_chunk)
        if os.path.exists(_image_name):
            raise os.error(f'File "{_image_name}" exists')
        qr.make_image().save(_image_name, 'png')
        info(f'{_i}')
        return _image_name

    image_names = [to_qrcode_1(chunk, image_name, i) for i, (chunk, image_name) in enumerate(zip(chunks, image_names))]
#    image_names = Parallel(n_jobs=n_jobs, prefer='processes')(
#        delayed(to_qrcode_1)(chunk, image_name, i)
#        for i, (chunk, image_name) in enumerate(zip(chunks, image_names))
#    )
    return image_names

def qrcode2code_v2(frame, quite_mode=True):
    decoded_objs = pyzbar.decode(frame)
    qr_str = None

    # only take one frame
    if len(decoded_objs) > 0:
        decoded_obj = decoded_objs[0]

        qr_str = decoded_obj.data.decode('utf-8')
        if not quite_mode:
            # mark qrcode in rectangle
            rect = decoded_obj.rect
            points = [(rect.left, rect.top), (rect.left, rect.top+rect.height),
                    (rect.left+rect.width, rect.top+rect.height), (rect.left+rect.width, rect.top)]

            if len(points) > 4 :
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else :
                hull = points;

            # Number of points in the convex hull
            n = len(hull)

            # Draw the convext hull
            for j in range(0,n):
                cv2.line(frame, hull[j], hull[ (j+1) % n], (255,0,0), 3)

    if quiet_mode:
        return qr_str
    else:
        return qr_str, frame

def qrcode2code(img_name):
    img = Image.open(img_name)
    data = pyzbar.decode(img)
    return data[0].data.decode('utf-8')

def code2data(encoded, encode_method='bz2', prepend_idx=False):
    encoded = encoded.replace('\n','')
    if prepend_idx:
        if CODE_SEP1 in encoded:
            idx_ed = encoded.index(CODE_SEP1)
            last_chunk = False
        elif CODE_SEP2 in encoded:
            idx_ed = encoded.index(CODE_SEP2)
            last_chunk = True
        else:
            raise Exception(f'{CODE_SEP1} and {CODE_SEP2} are not in encoded.')
        chunk_id = code2data(encoded[:idx_ed], encode_method='int')
        return chunk_id, encoded[idx_ed+1:], last_chunk
    else:
        num32_arr = [IDX_D[c] for c in encoded]
        bits = ''.join([bin(x)[2:].zfill(5) for x in num32_arr])
        if encode_method == 'bz2':
            bits = bits[len(bits)%8:]  # remove padding
            bit8_array = [bits[i:i+8] for i in range(0, len(bits), 8)]
            return bz2.decompress(bytes([int(byte, 2) for byte in bit8_array]))
        elif encode_method == 'int':
            return int(bits, 2)
        else:
            raise NotImplemented

