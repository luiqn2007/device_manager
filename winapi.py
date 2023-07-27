import ctypes
import sys
import os
import win32file
from ctypes import windll, wintypes
from ctypes.wintypes import WIN32_FIND_DATAW

kernel32 = windll.kernel32
user32 = windll.user32
shell32 = windll.shell32

# 具有关联的重新分析点的文件或目录，或作为符号链接的文件
FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


def find_first_file(p: str) -> WIN32_FIND_DATAW:
    """
    查找文件（夹）的文件属性
    :param p: 文件路径
    :return: 文件属性，详见 https://learn.microsoft.com/zh-cn/windows/win32/fileio/file-attribute-constants
    """
    find_result = wintypes.WIN32_FIND_DATAW()
    find_handle = kernel32.FindFirstFileW(p, ctypes.byref(find_result))
    kernel32.FindClose(find_handle)
    return find_result


# noinspection PyPep8Naming
def IsReparseTagNameSurrogate(dwReserved0) -> bool:
    """
    IsReparseTagNameSurrogate 宏，确定标记的关联重新分析点是否是另一个命名实体的代理项 (例如装载的文件夹) 。
    :param dwReserved0: 重新分析点
    :return: 与是否是软连接有关
    """
    return bool(dwReserved0 & 0x20000000)


def make_symbol_link(src: str, dst: str, is_directory: bool):
    """
    创建符号链接
    :param src: 源文件/目录
    :param dst: 目标文件/目录
    :param is_directory: 是否为目录
    :return: None
    """
    # return kernel32.CreateSymbolicLinkW(src, dst, 0x1 if is_directory else 0x0)
    print(f"link {src} <= {dst}")
    win32file.CreateSymbolicLink(dst, src, 1 if is_directory else 0)


def make_symbol_in(src: str, dst_dir: str, basename: str, is_directory: bool):
    """
    在某个目录创建符号链接
    :param src: 源文件
    :param dst_dir: 目标目录
    :param basename: 链接文件名
    :param is_directory: 是否为目录
    :return: None
    """
    make_symbol_link(src, os.path.join(dst_dir, basename), is_directory)


def is_admin() -> bool:
    """
    检查是否为管理员权限
    :return: 是否以管理员权限执行
    """
    try:
        return shell32.IsUserAnAdmin()
    except:
        return False


def require_admin():
    """
    请求管理员权限
    :return: None
    """
    if not is_admin():
        shell32.ShellExecuteW(None, 'runas', sys.executable, __file__, None, 1)


def is_file_used(p):
    """
    检查文件是否被占用
    :param p: 文件
    :return: 是否被占用
    """
    handle = None
    try:
        handle = win32file.CreateFile(p, win32file.GENERIC_READ,
                                      0, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, None)
        return int(handle) == win32file.INVALID_HANDLE_VALUE
    except:
        return True
    finally:
        try:
            win32file.CloseHandle(handle)
        except:
            pass


def is_directory_open(p):
    """
    检查目录是否被占用
    :param p: 目录
    :return: 是否被占用
    """
    try:
        os.listdir(p)
        return False
    except:
        return True
