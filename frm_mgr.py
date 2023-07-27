from tkinter import ttk, Tk


class FrmManager:
    """
    功能面板管理
    """

    def __init__(self, tk: Tk):
        """
        :param tk: 窗口 Tk 对象
        """
        self._tk = tk

    def create_frm(self, name: str) -> ttk.Frame:
        """
        创建面板
        :param name: 面板名称
        :return: 新建的面板
        """
        pass

    def resume(self, frm: ttk.Frame):
        """
        重新显示面板
        :param frm: 面板
        :return: None
        """
        frm.pack(side='left', fill='both', padx=5, pady=5, expand=True)

    def hide_frm(self, frm: ttk.Frame):
        """
        隐藏面板，并清理环境
        :param frm: 面板
        :return: None
        """
        frm.pack_forget()
        pass
