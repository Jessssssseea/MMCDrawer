# -*- coding: utf-8 -*-
import os, sys
import pandas as pd
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class EditRangeWindow(QDialog):
    rangeSelected = Signal(list)          # 返回 List[姓名]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑抽签范围")
        self.resize(400, 500)
        self.df = None
        self.units = []         # (header_check, group_box)

        # 读取上次记忆
        self.settings = QSettings('MyCompany', 'DrawLots')
        self.lastFile = self.settings.value('lastFile', '')
        self.lastMethod = self.settings.value('lastMethod', '按组别')

        # -------------------- 顶部 --------------------
        self.method_combo = QComboBox()
        self.method_combo.addItems(["按组别", "按班级", "按性别", "按姓氏"])
        self.load_btn = QToolButton()
        self.load_btn.setText("加载表格...")
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("分类方式："))
        top_layout.addWidget(self.method_combo)
        top_layout.addWidget(self.load_btn)
        top_layout.addStretch()

        # -------------------- 动态复选区域 --------------------
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)

        # -------------------- 底部按钮 --------------------
        self.select_btn = QPushButton("全选")
        self.invert_btn = QPushButton("反选")
        self.ok_btn = QPushButton("确定")
        bot_layout = QHBoxLayout()
        bot_layout.addWidget(self.select_btn)
        bot_layout.addWidget(self.invert_btn)
        bot_layout.addStretch()
        bot_layout.addWidget(self.ok_btn)

        # -------------------- 主布局 --------------------
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(bot_layout)

        # -------------------- 信号 --------------------
        self.load_btn.clicked.connect(self.load_excel)
        self.method_combo.currentTextChanged.connect(self.rebuild_checks)
        self.select_btn.clicked.connect(self.on_select_btn)
        self.invert_btn.clicked.connect(self.invert_select)
        self.ok_btn.clicked.connect(self.submit)

    # --------------------------------------------------
    # 首次被主窗口调用（按钮第一次点击）
    # --------------------------------------------------
    def first_time_load(self):
        """返回 True 表示成功加载并走完列向导；False 表示取消或失败。"""
        open_dir = os.path.dirname(self.lastFile) if os.path.isfile(self.lastFile) else ""
        path, _ = QFileDialog.getOpenFileName(self, "打开 Excel", open_dir,
                                              "Excel (*.xlsx *.xls)")
        if not path:
            return False
        try:
            self.df = pd.read_excel(path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取失败：{e}")
            self.df = None
            return False

        # 列向导
        from column_assistant import ColumnAssistant
        dlg = ColumnAssistant(self.df, self)
        if dlg.exec_() != QDialog.Accepted:
            self.df = None
            return False

        cats = dlg.selected_columns()
        if "姓名" not in cats:
            cats.append("姓名")
        self.df = self.df[cats].dropna(subset=["姓名"])
        if "姓氏" not in self.df.columns:
            self.df["姓氏"] = self.df["姓名"].astype(str).str[0]

        # 同步下拉框
        self.method_combo.clear()
        self.method_combo.addItems([c for c in self.df.columns if c != "姓氏"] + ["姓氏"])

        # 记住路径
        self.lastFile = path
        self.settings.setValue('lastFile', path)
        self.settings.setValue('lastColumns', cats)

        # 生成复选框
        self.rebuild_checks()
        return True

    def quick_load(self):
        """第二次以后直接读上次文件+列配置，返回 bool 表示成功"""
        if not os.path.isfile(self.lastFile):
            return False

        # 读表
        try:
            self.df = pd.read_excel(self.lastFile)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取失败：{e}")
            self.df = None
            return False

        # 直接用上次的列
        cols = self.settings.value("lastColumns", "")  # 保存的是 strList
        if not cols:
            return False  # 没有列记忆，走不了快速

        # 转成 list
        if isinstance(cols, str):  # 单值保护
            cols = [cols]
        else:
            cols = list(cols)

        # 同第一次逻辑
        if "姓名" not in cols:
            cols.append("姓名")
        self.df = self.df[cols].dropna(subset=["姓名"])
        if "姓氏" not in self.df.columns:
            self.df["姓氏"] = self.df["姓名"].astype(str).str[0]

        # 同步下拉框
        self.method_combo.clear()
        self.method_combo.addItems([c for c in self.df.columns if c != "姓氏"] + ["姓氏"])
        self.method_combo.setCurrentText(self.lastMethod)

        # 生成复选框
        self.rebuild_checks()
        return True

    # --------------------------------------------------
    # 手动加载（供“加载表格...”按钮使用）
    # --------------------------------------------------
    def load_excel(self):
        ok = self.first_time_load()
        if ok:
            self.settings.setValue('lastMethod', self.method_combo.currentText())

    # --------------------------------------------------
    # 重建复选框
    # --------------------------------------------------
    def rebuild_checks(self):
        # 1. 清空旧控件
        for header, gb in self.units:
            header.deleteLater()
            gb.deleteLater()
        self.units.clear()

        # 2. 把布局里所有剩余 item 全部清掉
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            if item.spacerItem():
                del item

        if self.df is None:
            return

        method = self.method_combo.currentText().strip()
        if not method or method not in self.df.columns:
            method = '姓名'
        key_col = method
        self.df[key_col] = self.df[key_col].fillna('未分类')

        for key, sub in self.df.groupby(key_col, sort=False):
            header = QCheckBox(f"{key}（{len(sub)} 人）")
            header.setTristate(True)
            header.setChecked(True)

            gb = QGroupBox()
            vlay = QVBoxLayout(gb)
            for _, row in sub.iterrows():
                chk = QCheckBox(row["姓名"])
                chk.setChecked(True)
                chk.setProperty("isName", True)
                vlay.addWidget(chk)

            header.toggled.connect(lambda c, g=gb: self.sync_group(g, c))
            for chk in gb.findChildren(QCheckBox):
                if chk.property("isName"):
                    chk.clicked.connect(lambda h=header, g=gb: self.update_header(h, g))

            unit = QWidget()
            unit_layout = QVBoxLayout(unit)
            unit_layout.setContentsMargins(0, 0, 0, 0)
            unit_layout.addWidget(header)
            unit_layout.addWidget(gb)
            self.scroll_layout.addWidget(unit)
            self.units.append((header, gb))

        self.scroll_layout.addStretch()
        self.update_header_states()

    # --------------------------------------------------
    # 组级点击 → 同步人名
    # --------------------------------------------------
    def sync_group(self, group_box: QGroupBox, checked: bool):
        for chk in group_box.findChildren(QCheckBox):
            if chk.property("isName"):
                chk.setChecked(checked)
        for header, gb in self.units:
            self.update_header(header, gb)

    # --------------------------------------------------
    # 人名点击 → 更新组级三态
    # --------------------------------------------------
    def update_header(self, header: QCheckBox, group_box: QGroupBox):
        inner = [chk for chk in group_box.findChildren(QCheckBox) if chk.property("isName")]
        selected = sum(chk.isChecked() for chk in inner)
        header.blockSignals(True)
        if selected == 0:
            header.setCheckState(Qt.Unchecked)
        elif selected == len(inner):
            header.setCheckState(Qt.Checked)
        else:
            header.setCheckState(Qt.PartiallyChecked)
        header.blockSignals(False)
        self.update_select_btn_text()

    def update_header_states(self):
        for header, gb in self.units:
            self.update_header(header, gb)

    # --------------------------------------------------
    # 底部「全选 / 取消全选」
    # --------------------------------------------------
    def on_select_btn(self):
        all_selected = all(chk.isChecked() for chk in self.name_checks())
        for chk in self.name_checks():
            chk.setChecked(not all_selected)
        self.update_header_states()

    def update_select_btn_text(self):
        all_selected = all(chk.isChecked() for chk in self.name_checks())
        self.select_btn.setText("取消全选" if all_selected else "全选")

    # --------------------------------------------------
    # 反选
    # --------------------------------------------------
    def invert_select(self):
        for chk in self.name_checks():
            chk.setChecked(not chk.isChecked())
        self.update_header_states()

    # --------------------------------------------------
    # 提交
    # --------------------------------------------------
    def submit(self):
        selected = [chk.text() for chk in self.name_checks() if chk.isChecked()]
        if not selected:
            QMessageBox.warning(self, "提示", "请至少选择 1 人！")
            return
        self.rangeSelected.emit(selected)
        self.accept()

    # --------------------------------------------------
    # 工具：只拿人名复选框
    # --------------------------------------------------
    def name_checks(self):
        return [chk for chk in self.findChildren(QCheckBox)
                if chk.property("isName")]