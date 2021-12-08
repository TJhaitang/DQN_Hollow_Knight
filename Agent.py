# -*- coding: utf-8 -*-
import numpy as np
import tensorflow as tf


class Agent:
    def __init__(self, act_dim, algorithm, e_greed=0.1, e_greed_decrement=0):
        self.act_dim = act_dim
        self.algorithm = algorithm
        self.e_greed = e_greed
        self.e_greed_decrement = e_greed_decrement

    def samplep(self, station, soul, hornet_x, hornet_y, player_x, hornet_skill1):  # 完全依赖模型给出动作
        pred_move, pred_act = self.algorithm.model.predict(station)  # 从模型中获取动作
        pred_move = pred_move.numpy()
        pred_act = pred_act.numpy()
        # 有一定几率不使用模型给出的动作
        sample = 5
        if sample < self.e_greed:  # 使用计算给出的操作

            move = self.better_move(hornet_x, player_x, hornet_skill1)
        else:
            move = np.argmax(pred_move)
        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)

        sample = np.random.rand()
        if sample < self.e_greed:  # 使用计算给出的操作
            act = self.better_action(
                soul, hornet_x, hornet_y, player_x, hornet_skill1)
        else:  # 如果使用模型给出的操作但是能量不够，就用模型给出的其他建议
            act = np.argmax(pred_act)
            if soul < 33:
                if act == 4 or act == 5:
                    pred_act[0][4] = -30
                    pred_act[0][5] = -30
            act = np.argmax(pred_act)
        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)

        return move, act

    def sample(self, station, soul, hornet_x, hornet_y, player_x, hornet_skill1):  # 获取一次动作

        pred_move, pred_act = self.algorithm.model.predict(station)  # 从模型中获取动作
        pred_move = pred_move.numpy()
        pred_act = pred_act.numpy()
        # 有一定几率不使用模型给出的动作
        sample = np.random.rand()
        if sample < self.e_greed:  # 使用计算给出的操作

            move = self.better_move(hornet_x, player_x, hornet_skill1)
        else:
            move = np.argmax(pred_move)
        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)

        sample = np.random.rand()
        if sample < self.e_greed:  # 使用计算给出的操作
            act = self.better_action(
                soul, hornet_x, hornet_y, player_x, hornet_skill1)
        else:  # 如果使用模型给出的操作但是能量不够，就用模型给出的其他建议
            act = np.argmax(pred_act)
            if soul < 33:
                if act == 4 or act == 5:
                    pred_act[0][4] = -30
                    pred_act[0][5] = -30
            act = np.argmax(pred_act)
        self.e_greed = max(
            0.03, self.e_greed - self.e_greed_decrement)

        return move, act

    def better_move(self, hornet_x, player_x, hornet_skill1):  # 对方向和距离进行判断给出move风格
        dis = abs(player_x - hornet_x)
        dire = player_x - hornet_x
        if hornet_skill1:
            if dis < 6:
                if dire > 0:
                    return 1
                else:
                    return 0
            else:
                if dire > 0:
                    return 2
                else:
                    return 3

        if dis < 2.5:
            if dire > 0:
                return 1
            else:
                return 0
        elif dis < 5:
            if dire > 0:
                return 2
            else:
                return 3
        else:
            if dire > 0:
                return 0
            else:
                return 1

    def better_action(self, soul, hornet_x, hornet_y, player_x, hornet_skill1):  # 对距离、能量进行判断给出操作风格
        dis = abs(player_x - hornet_x)
        if hornet_skill1:
            if dis < 3:
                return 6
            else:
                return 1  # 没事就a

        if hornet_y > 34 and dis < 5 and soul >= 33:
            return 4

        if dis < 1.5:
            return 6
        elif dis < 5:
            if hornet_y > 32:  # 在空中
                return 6
            else:
                act = np.random.randint(self.act_dim)
                if soul < 33:
                    while act == 4 or act == 5:
                        act = np.random.randint(self.act_dim)
                return act
        elif dis < 12:
            act = np.random.randint(2)
            return 2 + act  # 没事就跳，安全的很
        else:
            return 6
