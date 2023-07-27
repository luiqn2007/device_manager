import os.path
import json
import tkinter
from tkinter import ttk, Listbox, filedialog, messagebox
from file import File
from threading import Thread
from typing import Union

from frm_mgr import FrmManager


class Mgr(FrmManager):

    def __init__(self, gui):
        super().__init__(gui)
        self.lst_src = None  # type: Listbox
        self.lst_link = None  # type: Listbox
        self.lst_log = None  # type: Listbox
        self.data = {}  # type: dict[str, list[File]]
        self.is_working = False
        self.working_stop = False

    def create_frm(self, name: str) -> ttk.Frame:
        frm = ttk.Frame(self._tk, name=name)
        # 区域1 控制按钮
        ctr = ttk.Frame(frm)
        ctr.pack(fill='x')
        ttk.Button(ctr, text='选择目录', command=lambda: self._select_dir()).pack(side='left')
        ttk.Button(ctr, text='清空', command=lambda: self._clear_data()).pack(side='left')
        ttk.Button(ctr, text='删除选中链接', command=lambda: self._delete_selected_links()).pack(side='left')
        ttk.Button(ctr, text='删除文件链接', command=lambda: self._delete_selected_file_links()).pack(side='left')
        ttk.Button(ctr, text='导出选中文件', command=lambda: self._export_select_files()).pack(side='left')
        ttk.Button(ctr, text='导出选中链接', command=lambda: self._export_select_links()).pack(side='left')
        ttk.Button(ctr, text='导出所有链接', command=lambda: self._export_all()).pack(side='left')
        ttk.Button(ctr, text='停止查找', command=lambda: self._stop_search()).pack(side='left')
        # 区域2 源文件
        frm_src = ttk.Labelframe(frm, text='源文件')
        frm_src.pack(fill='x')
        self.lst_src = Listbox(frm_src, selectmode=tkinter.SINGLE)
        self.lst_src.pack(fill='both')
        self.lst_src.bind('<Button-1>', lambda evt: self._display_selected_links())
        # 区域3 链接文件
        frm_link = ttk.Labelframe(frm, text='链接文件')
        frm_link.pack(fill='x')
        self.lst_link = Listbox(frm_link, selectmode=tkinter.EXTENDED)
        self.lst_link.pack(fill='both')
        # 区域4 log
        frm_log = ttk.Labelframe(frm, text='Log')
        frm_log.pack(fill='x')
        self.lst_log = Listbox(frm_log)
        self.lst_log.pack(fill='both')
        return frm

    def fresh(self):
        """
        刷新列表显示
        :return: None
        """
        # 获取选择的选项
        selected = self.lst_src.curselection()
        selected = selected[0] if len(selected) > 0 else None
        selected = None if selected is None else self.lst_src.get(selected)[3:]
        # 清空
        self.lst_src.delete(0, 'end')
        self.lst_link.delete(0, 'end')
        # 插入
        new_selected = -1
        for p in self.data.keys():
            if os.path.isdir(p):
                self.lst_src.insert('end', f'[D]{p}')
            else:
                self.lst_src.insert('end', f'[F]{p}')
            if p == selected:
                new_selected = self.lst_src.size() - 1
        # 选中
        self.lst_src.selection_clear(0)
        if new_selected >= 0:
            self.lst_src.selection_set(new_selected)
        pass

    def _clear_data(self):
        """
        清空数据
        :return: None
        """
        self.data.clear()
        self.fresh()
        pass

    def _select_dir(self):
        """
        选择一个目录，遍历所有文件并将符号链接及其源文件插入列表
        :return: None
        """
        # 检查是否有正在进行的任务
        if self.is_working:
            messagebox.showerror('任务进行中', '当前存在正在进行的任务，无法进行新任务')
            return
        # 选择目录
        directory = filedialog.askdirectory()
        if directory is None or directory == "" or not os.path.isdir(directory):
            return
        self.lst_log.delete(0, 'end')
        self.lst_log.insert('end', f'loading {directory}')
        self.lst_log.insert('end', '...')
        last_idx = self.lst_log.size() - 1

        # 插入文件到记录
        def insert_to_data(f: File):
            if f.real_path in self.data:
                self.data[f.real_path].append(f)
            else:
                self.data[f.real_path] = [f]
            self.fresh()

        # 遍历目录，递归查找符号链接
        # 返回 True 表示查询中断
        def walk_dir(file_dir: File) -> bool:
            if self.working_stop:
                self.is_working = False
                self.working_stop = False
                return True
            self.lst_log.delete(last_idx, last_idx)
            self.lst_log.insert(last_idx, f'...{file_dir.path}')
            # 目录本身是符号链接
            if file_dir.is_symbol_link:
                insert_to_data(file_dir)
                return False
            # 遍历目录内容
            try:
                for entry in os.scandir(file_dir.real_path):
                    if self.working_stop:
                        self.is_working = False
                        self.working_stop = False
                        return True
                    self.lst_log.delete(last_idx, last_idx)
                    self.lst_log.insert(last_idx, f'...{file_dir.path}')
                    file = File(entry.path)
                    if file.is_symbol_link:
                        insert_to_data(file)
                    elif file.is_directory:
                        if walk_dir(file):
                            return True

                return False
            except PermissionError:
                self.lst_log.insert('end', f'  -{file_dir.real_path} 权限不足')
                return False

        self.is_working = True
        self.working_stop = False
        td = Thread(target=lambda: walk_dir(File(directory)))
        td.start()
        # walk_dir(File(directory))

    def _delete_selected_links(self):
        """
        删除选中的符号链接
        :return: None
        """
        # 是否已选中
        cur = self.lst_src.curselection()
        if len(cur) == 0:
            return

        cur = self.lst_src.get(cur)[3:]

        to_remove = set(map(lambda i: self.lst_link.get(i), self.lst_link.curselection()))
        # 删除所有链接
        for link in to_remove:
            os.remove(link)
        # 更新数据
        self.data[cur] = list(filter(lambda f: not (f.path in to_remove), self.data[cur]))
        self.fresh()

    def _delete_selected_file_links(self):
        """
        删除选中文件的所有符号链接
        :return: None
        """
        # 是否已选中
        cur = self.lst_src.curselection()
        if len(cur) == 0:
            return

        cur = self.lst_src.get(cur)[3:]
        # 删除所有链接
        for link in self.data[cur]:
            os.remove(link.path)
        # 更新数据
        del self.data[cur]
        self.fresh()

    def _export_select_files(self):
        """
        导出选择的文件的所有符号链接
        :return: None
        """
        # 是否已选中
        cur = self.lst_src.curselection()
        if len(cur) == 0:
            return

        cur = self.lst_src.get(cur)[3:]
        # 收集信息
        out = {'src': [cur], 'dst': list(map(lambda f: f.path, self.data[cur]))}
        # 保存
        out_file = filedialog.asksaveasfile(mode='w', defaultextension='.json', filetypes=[('JSON', '.json')])
        if out_file is None:
            return
        json.dump(out, out_file)
        out_file.flush()
        out_file.close()

    def _export_select_links(self):
        """
        导出选中的符号链接
        :return: None
        """
        # 是否已选中
        cur = self.lst_src.curselection()
        if len(cur) == 0:
            return
        cur = self.lst_src.get(cur)[3:]
        selections = map(lambda i: self.data[cur][i].path, self.lst_link.curselection())
        # 收集信息
        out = {'src': [cur], 'dst': list(selections)}
        # 保存
        out_file = filedialog.asksaveasfile(mode='w', defaultextension='.json', filetypes=[('JSON', '.json')])
        if out_file is None:
            return
        json.dump(out, out_file)
        out_file.flush()
        out_file.close()

    def _export_all(self):
        """
        导出所有符号链接
        :return: None
        """
        # 保存目录
        save_dir = filedialog.askdirectory()
        if save_dir == '':
            return
        # 保存数据
        data = map(lambda path, files: {'src': [path], 'dst': list(map(lambda f: f.path, files))}, self.data.items())
        for obj in data:
            src_path = obj['src'][0]  # type: str
            file_name = src_path.replace('/', '_').replace('\\', '_').replace(':', '_') + '.json'
            file_io = open(os.path.join(save_dir, file_name), mode='w')
            os.fdopen(fd=0, mode='w', )
            json.dump(obj, file_io)
            file_io.flush()
            file_io.close()

    def _display_selected_links(self):
        """
        显示当前选中文件的软连接
        :return: None
        """
        self.lst_link.delete(0, 'end')
        cur_select = self.lst_src.curselection()  # type: list[int]
        cur_select = None if cur_select is None or len(cur_select) == 0 else cur_select[0]  # type: int
        cur_select = None if cur_select is None else self.lst_src.get(cur_select, cur_select)[0][3:]  # type: str

        if cur_select is None or cur_select not in self.data:
            return

        for path in map(lambda f: f.path, self.data[cur_select]):
            self.lst_link.insert('end', path)

    def _stop_search(self):
        self.working_stop = True


mgr = None


def obtain(gui):
    global mgr
    if mgr is None:
        mgr = Mgr(gui)
    return mgr
