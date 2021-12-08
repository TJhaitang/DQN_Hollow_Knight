# -*- coding: utf-8 -*-
import tensorflow as tf
import time
import collections
from ctypes import *
from eprogress import LineProgress

from Model import Model
from DQN import DQN
from Agent import Agent
from ReplayMemory import ReplayMemory

import Tool.Helper
import Tool.Actions
from Tool.Helper import mean
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


def run_episode(hp, algorithm, agent, act_rmp_correct, move_rmp_correct, PASS_COUNT):
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
    # Delay Reward
    DelayMoveReward = collections.deque(maxlen=DELAY_REWARD)
    DelayActReward = collections.deque(maxlen=DELAY_REWARD)
    DelayStation = collections.deque(
        maxlen=DELAY_REWARD + 1)  # 1 more for next_station
    DelayActions = collections.deque(maxlen=DELAY_REWARD)
    DelayDirection = collections.deque(maxlen=DELAY_REWARD)

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
        move, action = agent.sample(
            stations, soul, hornet_x, hornet_y, player_x, hornet_skill1)
        # threading.Thread(target=runDo, args=(
        #     move, action, player_x, hornet_x)).start()#开一个线程进行操作以避免操作本身占用些什么时间，但性能够好就无所谓（而且不好做线程之间的统筹
        take_direction(move)
        take_action(action, player_x, hornet_x)  # 改了一下
        time.sleep(0.1)  # 等技能放出去了再判断reward，但这个时间到底要多久就不知道了，0.05基本就是无，又不敢放多了
        # 获取动作效果
        next_station = thread1.get_buffer()
        next_boss_hp_value = hp.get_boss_hp()
        next_self_hp = hp.get_self_hp()
        next_player_x, next_player_y = hp.get_play_location()
        next_hornet_x, next_hornet_y = hp.get_hornet_location()
        Nothing()  # 释放双手

        # 获取一下操作的收益并存起来，但这个放在这里会不会浪费性能，放在循环外会不会好一点
        # actionreward可以调整以改变骑士的风格
        move_reward = Tool.Helper.move_judge(
            self_hp, next_self_hp, player_x, next_player_x, hornet_x, next_hornet_x, move, hornet_skill1)
        act_reward, done = Tool.Helper.action_judge(
            boss_hp_value, next_boss_hp_value, self_hp, next_self_hp, next_player_x, next_hornet_x, next_hornet_x, action, hornet_skill1)
        # 存起来
        DelayMoveReward.append(move_reward)
        DelayActReward.append(act_reward)
        DelayStation.append(stations)
        DelayStation.append(next_station)
        DelayActions.append(action)
        DelayDirection.append(move)

        # 存起来
        if len(DelayStation) >= DELAY_REWARD + 1:
            if DelayMoveReward[0] != 0:
                move_rmp_correct.append(
                    (DelayStation[0], DelayDirection[0], DelayMoveReward[0], DelayStation[1], done))

        if len(DelayStation) >= DELAY_REWARD + 1:
            if mean(DelayActReward) != 0:
                act_rmp_correct.append((DelayStation[0], DelayActions[0], mean(
                    DelayActReward), DelayStation[1], done))

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
    print("结算中...")
    line_progress = LineProgress(title='模型学习中。。。')
    # 强化一下
    for i in range(50):
        if (len(move_rmp_correct) > MEMORY_WARMUP_SIZE):
            # print("move learning")
            batch_station, batch_actions, batch_reward, batch_next_station, batch_done = move_rmp_correct.sample(
                BATCH_SIZE)
            algorithm.move_learn(batch_station, batch_actions,
                                 batch_reward, batch_next_station, batch_done)
        line_progress.update(2*i+1)
        if (len(act_rmp_correct) > MEMORY_WARMUP_SIZE):
            # print("action learning")
            batch_station, batch_actions, batch_reward, batch_next_station, batch_done = act_rmp_correct.sample(
                BATCH_SIZE)
            algorithm.act_learn(batch_station, batch_actions,
                                batch_reward, batch_next_station, batch_done)
        line_progress.update(2*i+2)

    return PASS_COUNT, self_hp


if __name__ == '__main__':

    # In case of out of memory
    config = tf.compat.v1.ConfigProto(allow_soft_placement=True)
    config.gpu_options.allow_growth = True  # 程序按需申请内存
    sess = tf.compat.v1.Session(config=config)

    total_remind_hp = 0

    act_rmp_correct = ReplayMemory(
        MEMORY_SIZE, file_name='./act_memory')         # experience pool
    move_rmp_correct = ReplayMemory(
        MEMORY_SIZE, file_name='./move_memory')         # experience pool

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
            hp, algorithm, agent, act_rmp_correct, move_rmp_correct, PASS_COUNT)
        # 偶尔保存模型和数据
        if episode % 10 == 1:
            model.save_mode()
        if episode % 5 == 0:
            move_rmp_correct.save(move_rmp_correct.file_name)
        if episode % 5 == 0:
            act_rmp_correct.save(act_rmp_correct.file_name)
        total_remind_hp += remind_hp
        print("Episode: ", episode, ", pass_count: ",
              PASS_COUNT, ", hp:", total_remind_hp / episode)
