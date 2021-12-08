# -*- coding: utf-8 -*-
import tensorflow as tf
import time
from ctypes import *

from Model import Model
from DQN import DQN
from Agent import Agent

import Tool.Helper
import Tool.Actions
from Tool.Actions import Nothing, take_action, restart, take_direction
from Tool.GetHP import Hp_getter
from Tool.FrameBuffer import FrameBuffer
from Tool.SendKey import PressKey, ReleaseKey

WIDTH = 400  # 奶酪
HEIGHT = 200
ACTION_DIM = 7  # 操作维度：砍、小跳、大跳、上砍、技能上、技能下、不动
FRAMEBUFFERSIZE = 4  # 缓存区大小
INPUT_SHAPE = (FRAMEBUFFERSIZE, HEIGHT, WIDTH, 3)

MEMORY_SIZE = 200  # replay memory的大小，越大越占用内存
MEMORY_WARMUP_SIZE = 24  # replay_memory 里需要预存一些经验数据，再从里面sample一个batch的经验让agent去learn
BATCH_SIZE = 10  # 每次给agent learn的数据数量，从replay memory随机里sample一批数据出来
LEARNING_RATE = 0.00001  # 学习率
GAMMA = 0
DELAY_REWARD = 1

action_name = ["Attack", "Attack_Up",
               "Short_Jump", "Mid_Jump", "Skill_Up",
               "Skill_Down", "Rush", "nothing"]

move_name = ["Move_Left", "Move_Right", "Turn_Left", "Turn_Right"]


def run_episode(hp, algorithm, agent, PASS_COUNT):
    # 按f2启动record
    PressKey(0x71)
    time.sleep(0.1)
    ReleaseKey(0x71)
    # 启动开始游戏脚本
    thread1 = FrameBuffer(1, "FrameBuffer", WIDTH,
                          HEIGHT, maxlen=FRAMEBUFFERSIZE)  # 这里同时完成一下录制功能
    thread1.start()
    restart()
    # 初始化一些数据
    step = 0
    done = 0

    while True:  # 等待进入游戏，当boss有血量信息的时候说明进去了遂退出循环
        hp.load_boss_hp_address()
        hp.load_boss_location()
        boss_hp_value = hp.get_boss_hp()
        self_hp = hp.get_self_hp()
        if boss_hp_value > 800 and boss_hp_value <= 900 and self_hp >= 1 and self_hp <= 9:
            break

    last_hornet_y = 0
    while True:  # 开始游戏
        step += 1  # 操作数
        # in case of do not collect enough frames
        while(len(thread1.buffer) < FRAMEBUFFERSIZE):
            time.sleep(0.1)

        stations = thread1.get_buffer()
        # 奶酪入口
        # 获取当前状态
        boss_hp_value = hp.get_boss_hp()
        self_hp = hp.get_self_hp()
        player_x, player_y = hp.get_play_location()
        hornet_x, hornet_y = hp.get_hornet_location()
        soul = hp.get_souls()
        # 监控一下，意义不大
        print(str(self_hp)+"--"+str(boss_hp_value))
        # 调整，手动判断一下大黄蜂有没有放技能
        hornet_skill1 = False
        if last_hornet_y > 32 and last_hornet_y < 32.5 and hornet_y > 32 and hornet_y < 32.5:
            hornet_skill1 = True
        last_hornet_y = hornet_y
        # 从agent中获取预测结果
        move, action = agent.samplep(
            stations, soul, hornet_x, hornet_y, player_x, hornet_skill1)
        # threading.Thread(target=runDo, args=(
        #     move, action, player_x, hornet_x)).start()#开一个线程进行操作以避免操作本身占用些什么时间，但性能够好就无所谓（而且不好做线程之间的统筹
        take_direction(move)
        take_action(action, player_x, hornet_x)  # 改了一下
        next_boss_hp_value = hp.get_boss_hp()
        next_self_hp = hp.get_self_hp()
        next_player_x, next_player_y = hp.get_play_location()
        next_hornet_x, next_hornet_y = hp.get_hornet_location()
        Nothing()  # 释放双手
        act_reward, done = Tool.Helper.action_judge(
            boss_hp_value, next_boss_hp_value, self_hp, next_self_hp, next_player_x, next_hornet_x, next_hornet_x, action, hornet_skill1)

        if done == 1:  # 打完了就结算
            Tool.Actions.Nothing()
            break
        elif done == 2:
            PASS_COUNT += 1
            Tool.Actions.Nothing()
            time.sleep(3)
            break
    # 关掉recorder，打过了就保存视频，没打过就删
    if done == 1:
        PressKey(0x73)
        time.sleep(0.1)
        ReleaseKey(0x73)
    elif done == 2:
        PressKey(0x72)
        time.sleep(0.1)
        ReleaseKey(0x72)
    # thread
    thread1.stop()

    return PASS_COUNT, self_hp


if __name__ == '__main__':

    # In case of out of memory
    config = tf.compat.v1.ConfigProto(allow_soft_placement=True)
    config.gpu_options.allow_growth = True  # 程序按需申请内存
    sess = tf.compat.v1.Session(config=config)

    total_remind_hp = 0

    # new model, if exit save file, load it
    model = Model(INPUT_SHAPE, ACTION_DIM)

    # Hp counter
    hp = Hp_getter()

    model.load_model()
    algorithm = DQN(model, gamma=GAMMA, learnging_rate=LEARNING_RATE)
    agent = Agent(ACTION_DIM, algorithm, e_greed=0.12, e_greed_decrement=1e-6)

    # 先暂停等开始
    Tool.Helper.pause_game(True)

    max_episode = 30000
    # 开始训练
    episode = 0
    PASS_COUNT = 0                                       # pass count
    while episode < max_episode:    # 训练max_episode个回合，test部分不计算入episode数量
        # 训练
        episode += 1
        PASS_COUNT, remind_hp = run_episode(
            hp, algorithm, agent, PASS_COUNT)
        total_remind_hp += remind_hp
        print("Episode: ", episode, ", pass_count: ",
              PASS_COUNT, ", hp:", total_remind_hp / episode)
