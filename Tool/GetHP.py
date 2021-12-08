import win32gui
import win32api
import win32process
import ctypes

# 导入动态链接库（方法重了不过不想改了
Psapi = ctypes.WinDLL('Psapi.dll')
Kernel32 = ctypes.WinDLL('kernel32.dll')
# 进程权限
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010


def EnumProcessModulesEx(hProcess):  # 用来获得一些动态链接库的基址
    buf_count = 256
    while True:
        LIST_MODULES_ALL = 0x03
        buf = (ctypes.wintypes.HMODULE * buf_count)()
        buf_size = ctypes.sizeof(buf)
        needed = ctypes.wintypes.DWORD()
        if not Psapi.EnumProcessModulesEx(hProcess, ctypes.byref(buf), buf_size, ctypes.byref(needed), LIST_MODULES_ALL):
            raise OSError('EnumProcessModulesEx failed')
        if buf_size < needed.value:
            buf_count = needed.value // (buf_size // buf_count)
            continue
        count = needed.value // (buf_size // buf_count)
        return map(ctypes.wintypes.HMODULE, buf[:count])


class Hp_getter():
    def __init__(self):
        # 获得空洞骑士的进程id
        hd = win32gui.FindWindow(None, "Hollow Knight")
        pid = win32process.GetWindowThreadProcessId(hd)[1]
        self.process_handle = win32api.OpenProcess(0x1F0FFF, False, pid)  # 高权限
        self.kernal32 = ctypes.windll.LoadLibrary(
            r"C:\\Windows\\System32\\kernel32.dll")
        self.check = 0
        self.hx = 0
        # 获取全部进程地址
        hProcess = Kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
            False, pid)
        hModule = EnumProcessModulesEx(hProcess)
        # 获得以下两个dll的内存地址是为了获得boss和自己的信息
        for i in hModule:
            temp = win32process.GetModuleFileNameEx(
                self.process_handle, i.value)
            if temp[-15:] == "UnityPlayer.dll":
                self.UnityPlayer = i.value
            if temp[-8:] == "mono.dll":
                self.mono = i.value
        self.load_boss_hp_address()
        self.load_boss_location()
        self.load_play_location_address()
        self.load_self_hp_address()
        self.load_souls_address()

    # 通过base_address和offset_list获取一个内存地址
    def load_address_from(self, base_address, offset_list):
        offset_address = ctypes.c_ulonglong()
        self.kernal32.ReadProcessMemory(
            int(self.process_handle), ctypes.c_void_p(base_address), ctypes.byref(offset_address), 4, None)
        for offset in offset_list[:-1]:
            self.kernal32.ReadProcessMemory(int(
                self.process_handle), ctypes.c_void_p(offset_address.value + offset), ctypes.byref(offset_address), 4, None)
        return offset_address.value+offset_list[-1]

    def get_num_from(self, address):  # 在内存地址里面取数
        offset_address = ctypes.c_long()
        self.kernal32.ReadProcessMemory(int(
            self.process_handle), ctypes.c_void_p(address), ctypes.byref(offset_address), 4, None)
        return offset_address.value

    # 各个数据的内存地址
    def load_souls_address(self):
        base_address = self.UnityPlayer + 0x00FA0998  # 用cheat engine搜出来的一串指针指向自己的信息所在内存
        offset_list = [0x10, 0x64, 0x3C, 0xC, 0x60, 0x120]
        self.souls_address = self.load_address_from(base_address, offset_list)

    def load_self_hp_address(self):
        base_address = self.mono + 0x1F50AC
        offset_list = [0x3B4, 0x24, 0x34, 0x48, 0x50, 0xE4]  # 用cheat engine搜索
        self.self_hp_address = self.load_address_from(
            base_address, offset_list)

    def load_play_location_address(self):
        base_address = self.UnityPlayer + 0x00FEF994
        x_offset_list = [0x4C, 0x4, 0x4, 0x10, 0x0, 0x44]
        self.x_address = self.load_address_from(base_address, x_offset_list)

        y_offset_list = [0x24, 0x104, 0x6C, 0x10, 0xAC, 0xC]
        self.y_address = self.load_address_from(base_address, y_offset_list)

    # 以下内存地址只能找到大黄蜂的，其他的还需要再搜呜呜呜

    def load_boss_hp_address(self):
        base_address = self.UnityPlayer + 0x00FEF994
        # offset_list = [0x54, 0x8, 0x1C, 0x1C, 0x7C, 0x18, 0xAC]  # 奶酪
        # 这里按理说可以搜到一个适用于所有boss的偏移量串
        offset_list = [0x58, 0x8C, 0x40, 0xFC, 0x5C, 0x18, 0xAC]
        self.boss_hp_address = self.load_address_from(
            base_address, offset_list)

    def load_boss_location(self):
        base_address = self.UnityPlayer + 0x00FEF994
        x_offset_list = [0x20, 0x54, 0x24, 0x20, 0x5C, 0xC]
        self.boss_x_address = self.load_address_from(
            base_address, x_offset_list)

        y_offset_list = [0x54, 0x8, 0x1C, 0x1C, 0x14, 0xAC]
        self.boss_y_address = self.load_address_from(
            base_address, y_offset_list)

# 没有做安全性检查，不过训练的时候没出过问题所以阿弥陀佛
    def get_souls(self):
        return self.get_num_from(self.souls_address)

    def get_self_hp(self):
        return self.get_num_from(self.self_hp_address)

    def get_boss_hp(self):
        hp = self.get_num_from(self.boss_hp_address)
        if hp > 900:
            return 901
        elif hp < 0:
            return -1
        return hp

    def get_play_location(self):  # 获取自己的位置
        xx = ctypes.c_float()
        self.kernal32.ReadProcessMemory(
            int(self.process_handle), ctypes.c_void_p(self.x_address), ctypes.byref(xx), 4, None)

        yy = ctypes.c_float()
        self.kernal32.ReadProcessMemory(
            int(self.process_handle), ctypes.c_void_p(self.y_address), ctypes.byref(yy), 4, None)

        return xx.value, yy.value

    def get_hornet_location(self):  # 获取boss的位置
        xx = ctypes.c_float()
        self.kernal32.ReadProcessMemory(
            int(self.process_handle), ctypes.c_void_p(self.boss_x_address), ctypes.byref(xx), 4, None)

        yy = ctypes.c_float()
        self.kernal32.ReadProcessMemory(
            int(self.process_handle), ctypes.c_void_p(self.boss_y_address), ctypes.byref(yy), 4, None)

        if xx.value > 14 and xx.value < 40:
            self.hx = xx.value
        return self.hx, yy.value
