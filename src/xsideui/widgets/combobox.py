from typing import Union

from ..utils.qt_compat import (QComboBox, QCompleter, QListView, QWidget, Qt, QEvent, QIcon, QStyledItemDelegate, QTimer)
from .xarrowbutton import XArrowButton
from ..icon import IconName
from ..xenum import XSize
from ..i18n import XI18N


class XComboBox(QComboBox):
    """下拉框组件"""

    def __init__(
            self,
            size: Union[XSize, str] = XSize.DEFAULT,
            border_visible: bool = True,
            searchable: bool = False,
            parent=None
    ):
        """初始化下拉框组件。

            Args:
                size: 组件的尺寸规格。影响输入框高度、字体大小以及下拉箭头的大小。
                    支持 XSize 枚举或字符串（'small', 'default', 'large'）。
                border_visible: 是否显示外边框。设为 False 时通常用于表格嵌入或紧凑型 UI。
                searchable: 是否支持输入搜索。设为 True 时组件变为可编辑并启用自动补全过滤。
                parent: 父级组件。
            """
        super().__init__(parent)
        self.setObjectName("xcombobox")
        self._size_value = self._parse_size(size)
        self._show_border = border_visible
        self._searchable = searchable
        self._item_keys = []  # 存储选项的翻译键
        self._set_listview()
        self._setup_arrow()
        if searchable:
            self._setup_search()
        self._update_style()


    def _setup_search(self):
        """启用输入搜索：可编辑 + 自动补全过滤"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)

        self._completer = QCompleter(self.model(), self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(self._completer)

        popup = self._completer.popup()
        if popup:
            popup.setObjectName("xcombobox-search-popup")
            # 使用 QStyledItemDelegate，使 QSS 的 ::item 规则（内边距/悬停/选中）生效
            popup.setItemDelegate(QStyledItemDelegate(popup))
            # 去掉原生阴影，与下拉列表样式一致
            popup.setWindowFlags(popup.windowFlags() | Qt.NoDropShadowWindowHint)
            popup.installEventFilter(self)

        self.lineEdit().setPlaceholderText("搜索...")
        self.lineEdit().installEventFilter(self)
        self._arrow_btn.clicked.connect(self._open_search_popup)
        self.setCurrentIndex(-1)

    def _open_search_popup(self):
        """点击触发：清空当前选中并弹出全部选项，提示可搜索"""
        if self.currentIndex() >= 0:
            self.lineEdit().clear()
            self.setCurrentIndex(-1)
        self._completer.setCompletionPrefix('')
        self._completer.complete()

    def _setup_arrow(self):
        """设置自定义箭头标签"""
        self._arrow_btn = XArrowButton(icon_name=IconName.DOWN, parent=self)
        self._arrow_btn.setObjectName("xcombobox-arrow")
        if not self._searchable:
            self._arrow_btn.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._arrow_btn.show()

    def _update_button_positions(self):
        """动态计算箭头位置与尺寸"""
        h = self.height()
        w = self.width()
        btn_size = int(h * 0.6)
        margin = (h - btn_size) // 2
        self._arrow_btn.setFixedSize(btn_size, btn_size)
        self._arrow_btn.move(w - btn_size - 6, margin)
        self._arrow_btn.raise_()
        right_padding = btn_size + 10
        if self._searchable and self.lineEdit():
            self.lineEdit().setTextMargins(0, 0, right_padding, 0)
        else:
            self.setStyleSheet(f"QComboBox#xcombobox {{ padding-right: {right_padding}px; }}")



    def resizeEvent(self, event):
        """调整箭头位置"""
        super().resizeEvent(event)
        self._update_button_positions()

    def showEvent(self, event):
        """显示时确保位置正确"""
        super().showEvent(event)
        self._update_button_positions()

    def _parse_size(self, size: Union[XSize, str]) -> str:
        """解析尺寸参数"""
        if isinstance(size, XSize):
            return size.value
        return size

    def _update_style(self):
        """更新样式属性"""
        # 这里的 QSS 也可以根据 self._size_value 动态微调文字大小和内边距
        border = "none" if not self._show_border else "visible"
        self.setProperty("borderVisible", border)
        self.setProperty("componentSize", self._size_value)
        # 强制刷新样式
        self.style().unpolish(self)
        self.style().polish(self)



    def _set_listview(self):
        """设置列表视图并移除阴影"""
        view = QListView()
        view.setObjectName("xcombobox-view")
        self.setView(view)
        container_obj = self.view().parent()
        if isinstance(container_obj, QWidget):
            container_obj.setWindowFlags(container_obj.windowFlags() | Qt.NoDropShadowWindowHint)

    def showPopup(self):
        """显示下拉列表"""
        super().showPopup()
        # 修正某些版本下弹出层宽度不一致的问题
        popup = self.view().parentWidget()
        if popup:
            popup.setMinimumWidth(self.width())
            # 设置弹出层与 combobox 之间的间距
            popup.move(popup.x(), popup.y() + 6)


    def set_border_visible(self, visible: bool):
        """设置边框可见性

        Returns:
            self
        """
        self._show_border = visible
        self._update_style()
        return self

    def set_size(self, size: Union[XSize, str]):
        """设置组件尺寸

        Returns:
            self
        """
        self._size_value = self._parse_size(size)
        self._update_style()
        return self

    def get_size(self) -> str:
        """获取当前尺寸

        Returns:
            尺寸字符串值
        """
        return self._size_value

    def addItem(self, icon=None, text=None, userData=None):
        """
        添加选项（兼容 Qt 原生两种调用形式）

        Args:
            icon: 图标（QIcon 或图标路径）。调用 addItem(text) 时忽略。
            text: 选项文本或翻译键。当 icon 为 str 时按 addItem(text) 处理。
            userData: 用户数据（可选）
        """
        if text is None and isinstance(icon, str):
            text = icon
            icon = None
        if text is None:
            text = ""
        self._item_keys.append(text)
        translated = XI18N.x_tr(text)

        if icon:
            super().addItem(icon, translated, userData)
        else:
            super().addItem(translated, userData)



    def addItems(self, texts: list):
        """
        批量添加选项

        Args:
            texts: 选项文本或翻译键列表
        """
        for text in texts:
            self.addItem(text=text)



    def clear(self):
        super().clear()
        self._item_keys.clear()

    def retranslateUi(self):
        """当语言切换或文本更新时调用"""
        if not self._item_keys:
            return
        for i, text_key in enumerate(self._item_keys):
            if text_key and i < self.count():
                translated = XI18N.x_tr(text_key)
                self.setItemText(i, translated)


    def eventFilter(self, obj, event):
        """搜索模式下点击输入框时打开下拉列表并清空选中；弹层显示时向下偏移留间距"""
        if self._searchable:
            if obj is self.lineEdit() and event.type() == QEvent.MouseButtonPress:
                self._open_search_popup()
            elif obj is self._completer.popup() and event.type() == QEvent.Show:
                popup = obj
                QTimer.singleShot(0, lambda p=popup: p.move(p.x(), p.y() + 6))
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        """显式捕获事件"""
        if event.type() == QEvent.LanguageChange:
            # 强制触发刷新
            self.retranslateUi()
        super().changeEvent(event)




