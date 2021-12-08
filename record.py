import threading
from os import remove, mkdir, listdir
from os.path import exists, splitext, basename, join
import time
from shutil import rmtree
from PIL import ImageGrab
from moviepy.editor import *
import keyboard

CHUNK_SIZE = 1024
CHANNELS = 2
RATE = 48000
allowRecording = True


class Recorder():  # 用来录像
    def __init__(self):
        self.allowRecording = True
        self.isRun = 0
        self.pic_dir = 'pics'  # 截图放在pics文件夹下
        if not exists(self.pic_dir):
            mkdir(self.pic_dir)

    def start(self):  # 开始录制
        if (self.isRun == 0):
            print("start")
            self.rd = threading.Thread(
                target=self.record_screen)  # 开一个线程用来保存图像
            self.pic_dir = 'pics'
            self.startTime = time.time()  # 记录一下开始时间
            self.allowRecording = True
            if not exists(self.pic_dir):
                mkdir(self.pic_dir)
            self.rd.start()
            self.isRun = 1

    def shut(self):  # 结束录制并删除截图不保存
        if(self.isRun == 1):
            print("shut")
            self.allowRecording = False
            self.rd.join()  # 等待线程结束
            rmtree(self.pic_dir)  # 删除文件
            self.isRun = 0  # 代替一下锁

    def stop(self):  # 结束录制并保存录像
        if(self.isRun == 1):
            print("stop")
            self.allowRecording = False
            self.rd.join()
            pic_files = [join(self.pic_dir, fn) for fn in listdir(self.pic_dir)
                         if fn.endswith('.jpg')]
            # 按文件名编号升序排序
            pic_files.sort(key=lambda fn: int(splitext(basename(fn))[0]))
            # 计算每个图片的显示时长
            each_duration = round(
                (time.time()-self.startTime) / len(pic_files), 4)
            # 连接多个图片
            image_clips = []
            for pic in pic_files:
                image_clips.append(ImageClip(pic,
                                             duration=each_duration))
            video = concatenate_videoclips(image_clips)
            video.write_videofile(str(time.time())+'.avi',
                                  codec='mpeg4', fps=24)
            # 删除截图
            rmtree(self.pic_dir)
            self.isRun = 0

    def record_screen(self):  # 不断截图并保存
        index = 1
        while self.allowRecording:
            ImageGrab.grab().save(f'{self.pic_dir}\{index}.jpg',
                                  quality=95, subsampling=0)
            time.sleep(0.04)
            index = index + 1


# 加几个listener用来控制录屏的开关
rcd = Recorder()
keyboard.add_hotkey('f2', rcd.start)
keyboard.add_hotkey('f3', rcd.stop)
keyboard.add_hotkey('f4', rcd.shut)
keyboard.wait()
