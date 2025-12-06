# -*- coding: utf-8 -*-
import sys
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox
from main_window import Ui_MainWindow
from edit_range import EditRangeWindow
from roller import NameRoller
import random
from PySide2.QtGui import QIcon
import os

icon_path = os.path.join(os.path.dirname(__file__), "icon.png")

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("抽签器")
        self.setFixedSize(342, 324)
        #self.setWindowIcon(QIcon(icon_path))
        self.setWindowIcon(QIcon("icon.png"))


        self.roller = NameRoller(parent=self.centralwidget)
        self.roller.setGeometry(self.textBrowser.geometry())
        self.textBrowser.hide()
        self.roller.show()

        self.rangeDlg = EditRangeWindow(self)
        self.rangeDlg.rangeSelected.connect(self.on_range_selected)

        self.pushButton.clicked.connect(self.start_roll)   # “开始抽签”
        self.pushButton_2.clicked.connect(self.stop_roll)  # “停止”
        self.pushButton_3.clicked.connect(self.open_range_editor)

        self.currentNames = []

    # ---------- 选定范围 ----------
    def open_range_editor(self):
        if self.rangeDlg.df is not None:
            self.rangeDlg.show()
            self.rangeDlg.raise_()
            self.rangeDlg.activateWindow()
            return

        if self.rangeDlg.quick_load():
            self.rangeDlg.show()
            self.rangeDlg.raise_()
            self.rangeDlg.activateWindow()
            return

        ok = self.rangeDlg.first_time_load()
        if ok:
            self.rangeDlg.show()
            self.rangeDlg.raise_()
            self.rangeDlg.activateWindow()

    def on_range_selected(self, names: list):
        for i in range(random.randint(50, 500)):
            random.shuffle(names)
        names.insert(0, '开始抽签')
        self.currentNames = names
        self.roller.update_names(names)
        del names[0]
        self.statusBar().showMessage(f"已选 {len(names)} 人")

    # ---------- 开始滚 ----------
    def start_roll(self):
        if not self.currentNames:
            QMessageBox.information(self, "提示", "请先选定抽签范围！")
            return
        self.pushButton.setEnabled(False)   # 防重复
        self.roller.start()

    # ---------- 停 ----------
    def stop_roll(self):
        if self.roller._timer.isActive():
            self.roller.stop()
            winner = self.roller.current()
            #self.statusBar().showMessage(f"中奖：{winner}")
            #QMessageBox.information(self, "抽签结果", f"恭喜：{winner}")
            self.pushButton.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    #app.setWindowIcon(QIcon(icon_path))
    app.setWindowIcon(QIcon("icon.png"))
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())