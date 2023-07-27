import win32com.client

from winapi import *


class File:
    """
    文件信息

    Attributes:
        path                文件路径
        real_path           真实路径（解软、硬链接或快捷方式）
        is_directory        是否是文件夹
        is_file             是否是文件夹
        is_exist            是否存在
        is_symbol_link      是否是符号链接
        is_windows_link     是否是快捷方式
        hard_link_count     文件（夹）的硬链接数量
        size                文件大小
        basename            文件/目录名
    """

    def __init__(self, p: str):
        """
        获取文件信息
        :param p: 文件路径
        :return: 文件信息
        """
        self.path = p

        # 判断文件 or 文件夹
        self.is_directory = os.path.isdir(p)
        self.is_file = os.path.isfile(p)
        self.is_exist = self.is_file or self.is_directory
        if self.is_exist:
            s = os.stat(p)
            # 文件基本信息
            self.hard_link_count = s.st_nlink
            self.size = s.st_size
            # 判断链接
            self.is_windows_link = self.is_file and os.path.basename(p).endswith('.lnk')
            if self.is_windows_link:
                # 获取 lnk 目标
                shell = win32com.client.Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(p)
                real_path = str(shortcut.Targetpath)
                target = File(real_path)
                self.real_path = target.real_path
                self.is_symbol_link = False
                # 快捷方式可能无效或为网站等
                self.is_exist = target.is_exist
            else:
                # 检查符号链接
                attr = find_first_file(p)
                self.is_symbol_link = not (not attr.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) \
                                      and IsReparseTagNameSurrogate(attr.dwReserved0)
                self.real_path = os.path.realpath(p)
        else:
            self.real_path = None
            self.is_symbol_link = False
            self.is_windows_link = False
            self.hard_link_count = 0
            self.size = 0

        self.basename = os.path.basename(self.real_path) if self.is_exist else None

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
            and self.is_exist and other.is_exist \
            and self.real_path == other.real_path

