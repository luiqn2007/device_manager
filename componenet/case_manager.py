import tkinter
import subprocess
from tkinter import ttk, filedialog

import winapi
from file import File
from frm_mgr import FrmManager


class Mgr(FrmManager):

    def __init__(self, tk):
        super().__init__(tk)
        self.log = None  # type: tkinter.Listbox

    def create_frm(self, name: str) -> ttk.Frame:
        frm = ttk.Frame(self._tk, name=name)

        # 开启/关闭
        ctr = ttk.Frame(frm)
        ctr.pack(fill='x')
        ttk.Button(ctr, text='开启', command=lambda: self._enable(False)).pack(side='left')
        ttk.Button(ctr, text='递归开启', command=lambda: self._enable(True)).pack(side='left')
        # 信息
        self.log = tkinter.Listbox(frm, selectmode=tkinter.BROWSE)
        self.log.pack(fill='both')

        return frm

    def _enable(self, recursive: bool):
        """
        设置开启
        :return: None
        """
        winapi.require_admin()
        dir = filedialog.askdirectory()
        if dir == '':
            return
        dir_file = File(dir)
        self.log.insert('end', f'enable {dir_file.real_path}')

        ps = subprocess.run(f'fsutil file setCaseSensitiveInfo \"{dir}\" enable{" recursive" if recursive else ""}')
        if ps.returncode == 0:
            self.log.insert('end', f'[OK]{str(ps.stdout)}')
        else:
            self.log.insert('end', f'[ERR]{ps.returncode}:{str(ps.stderr)}')


mgr = None


def obtain(tk):
    global mgr
    if mgr is None:
        mgr = Mgr(tk)
    return mgr

