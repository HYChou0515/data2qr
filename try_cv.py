#!/usr/bin/env python
import numpy as np
import cv2

from PIL import Image
from pyzbar import pyzbar

from data2qr import code2data

def capture_video():

    cap = cv2.VideoCapture(0)
    out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc('P','I','M','1'), 20.0, (640,480))

    saving = False
    while cap.isOpened():
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret:
            # Display the resulting frame
            cv2.imshow('frame', frame)

            if saving:
                out.write(frame)

            key = cv2.waitKey(1)
            if key & 0xFF == ord('s'):
                print('Start Saving Video')
                saving = True
            elif key & 0xFF == ord('q'):
                break
        else:
            break

    # When everything done, release the capture
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def scan_qr(frame, quite_mode):
    decoded_objs = pyzbar.decode(frame)

    qr_str = None

    # only take one frame
    if len(decoded_objs) > 0:
        decoded_obj = decoded_objs[0]

        qr_str = decoded_obj.data.decode('utf-8')
        if not quite_mode:
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

    return frame, qr_str

def analysis_video(vname, scan_qr_rate=10, quite_mode=False):
    """Analysis a video of a sequence of images of QR code
    and return captured string from it.

    Args:
        scan_qr_rate: scan qrcode every {x} frames
    """

    cap = cv2.VideoCapture(vname)
    if not cap.isOpened():
        raise ValueError(f'cannot open video "{vname}"')

    state = {'paused': False, 'scan_qr': scan_qr_rate}

    qr_strings = {}
    nr_chunks = None
    while cap.isOpened():
        if not state['paused']:
            ret, frame = cap.read()
        if ret:
            if state['scan_qr'] <= 0:
                frame, qr_str = scan_qr(frame, quite_mode)
                if qr_str is not None:
                    state['scan_qr'] = scan_qr_rate
                    if qr_str not in qr_strings:
                        chunk_id, data, last_chunk = code2data(qr_str, prepend_idx=True)
                        qr_strings[qr_str] = chunk_id, data
                        if last_chunk:
                            nr_chunks = chunk_id + 1
            else:
                state['scan_qr'] -= 1

            if not quite_mode:
                cv2.imshow('frame', frame)

            key = cv2.waitKey(25)

            if key & 0xFF == ord('q'):
                break
            elif key & 0xFF == ord('p'):
                if state['paused']:
                    state['paused'] = False
                    print('Unpaused')
                else:
                    state['paused'] = True
                    print('Paused')
        else:
            break
    if nr_chunks is None:
        raise Exception('Cannot get nr_chunks')
    if len(qr_strings) != nr_chunks:
        raise Exception(f'got {len(qr_strings)} qrcodes but should have {nr_chunks}')
    qs_list = [None for _ in range(nr_chunks)]
    for chunk_id, data in qr_strings.values():
        if chunk_id < 0 or chunk_id >= nr_chunks:
            raise Exception(f'got chunk_id={chunk_id} but should between 0 and {nr_chunks-1}')
        if qs_list[chunk_id] is not None:
            raise Exception(f'got multiple chunk_id={chunk_id} that have different data')
        qs_list[chunk_id] = data
    return code2data(''.join(qs_list))

if __name__ == '__main__':
    import sys
    #capture_video()
    decoded_str = analysis_video(sys.argv[1], quite_mode=False)
    print(decoded_str)

