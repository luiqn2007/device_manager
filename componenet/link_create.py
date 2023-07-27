import json
import shutil
import tkinter as tk
import os
from tkinter import ttk, filedialog, Tk, messagebox
from typing import Literal, Iterable, Union
from os import path

from frm_mgr import FrmManager
from file import File
import winapi


class WrappedList:
    def __init__(self, lst: tk.Listbox):
        """
        打包的列表组件和文件列表
        """
        self.widget = lst  # type: tk.Listbox
        self.files = []  # type: list[File]

    def update(self):
        """
        刷新显示内容
        :return: None
        """
        self.widget.delete(0, 'end')
        for file in self.files:
            self.widget.insert('end', file.real_path)

    def clear(self):
        """
        清空
        :return: None
        """
        self.files.clear()
        self.update()

    def delete_selected(self):
        """
        删除选中内容
        :return: None
        """
        self.files = list(
            map(lambda tp: tp[1], filter(lambda tp: tp[0] not in self.widget.curselection(), enumerate(self.files))))
        self.update()

    def append(self, files: Literal[""] | Iterable[str]):
        """
        向列表添加文件/目录
        :param files: 添加路径
        :return: None
        """
        if files == "" or len(files) == 0 or (len(files) == 1 and len(files[0]) == 0):
            return
        for file in filter(lambda f: f.is_exist, map(File, files)):
            self.files.append(file)
        self.update()


