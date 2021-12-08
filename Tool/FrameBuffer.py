import threading
import time
import collections
import cv2
import win32gui
import win32ui
import win32con
import numpy as np
import tensorflow as tf
# 顺便录屏#不录了有点麻烦还是用record吧


class FrameBuffer(threading.Thread):
    def __init__(self, threadID, name, width, height,  maxlen=5):  # 进行一些初始化
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.buffer = collections.deque(maxlen=maxlen)  # 4
        self.lock = threading.Lock()

        # 这里是模型输入的图像的窗口范围，分别是左上xy和右下xy的坐标
        self.station_size = (230, 230, 1670, 930)
        self.WIDTH = width
        self.HEIGHT = height
        self._stop_event = threading.Event()

        self.hwnd = win32gui.FindWindow(None, 'Hollow Knight')
        self.left, self.top, x2, y2 = self.station_size
        self.width = x2 - self.left + 1
        self.height = y2 - self.top + 1

        self.hwindc = win32gui.GetWindowDC(self.hwnd)
        self.srcdc = win32ui.CreateDCFromHandle(self.hwindc)
        self.memdc = self.srcdc.CreateCompatibleDC()
        self.bmp = win32ui.CreateBitmap()
        self.bmp.CreateCompatibleBitmap(self.srcdc, self.width, self.height)

    def run(self):
        while not self.stopped():  # 每0.05秒截图一次并存到buffer中
            self.get_frame()
            time.sleep(0.05)
        self.srcdc.DeleteDC()
        self.memdc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, self.hwindc)
        win32gui.DeleteObject(self.bmp.GetHandle())

    def get_frame(self):  # 截图并存到buffer中
        self.lock.acquire(blocking=True)
        station = cv2.resize(cv2.cvtColor(
            self.grab_screen(), cv2.COLOR_RGBA2RGB), (self.WIDTH, self.HEIGHT))
        self.buffer.append(tf.convert_to_tensor(station))
        self.lock.release()

    def get_buffer(self):  # station是连续4次的截图，也就是0.2秒发生的事情，这也是模型的输入内容
        stations = []
        self.lock.acquire(blocking=True)
        for f in self.buffer:
            stations.append(f)
        self.lock.release()
        return stations

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def grab_screen(self):  # 进行一个图的截
        self.memdc.SelectObject(self.bmp)
        self.memdc.BitBlt((0, 0), (self.width, self.height),
                          self.srcdc, (self.left, self.top), win32con.SRCCOPY)

        signedIntsArray = self.bmp.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.height, self.width, 4)

        return img
