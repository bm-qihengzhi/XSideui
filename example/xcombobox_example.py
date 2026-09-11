"""
XComboBox Example 下拉框组件示例
展示下拉框组件的使用
"""
import sys


try:
    from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
except ImportError:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

from src.xsideui import XLabel, XComboBox, XSize, XWidget, XDivider,  IconName, XIcon, XColor, XI18N, XPushButton



class XComboBoxExample(XWidget):
    """XComboBox Example Window 下拉框组件示例窗口"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Setup user interface 设置用户界面"""
        self.set_title("XComboBox Example - 下拉框组件示例")
        self.resize(600, 600)

        main_widget = QWidget()
        self.addWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        items = ['Primary','小炒黄牛肉','生烧排骨','皮蛋擂辣椒' ]

        main_layout.addWidget(XLabel("Default", style=XLabel.Style.H3))
        main_layout.addWidget(XDivider())
        combo_box = XComboBox(searchable=True)
        combo_box.addItems(items)
        main_layout.addWidget(combo_box)

        main_layout.addWidget(XLabel("尺寸", style=XLabel.Style.H3))
        main_layout.addWidget(XDivider())

        size_layout = QHBoxLayout()
        main_layout.addLayout(size_layout)


        combo1 = XComboBox(size=XSize.LARGE, border_visible=True)
        combo1.addItems(items)
        combo1.addItem(XIcon(IconName.SEND, size=16, color=XColor.PRIMARY).icon(),'Primary')
        combo1.addItem(XIcon(IconName.SEND, size=16, color=XColor.PRIMARY).icon(),'Success')
        combo1.currentIndexChanged.connect(lambda :self._on_combo_changed)
        size_layout.addWidget(combo1)


        combo2 = XComboBox(size=XSize.DEFAULT, border_visible=True)
        combo2.addItems(items)
        combo2.currentIndexChanged.connect(lambda idx: print(f"选中: {combo2.itemText(idx)}"))
        size_layout.addWidget(combo2)

        combo3 = XComboBox(size=XSize.SMALL, border_visible=True)
        combo3.addItems(items)
        size_layout.addWidget(combo3)

        combo4 = XComboBox(size=XSize.MINI, border_visible=True)
        combo4.addItems(items)
        size_layout.addWidget(combo4)

        btn = XPushButton('语言切换')
        btn.clicked.connect(self.chang_langs)
        main_layout.addWidget(btn)

    def chang_langs(self):
        langs = XI18N.current_lang
        if langs == "zh_CN":
            XI18N.set_language("en_US")
        else:
            XI18N.set_language("zh_CN")
        print(langs)





    def _on_combo_changed(self,index):
        print(f"选中{index}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    XI18N.set_language("zh_CN")
    window = XComboBoxExample()
    window.show()
    sys.exit(app.exec_())