class Mgr(FrmManager):

    def __init__(self, gui: Tk):
        """
        _src: 源文件相关
        _dst: 目标目录相关
        _process: 进度条所在面板
        """
        super().__init__(gui)
        self._src = None  # type: WrappedList
        self._dst = None  # type: WrappedList
        self._process = None  # type: tk.Listbox

    def create_frm(self, name: str) -> ttk.Frame:
        frm = ttk.Frame(self._tk, name=name)
        # 区域1 选择已选文件
        f1 = ttk.Frame(frm, height=20)
        f1.pack(fill='x')
        ttk.Label(f1, text="源文件：").pack(side='left')
        ttk.Button(f1, text="选择文件", command=lambda: self._src.append(filedialog.askopenfilenames())) \
            .pack(side='left')
        ttk.Button(f1, text="选择目录", command=lambda: self._src.append([filedialog.askdirectory()])) \
            .pack(side='left')
        ttk.Button(f1, text="删除", command=lambda: self._src.delete_selected()).pack(side='left')
        ttk.Button(f1, text="清空", command=lambda: self._src.clear()).pack(side='left')
        ttk.Button(f1, text='从文件导入', command=lambda: self._import_symbol_record()).pack(side='left')
        # 区域2 已选文件
        lst_src = tk.Listbox(frm, height=10, selectmode=tk.EXTENDED)
        lst_src.pack(fill='x')
        self._src = WrappedList(lst_src)
        # 区域3 选择目标目录
        f2 = ttk.Frame(frm)
        f2.pack(fill='x')
        ttk.Label(f2, text="目标目录：").pack(side='left')
        ttk.Button(f2, text="选择目录", command=lambda: self._dst.append([filedialog.askdirectory()])) \
            .pack(side='left')
        ttk.Button(f2, text="删除", command=lambda: self._dst.delete_selected()).pack(side='left')
        ttk.Button(f2, text="清空", command=lambda: self._dst.clear()).pack(side='left')
        # 区域4 目标目录
        lst_dst = tk.Listbox(frm, height=10, selectmode=tk.EXTENDED)
        lst_dst.pack(fill='x')
        self._dst = WrappedList(lst_dst)
        # 区域5 选项
        ttk.Button(frm, text='创建符号链接', command=self._create_symbol_links).pack(anchor='w')
        ttk.Button(frm, text='将源文件移动至第一个目标目录并在原位置及剩余位置创建符号链接',
                   command=self._move_and_create_symbol_links).pack(anchor='w')
        # 区域6 进度
        f6 = tk.LabelFrame(frm, text='进度状态')
        f6.pack(fill='both')
        lst_proc = tk.Listbox(f6, selectmode=tk.BROWSE)
        lst_proc.pack(fill='both')
        self._process = lst_proc
        lst_proc.insert('end', '无任务')

        return frm

    def _create_symbol_links(self):
        """
        创建符号链接
        :return: None
        """
        lst_proc = self._process
        lst_proc.delete(0, 'end')
        # 检查文件名是否冲突
        file_map_by_name = {}  # type: dict[str, list[File]]
        for file in self._src.files:
            if file.basename in file_map_by_name:
                file_map_by_name[file.basename].append(file)
            else:
                file_map_by_name[file.basename] = [file]
        err_msg = ''
        for name in file_map_by_name:
            arr = file_map_by_name[name]
            if len(arr) > 1:
                err_msg += f'文件重复：{name}'
                for file in arr:
                    err_msg += f'\n{file.real_path}'
        if len(err_msg) > 0:
            messagebox.showerror('文件重复', err_msg)
            return
        lst_proc.insert('end', '文件重复性检查完成')

        # 检查文件是否已存在
        for file in self._dst.files:
            for pp in os.scandir(file.real_path):
                name = os.path.basename(pp)
                if name in file_map_by_name:
                    if len(err_msg) > 0:
                        err_msg += '\n'
                    err_msg += f'{file.real_path}: {name} 已存在'
                    continue
        if len(err_msg) > 0:
            messagebox.showerror('文件已存在', err_msg)
            return
        lst_proc.insert('end', '文件存在性检查完成')

        # 检查管理员权限
        winapi.require_admin()
        while not winapi.is_admin():
            if messagebox.askretrycancel('权限不足', '需要管理员权限运行'):
                winapi.require_admin()
            else:
                return

        # 创建软连接
        count = len(self._src.files)
        for index, file in enumerate(self._src.files):
            for dp in self._dst.files:
                winapi.make_symbol_in(file.real_path, dp.real_path, file.basename, file.is_directory)
                lst_proc.insert('end', f'{index + 1}/{count} {file.real_path} <- {dp.real_path}/{file.basename}')

    def _move_and_create_symbol_links(self):
        """
        将源文件移动到第一个目标目录，并创建符号链接
        :return: None
        """
        lst_proc: tk.Listbox = self._process
        lst_proc.delete(0, 'end')
        # 没有目标目录时不执行
        if len(self._dst.files) == 0:
            return
        # 异常信息
        err_msg = ''
        # 检查文件名是否冲突
        file_map_by_name = {}  # type: dict[str, list[File]]
        for file in self._src.files:
            if file.basename in file_map_by_name:
                file_map_by_name[file.basename].append(file)
            else:
                file_map_by_name[file.basename] = [file]
        for name in file_map_by_name:
            files = file_map_by_name[name]
            if len(files) > 1:
                err_msg += f'文件重复：{name}'
                for file in files:
                    err_msg += f'\n{file.real_path}'
        if len(err_msg) > 0:
            messagebox.showerror('文件重复', err_msg)
            return
        lst_proc.insert('end', '文件重复性检查完成')

        # 检验文件是否被占用
        for file in self._src.files:
            used_file = Mgr._reverse_check_file_used(file.real_path)
            if used_file is None:
                continue
            err_msg += f'{used_file} 已被占用'
        if len(err_msg) > 0:
            messagebox.showerror('文件被占用', err_msg)
            return
        lst_proc.insert('end', '文件占用校验完成')

        # 检查文件是否已存在
        for file in self._dst.files:
            for sub_file in os.scandir(file.real_path):
                name = path.basename(sub_file)
                if name in file_map_by_name:
                    if len(err_msg) > 0:
                        err_msg += '\n'
                    err_msg += f'{file}: {name} 已存在'
                    continue
        if len(err_msg) > 0:
            messagebox.showerror('文件已存在', err_msg)
            return
        lst_proc.insert('end', '文件存在性检查完成')

        # 移动文件并创建符号链接
        def copy_function(__src, __dst):
            """
            shutil.copy2 的副本，向列表中添加信息
            :param __src: 源文件
            :param __dst: 目标文件
            :return: None
            """
            lst_proc.insert('end', f'  move {__src} to {__dst}...')
            shutil.copy2(__src, __dst)
            lst_proc.delete('end')
            lst_proc.insert('end', f'  move {__src} to {__dst} √')
            pass

        for file in self._src.files:
            # 移动源文件到新目录
            move_to = self._dst.files[0]
            lst_proc.insert('end', f'move {file.real_path} to {move_to.real_path}...')
            shutil.move(file.real_path, move_to.real_path, copy_function)
            # 新的源文件
            src_path = path.join(move_to.real_path, file.basename)
            # 在源目录创建符号链接
            lst_proc.insert('end', src_path)
            winapi.make_symbol_in(src_path, path.dirname(file.real_path), file.basename, file.is_directory)
            dst_len = len(self._dst.files)
            lst_proc.insert('end', f'0/{dst_len}  <- {path.dirname(file.real_path)}/{file.basename}')
            # 在剩余目录中创建符号链接
            for idx, dst in enumerate(self._dst.files[1:]):
                winapi.make_symbol_in(src_path, dst.real_path, file.basename, file.is_directory)
                lst_proc.insert('end', f'{idx + 1}/{dst_len}  <- {path.dirname(file.real_path)}/{file.basename}')

    def _import_symbol_record(self):
        """
        从 json 文件导入，json 文档要求：
        {
            "src": [ ... ] // 源文件列表
            "dst": [ ... ] // 目标文件列表
        }
        :return: None
        """
        file = filedialog.askopenfile(mode='r', defaultextension='.json', filetypes=[('JSON 文件', ['.json', '.*'])])
        if file is None:
            return
        self._src.clear()
        self._dst.clear()
        with file:
            conf = json.load(file)
            self._src.append(conf.src)
            self._dst.append(conf.dst)

    @staticmethod
    def _reverse_check_file_used(p: str) -> Union[None, str]:
        """
        检查目录或文件是否被占用
        :param p: 目录或文件地址
        :return: 若被占用，返回被占用文件或目录的地址
        """
        if os.path.isdir(p):
            # 检查目录本身是否占用
            if winapi.is_directory_open(p):
                return p
            # 递归检查目录下各文件和目录是否被占用
            for sub_file in os.scandir(p):
                used_file = Mgr._reverse_check_file_used(sub_file.path)
                if used_file is None:
                    continue
                return used_file
            # 无占用
            return None
        else:
            # 检查文件是否被占用
            return p if winapi.is_file_used(p) else None


mgr = None


def obtain(gui):
    global mgr
    if mgr is None:
        mgr = Mgr(gui)
    return mgr
