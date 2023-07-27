import tkinter as tk
from tkinter import ttk
from typing import Union

from frm_mgr import FrmManager
from componenet.link_manager import obtain as link_manager
from componenet.link_create import obtain as link_create
from componenet.case_manager import obtain as case_manager


current_frm: Union[ttk.Frame, None] = None
current_mgr: Union[FrmManager, None] = None


def switch_panel(gui, name, obtain):
    global current_mgr
    global current_frm

    # 隐藏所有面板
    if current_frm and current_mgr:
        current_mgr.hide_frm(current_frm)

    # 切换面板
    current_mgr = obtain(gui)
    if name in gui.children:
        # 切换面板
        current_frm = gui.children[name]
    # 检查面板是否存在
    else:
        # 创建面板
        current_frm = current_mgr.create_frm(name)

    # 显示面板
    current_mgr.resume(current_frm)


def main():
    gui = tk.Tk()
    gui.title("Manger")
    gui.geometry("800x600")
    # 控制器
    controller = ttk.Frame(gui, name='ctr')
    controller.pack(fill='y', side='left')
    ttk.Button(controller, text="链接管理", command=lambda: switch_panel(gui, 'link_mgr', link_manager)).pack()
    ttk.Button(controller, text="链接创建", command=lambda: switch_panel(gui, 'link_new', link_create)).pack()
    ttk.Button(controller, text="大小写敏感", command=lambda: switch_panel(gui, 'case_mgr', case_manager)).pack()

    gui.mainloop()


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    main()
