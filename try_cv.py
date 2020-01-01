import numpy as np
import cv2
import sys

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

def scan_qr(frame):
    decoded_objs = pyzbar.decode(frame)

    qr_str = None
    for decoded_obj in decoded_objs:
        qr_str = decoded_obj.data.decode('utf-8')
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

        # only take one frame
        break

    return frame, qr_str

def analysis_video(vname):

    cap = cv2.VideoCapture(vname)
    if not cap.isOpened():
        raise ValueError('cannot open video \"%s\"' % (vname))

    SCAN_QR_RATE = 10 # scan qrcode every ?? frames
    state = {'paused': False, 'scan_qr': SCAN_QR_RATE}

    qr_strings = []
    last_qr_str = None
    while cap.isOpened():
        if not state['paused']:
            ret, frame = cap.read()
        if ret:
            if state['scan_qr'] <= 0:
                frame, qr_str = scan_qr(frame)
                if qr_str is not None:
                    state['scan_qr'] = SCAN_QR_RATE
                    if last_qr_str is None or last_qr_str != qr_str:
                        print(qr_str)
                        qr_strings.append(qr_str)
                        last_qr_str = qr_str
            else:
                state['scan_qr'] -= 1

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
    print(qr_strings)

#capture_video()
analysis_video(sys.argv[1])
