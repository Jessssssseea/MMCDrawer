# -*- coding: utf-8 -*-
import random
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QLabel
from PySide2.QtCore import Qt


class NameRoller(QLabel):
    def __init__(self, names=None, parent=None):
        super().__init__(parent)
        self.names = names or []
        self._index = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        # 样式
        self.setStyleSheet("font: 40pt '微软雅黑'; color: #ff6600;")
        self.setAlignment(Qt.AlignCenter)
        self._tick()          # 先显示一个

    # ---------- 开始滚动 ----------
    def start(self):
        if self.names:
            self._timer.start(50)   # 每 50 ms 切一次

    # ---------- 停止 ----------
    def stop(self):
        self._timer.stop()
        # 最后再给一个随机
        self._index = random.randrange(len(self.names))
        self._tick()

    # ---------- 内部切名字 ----------
    def _tick(self):
        if self.names:
            self.setText(self.names[self._index])
            self._index = (self._index + 1) % len(self.names)

    # ---------- 当前中奖人 ----------
    def current(self):
        return self.names[self._index] if self.names else ""

    # ---------- 动态更新名单 ----------
    def update_names(self, names):
        self.names = names
        self._index = 0
        self._tick()