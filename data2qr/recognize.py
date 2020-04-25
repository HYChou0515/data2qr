import numpy as np
import cv2
from PIL import Image
from pyzbar import pyzbar

__all__ = ['analysis_pic', 'analysis_pic_file', 'analysis_vid', 'analysis_vid_file']

def analysis_pic(pic):
    decoded_objs = pyzbar.decode(pic)

    qr_str = None
    for decoded_obj in decoded_objs:
        qr_str = decoded_obj.data.decode('utf-8')
        rect = decoded_obj.rect
        points = [(rect.left, rect.top), (rect.left, rect.top+rect.height),
                (rect.left+rect.width, rect.top+rect.height), (rect.left+rect.width, rect.top)]

        if len(points) > 4 :
            hull = cv2.convexHull(np.array(points, dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else :
            hull = points;

        # Number of points in the convex hull
        n = len(hull)

        # Draw the convext hull
        for j in range(n):
            cv2.line(pic, hull[j], hull[ (j+1) % n], (255,0,0), 3)

        # only take one pic
        break

    return pic, qr_str


def analysis_pic_file(pname):
    return analysis_pic(Image.open(pname))


def analysis_vid_file(vname, scan_qr_rate=10, quite_mode=False):
    """Analysis a video of a sequence of images of QR code
    and return captured string from it.

    Args:
        scan_qr_rate: scan qrcode every {x} frames
    """

    vid = cv2.VideoCapture(vname)
    if not vid.isOpened():
        raise ValueError(f'cannot open video "{vname}"')
    return analysis_vid(vid, scan_qr_rate=scan_qr_rate, quite_mode=quite_mode)


def analysis_vid(vid, scan_qr_rate=10, quite_mode=False):

    state = {'paused': False, 'scan_count_down': scan_qr_rate}

    qr_strings = []
    last_qr_str = None
    while vid.isOpened():
        if not state['paused']:
            ret, frame = vid.read()
        if ret:
            if state['scan_count_down'] <= 0:
                frame, qr_str = analysis_pic(frame)
                if qr_str is not None:
                    state['scan_count_down'] = scan_qr_rate
                    if last_qr_str is None or last_qr_str != qr_str:
                        qr_strings.append(qr_str)
                        last_qr_str = qr_str
            else:
                state['scan_count_down'] -= 1

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
    return ''.join(qr_strings)

