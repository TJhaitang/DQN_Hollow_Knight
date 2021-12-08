import random
import collections
import numpy as np
import pickle
import os


class ReplayMemory:  # 管理经验池
    def __init__(self, max_size, file_name):
        self.size = max_size
        self.count = 0
        self.file_name = file_name
        self.buffer = collections.deque(maxlen=max_size)  # 200，大约是一局半的操作量

    def append(self, exp):  # 将单次操作放入缓存区：操作、操作前后状态、reward
        self.count += 1
        self.buffer.append(exp)

    def sample(self, batch_size):
        # 在缓存区中随机抽batch_size个样本用来训练
        mini_batch = random.sample(self.buffer, batch_size)  # 10

        obs_batch, action_batch, reward_batch, next_obs_batch, done_batch = [], [], [], [], []

        for experience in mini_batch:
            s, a, r, s_p, done = experience
            obs_batch.append(s)
            action_batch.append(a)
            reward_batch.append(r)
            next_obs_batch.append(s_p)
            done_batch.append(done)
        # 格式化一下
        return np.array(obs_batch).astype('float32'), \
            np.array(action_batch).astype('int32'), np.array(reward_batch).astype('float32'),\
            np.array(next_obs_batch).astype('float32'), np.array(
                done_batch).astype('float32')

    def save(self, file_name):  # 将缓存区的内容存文件
        count = 0
        for x in os.listdir(file_name):
            count += 1
        file_name = file_name + "/memory_" + str(count) + ".txt"
        pickle.dump(self.buffer, open(file_name, 'wb'))
        print("Save memory:", file_name)

    def load(self, file_name):  # 将经验池中的数据读入缓存区
        self.buffer = pickle.load(open(file_name, 'rb'))
        return self.buffer

    def __len__(self):
        return len(self.buffer)
