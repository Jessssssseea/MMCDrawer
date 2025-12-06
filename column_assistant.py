# 文件：column_assistant.py
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QListWidget, QPushButton, QDialogButtonBox,
                               QCheckBox, QGroupBox, QGridLayout, QListWidgetItem)

class ColumnAssistant(QDialog):
    """弹窗：自动识别表头 + 手动勾选分类列"""
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.setWindowTitle("列识别向导")
        self.resize(500, 400)
        self._init_ui()
        self._guess_columns()

    def _init_ui(self):
        main = QVBoxLayout(self)

        main.addWidget(QLabel("已识别到以下列，请勾选可作为“分类依据”的列："))

        self.list_w = QListWidget()
        self.list_w.setSelectionMode(QListWidget.ExtendedSelection)
        main.addWidget(self.list_w)

        self.bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.bb.accepted.connect(self.accept)
        self.bb.rejected.connect(self.reject)
        main.addWidget(self.bb)

    def _guess_columns(self):
        """自动勾选候选列：文本型、非空值多、唯一值<50、重复率高"""
        import numpy as np
        n_rows = len(self.df)
        for col in self.df.columns:
            s = self.df[col].dropna()
            unique_cnt = s.nunique()
            text_ratio = s.apply(lambda x: isinstance(x, str)).mean()
            repeat_ratio = 1 - unique_cnt / len(s) if len(s) else 0

            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            # 候选规则：文本占比高、非空多、唯一值少、重复率高
            checked = (text_ratio > 0.8 and
                       len(s) / n_rows > 0.8 and
                       unique_cnt < 50 and
                       repeat_ratio > 0.2)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.list_w.addItem(item)

    def selected_columns(self):
        return [self.list_w.item(i).text()
                for i in range(self.list_w.count())
                if self.list_w.item(i).checkState() == Qt.Checked]