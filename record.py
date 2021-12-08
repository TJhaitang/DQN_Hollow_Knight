import wave
import threading
from os import remove, mkdir, listdir
from os.path import exists, splitext, basename, join
from datetime import datetime
import time
from shutil import rmtree
from PIL import ImageGrab
from moviepy.editor import *
import keyboard

CHUNK_SIZE = 1024
CHANNELS = 2
RATE = 48000
allowRecording = True


class Recorder():
    def __init__(self):
        self.allowRecording = True
        self.isRun = 0
        self.pic_dir = 'pics'
        if not exists(self.pic_dir):
            mkdir(self.pic_dir)

    def start(self):
        if (self.isRun == 0):
            print("start")
            self.rd = threading.Thread(target=self.record_screen)
            self.pic_dir = 'pics'
            self.startTime = time.time()
            self.allowRecording = True
            if not exists(self.pic_dir):
                mkdir(self.pic_dir)
            self.rd.start()
            self.isRun = 1

    def shut(self):
        if(self.isRun == 1):
            print("shut")
            self.allowRecording = False
            self.rd.join()
            rmtree(self.pic_dir)
            self.isRun = 0

    def stop(self):
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
            # 删除临时音频文件和截图
            rmtree(self.pic_dir)
            self.isRun = 0

    def record_screen(self):
        index = 1
        while self.allowRecording:
            ImageGrab.grab().save(f'{self.pic_dir}\{index}.jpg',
                                  quality=95, subsampling=0)
            time.sleep(0.04)
            index = index + 1


rcd = Recorder()
keyboard.add_hotkey('f2', rcd.start)
keyboard.add_hotkey('f3', rcd.stop)
keyboard.add_hotkey('f4', rcd.shut)
keyboard.wait()
# pic_dir = 'pics'
# if not exists(pic_dir):
#     mkdir(pic_dir)
# video_filename = audio_filename[:-3] + 'avi'
# # 创建两个线程，分别录音和录屏
# t2 = threading.Thread(record_screen)
# t2.start()888888888
# print('3秒后开始录制，按q键结束录制')
# while (ch:= input()) != 'q':
#     pass98897978
# allowRecording = False
# t2.join()

# # 把录制的音频和屏幕截图合成为视频文件
# pic_files = [join(pic_dir, fn) for fn in listdir(pic_dir)
#              if fn.endswith('.jpg')]
# # 按文件名编号升序排序
# pic_files.sort(key=lambda fn: int(splitext(basename(fn))[0]))
# # 计算每个图片的显示时长
# each_duration = round(audio.duration / len(pic_files), 4)
# # 连接多个图片
# image_clips = []9878
# for pic in pic_files:
#     image_clips.append(ImageClip(pic,
#                                  duration=each_duration))
# video = concatenate_videoclips(image_clips)
# video.write_videofile(video_filename, codec='mpeg4', fps=24)
# # 删除临时音频文件和截图
# rmtree(pic_dir)
