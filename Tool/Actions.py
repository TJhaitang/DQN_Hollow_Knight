# Define the actions we may need during training
# You can define your actions here

from Tool.SendKey import PressKey, ReleaseKey
from Tool.WindowsAPI import grab_screen
import time
import cv2
import threading

# Hash code for key we may use: https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
UP_ARROW = 0x26
DOWN_ARROW = 0x28
LEFT_ARROW = 0x25
RIGHT_ARROW = 0x27

L_SHIFT = 0xA0
A = 0x41
C = 0x43
X = 0x58
Z = 0x5A

# move actions
# 0

# 以下是一些操作，内容就是函数名


def Nothing():
    ReleaseKey(LEFT_ARROW)
    ReleaseKey(RIGHT_ARROW)
    pass

# Move
# 0


def Move_Left():
    PressKey(LEFT_ARROW)
    time.sleep(0.01)
# 1


def Move_Right():
    PressKey(RIGHT_ARROW)
    time.sleep(0.01)

# 2


def Turn_Left():
    PressKey(LEFT_ARROW)
    time.sleep(0.01)
    ReleaseKey(LEFT_ARROW)

# 3


def Turn_Right():
    PressKey(RIGHT_ARROW)
    time.sleep(0.01)
    ReleaseKey(RIGHT_ARROW)

# ----------------------------------------------------------------------
# action
# 0


def Attack():
    PressKey(X)
    time.sleep(0.15)
    ReleaseKey(X)
    # Nothing()
    time.sleep(0.01)
# 1
# def Attack_Down():#下砍没有意义
#     PressKey(DOWN_ARROW)
#     PressKey(X)
#     time.sleep(0.05)
#     ReleaseKey(X)
#     ReleaseKey(DOWN_ARROW)
#     time.sleep(0.01)
# 1


def Attack_Up():
    # print("Attack up--->")
    PressKey(UP_ARROW)
    PressKey(X)
    time.sleep(0.11)
    ReleaseKey(X)
    ReleaseKey(UP_ARROW)
    # Nothing()
    time.sleep(0.01)

# JUMP
# 2


def Short_Jump():
    PressKey(C)
    PressKey(DOWN_ARROW)
    PressKey(X)
    time.sleep(0.2)
    ReleaseKey(X)
    ReleaseKey(DOWN_ARROW)
    ReleaseKey(C)
    # Nothing()
# 3


def Mid_Jump():
    PressKey(C)
    time.sleep(0.2)
    PressKey(X)
    time.sleep(0.2)
    ReleaseKey(X)
    ReleaseKey(C)
    # Nothing()


# Skill
# 4
# def Skill():#向前放技能太弱了
#     PressKey(Z)
#     PressKey(X)
#     time.sleep(0.1)
#     ReleaseKey(Z)
#     ReleaseKey(X)
#     time.sleep(0.01)
# 4
def Skill_Up():
    PressKey(UP_ARROW)
    PressKey(Z)
    PressKey(X)
    time.sleep(0.15)
    ReleaseKey(UP_ARROW)
    ReleaseKey(Z)
    ReleaseKey(X)
    # Nothing()
    time.sleep(0.15)
# 5


def Skill_Down():
    PressKey(DOWN_ARROW)
    PressKey(Z)
    PressKey(X)
    time.sleep(0.2)
    ReleaseKey(X)
    ReleaseKey(DOWN_ARROW)
    ReleaseKey(Z)
    # Nothing()
    time.sleep(0.3)


# Rush
# 6
def Rush():
    PressKey(L_SHIFT)
    time.sleep(0.1)
    ReleaseKey(L_SHIFT)
    # Nothing()
    time.sleep(0.2)
    PressKey(X)
    time.sleep(0.03)
    ReleaseKey(X)


# Cure
def DoNothing():
    Nothing()
    time.sleep(0.3)


def Look_up():
    PressKey(UP_ARROW)
    time.sleep(0.1)
    ReleaseKey(UP_ARROW)


def restart():
    station_size = (230, 230, 1670, 930)
    while True:  # 页面不黑了就是可以开始了
        station = cv2.resize(cv2.cvtColor(grab_screen(
            station_size), cv2.COLOR_RGBA2RGB), (1000, 500))
        if station[187][300][0] != 0:
            time.sleep(1)
        else:
            break
    # 起立、选关、进入、开打！！
    time.sleep(1)
    Look_up()
    time.sleep(1.5)
    Look_up()
    time.sleep(1)
    while True:
        station = cv2.resize(cv2.cvtColor(grab_screen(
            station_size), cv2.COLOR_RGBA2RGB), (1000, 500))
        if station[187][612][0] > 200:
            PressKey(C)  # 判断到选择了第一个难度就按C进入游戏
            time.sleep(0.1)
            ReleaseKey(C)
            break
        else:
            Look_up()
            time.sleep(0.2)


Actions = [Attack, Attack_Up,
           Short_Jump, Mid_Jump, Skill_Up,
           Skill_Down, Rush, DoNothing]  # 加入了DoNothing选项，有时候无为也是一种有为，而且乐得无为
Directions = [Move_Left, Move_Right, Turn_Left, Turn_Right]


def take_action(action, playerx, hx):
    # if(action <= 3):#想做“砍就要对着砍！”的小设定，但效果一般，换种解释就是写的太清楚了这就不是学习是脚本了
    #     if(playerx < hx):
    #         print("right")
    #         Directions[3]()
    #     else:
    #         print("left")
    #         Directions[2]()
    Actions[action]()


def take_direction(direc):
    Directions[direc]()

# def runDo(direction, action, player_x, hornet_x):
#     take_direction(direction)
#     take_action(action, player_x, hornet_x)


class TackAction(threading.Thread):  # 如你所见想开线程但没有用这个因为不好调度
    def __init__(self, threadID, name, direction, action, player_x, hornet_x):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.direction = direction
        self.action = action
        self.x1 = player_x
        self.x2 = hornet_x

    def run(self):
        take_direction(self.direction)
        take_action(self.action, self.x1, self.x2)
