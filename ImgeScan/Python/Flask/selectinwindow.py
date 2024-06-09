# selectinwindow.py

import cv2
import numpy as np

class DragRectangle:
    def __init__(self, image, wname, image_width, image_height):
        self.image = image
        self.orig_image = image.copy()
        self.wname = wname
        self.image_width = image_width
        self.image_height = image_height
        self.returnflag = False
        self.outRect = None
        self.drawing = False
        self.start_point = None
        self.end_point = None

    def reset(self):
        self.image = self.orig_image.copy()
        self.outRect = None
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.returnflag = False

    def update_rectangle(self):
        self.image = self.orig_image.copy()
        if self.start_point and self.end_point:
            cv2.rectangle(self.image, self.start_point, self.end_point, (0, 255, 0), 2)

def dragrect(event, x, y, flags, param):
    rectI = param
    if event == cv2.EVENT_LBUTTONDOWN:
        rectI.drawing = True
        rectI.start_point = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE:
        if rectI.drawing:
            rectI.end_point = (x, y)
            rectI.update_rectangle()
    elif event == cv2.EVENT_LBUTTONUP:
        rectI.drawing = False
        rectI.end_point = (x, y)
        rectI.outRect = (rectI.start_point[0], rectI.start_point[1], x - rectI.start_point[0], y - rectI.start_point[1])
        rectI.returnflag = True
        rectI.update_rectangle()
