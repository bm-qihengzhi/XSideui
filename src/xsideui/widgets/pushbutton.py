"""
XPushButton Component 按钮组件
支持多种变体、颜色、尺寸以及高性能图标状态联动的按钮组件
"""
from functools import partial
from typing import List, Dict, Union, Optional


from ..utils.qt_compat import QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QIcon, Qt, Signal, QPoint, QSize, QTimer, QEvent
from .menu import XMenu
from ..icon import IconName, XIcon
from ..icon.xicon_engine import XIconEngine
from ..icon.xicon_theme import xicon_theme_adapter
from ..xenum import XColor, XButtonVariant, XSize
from ..theme import theme_manager
from ..i18n import XI18N


class XPushButton(QPushButton):
    """Push Button Component 按钮组件

    一个可自定义的按钮组件，支持多种变体、颜色和尺寸，并集成了高性能图标系统。

    Features:
        - 属性驱动样式 (QSS Property-driven)
        - 高性能图标状态切换 (QIcon Normal/Active/Disabled)
        - 自动感知明暗主题切换
        - 支持链式调用 API
    """

    def __init__(
            self,
            text: str = "",
            icon: Union[str, IconName, None] = None,
            variant: Union[XButtonVariant, str] = XButtonVariant.SOLID,
            color: Union[XColor, str] = XColor.PRIMARY,
            size: Union[XSize, str] = XSize.DEFAULT,
            disabled: bool = False,
            parent=None
    ):
        """初始化按钮组件

        Args:
            text: 按钮文本
            icon: 图标名称
            variant: 按钮变体（solid/outlined/filled/text/link）
            color: 按钮颜色（primary/success/warning/danger/secondary/tertiary）
            size: 按钮尺寸（large/default/small/mini）
            disabled: 是否禁用
            parent: 父组件
        """
        super().__init__(parent)
        self._text_key = text
        self._variant = variant.value if isinstance(variant, XButtonVariant) else variant
        self._color = color.value if isinstance(color, XColor) else color
        self._size = size.value if isinstance(size, XSize) else size
        self._x_icon_name = self._resolve_icon_name(icon)
        self.setObjectName("xpushbutton")

        self.set_variant(variant)
        self.set_color(color)
        self.set_size(size)
        self.set_disabled(disabled)

        self._is_loading = False
        self._loading_frame = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading_animation)
        self._pre_loading_icon = None

        xicon_theme_adapter.theme_changed.connect(self._refresh_icon_style)


        icon_size = self._get_icon_size()
        self.setIconSize(QSize(icon_size, icon_size))

        # 初始翻译
        self.retranslateUi()


    def _get_icon_size(self) -> int:
        """根据按钮尺寸获取对应的图标尺寸

        Returns:
            图标尺寸（像素）
        """
        try:
            height_str = theme_manager.height.get(self._size, "32px")
            height_px = int(height_str.replace("px", ""))
            icon_size = int(height_px * 0.6)
            return max(12, min(32, icon_size))
        except Exception:
            size_map = {
                "large": 40,
                "default": 32,
                "small": 28,
                "mini": 24
            }
            return size_map.get(self._size, 20)

    def retranslateUi(self):
        """当语言切换或文本更新时调用"""
        if not self._text_key:
            super().setText("")
            return

        # 调用我们刚刚写的适配函数
        translated = XI18N.x_tr(self._text_key)
        super().setText(translated)
        self._refresh_icon_style()

    def changeEvent(self, event):
        """监听 I18nManager 发出的 LanguageChange 事件"""
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def setText(self, text: str):
        """重写 setText，确保外部修改文本时同步更新翻译键"""
        self._text_key = text
        self.retranslateUi()



    def set_x_icon(self, icon: Union[str, None]) -> 'XPushButton':
        """设置图标名称并自动应用状态变色图标包"""
        self._x_icon_name = icon
        self._refresh_icon_style()
        return self

    def _update_loading_animation(self):
        """更新加载动画帧"""
        if not self._is_loading:
            return


        self._loading_frame = (self._loading_frame + 1) % 12
        if self._variant == "solid":
            color = "#F1F1F1"
        else:
            color = getattr(theme_manager.colors, self._color, "#165dff")

        dpr = self.devicePixelRatioF()
        icon_size = self._get_icon_size()
        physical_size = int(icon_size * dpr)

        pixmap = XIconEngine.create_animated_pixmap(
            name="loading",
            size=physical_size,
            color=color,
            frame=self._loading_frame,
            total_frames=12
        )

        if pixmap:
            pixmap.setDevicePixelRatio(dpr)
            self.setIcon(QIcon(pixmap))

    def showEvent(self, event):
        super().showEvent(event)
        window = self.window().windowHandle()
        if window:
            window.screenChanged.connect(self._on_dpi_changed, Qt.UniqueConnection)

    def _on_dpi_changed(self):
        # # 延迟刷新图标，确保 devicePixelRatioF() 已更新
        # print('屏幕切换')
        # QTimer.singleShot(100, self._refresh_icon_style)
        """防抖处理：只在信号停止后的 150ms 执行一次刷新"""
        # 如果计时器正在运行，先停止它（丢弃之前的信号）
        if hasattr(self, '_dpi_timer'):
            # print(f'信号来了：{self.devicePixelRatioF()}')
            self._dpi_timer.stop()
        else:
            # print(f'准备更新:{self.devicePixelRatioF()}')
            self._dpi_timer = QTimer(self)
            self._dpi_timer.setSingleShot(True)
            self._dpi_timer.timeout.connect(self._refresh_icon_style)

        # 重新开始计时
        self._dpi_timer.start(150)

    def _resolve_icon_name(self, icon: Union[str, IconName, None]) -> Optional[str]:
        """解析图标参数，将 IconName 枚举转换为字符串"""
        if icon is None:
            return None
        if isinstance(icon, IconName):
            return icon.value
        return str(icon)

    def _refresh_icon_style(self):
        """刷新图标样式，根据当前按钮状态获取高性能复合图标包"""
        if not hasattr(self, '_x_icon_name') or not self._x_icon_name or self._color is None:
            return

        if self._variant == "solid":
            base_color = "#F1F1F1"
        else:
            base_color = getattr(theme_manager.colors, self._color, "#165dff")


        icon_size = self._get_icon_size()
        status_icon = XIcon.get(name=self._x_icon_name,size=icon_size, color=base_color).icon()
        if status_icon:
            self.setIcon(status_icon)
            self.setIconSize(QSize(icon_size, icon_size))
        if not self.text():
            self.setMaximumWidth(icon_size // 0.5)
        else:
            self.setMaximumWidth(99999)

    def set_variant(self, variant: Union[XButtonVariant, str]) -> 'XPushButton':
        """设置按钮变体"""
        if isinstance(variant, XButtonVariant):
            variant = variant.value
        elif variant not in ["solid", "outlined", "filled", "text", "link"]:
            variant = "solid"

        self._variant = variant
        self.setProperty("variant", variant)
        self._update_style()
        self._refresh_icon_style()
        return self

    def set_color(self, color: Union[XColor, str]) -> 'XPushButton':
        """设置按钮颜色"""
        if isinstance(color, XColor):
            color = color.value
        elif color not in ["primary", "success", "warning", "danger", "tertiary", "secondary"]:
            color = "primary"

        self._color = color
        self.setProperty("color", color)
        self._update_style()
        self._refresh_icon_style()
        return self

    def set_size(self, size: Union[XSize, str]) -> 'XPushButton':
        """设置按钮尺寸"""
        if isinstance(size, XSize):
            size = size.value
        elif size not in ["large", "default", "small", "mini"]:
            size = "default"

        self._size = size
        self.setProperty("button-size", size)
        self._update_style()
        self._refresh_icon_style()

        icon_size = self._get_icon_size()
        self.setIconSize(QSize(icon_size, icon_size))

        return self

    def set_icon_position(self, position: str):
        """设置图标位置

        Args:
            position: 'left' 或 'right'
        """
        if position == "right":
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)
        return self

    def set_disabled(self, disabled: bool) -> 'XPushButton':
        """设置按钮禁用状态"""
        self.setEnabled(not disabled)
        return self

    def _update_style(self):
        """刷新 QSS 样式"""
        self.style().unpolish(self)
        self.style().polish(self)

    def is_loading(self) -> bool:
        """获取按钮是否处于加载状态"""
        return self._is_loading

    def set_loading(self, loading: bool) -> 'XPushButton':
        """设置按钮加载状态"""
        if self._is_loading == loading:
            return self

        self._is_loading = loading

        if loading:
            self._pre_loading_icon = self._x_icon_name
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._loading_timer.start(100)
        else:
            self._loading_timer.stop()
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.set_x_icon(self._pre_loading_icon)

        return self

    # --- Getter 方法 ---
    def variant(self) -> str:
        """获取当前按钮变体"""
        return self._variant

    def color(self) -> str:
        """获取当前按钮颜色"""
        return self._color

    def size_type(self) -> str:
        """获取当前按钮尺寸"""
        return self._size


class XPushButtonGroup(QWidget):
    """Button Group Component 按钮组组件

    通过属性驱动的方式，无损地组合 XPushButton，自动处理圆角拼接和边框重叠。
    """

    def __init__(
            self,
            buttons: List[QWidget] = None,
            vertical: bool = False,
            spacing: int = -1,
            parent=None
    ):
        """初始化按钮组组件

        Args:
            buttons: 按钮列表
            vertical: 是否垂直排列，默认 False（水平排列）
            spacing: 按钮间距，-1 表示边框重叠（默认）
            parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("xbuttongroup")

        self._vertical = vertical
        self._buttons = []

        self._layout = QVBoxLayout() if vertical else QHBoxLayout()
        self._layout.setSpacing(0 if spacing == -1 else spacing)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        if buttons:
            self.add_buttons(buttons)

    def add_button(self, button: QWidget) -> 'XButtonGroup':
        """添加单个按钮到组"""
        if button not in self._buttons:
            self._buttons.append(button)
            self._layout.addWidget(button)
            self._update_buttons_position()
        return self

    def add_buttons(self, buttons: List[QWidget]) -> 'XButtonGroup':
        """添加多个按钮到组"""
        for button in buttons:
            self._buttons.append(button)
            self._layout.addWidget(button)
        self._update_buttons_position()
        return self

    def remove_button(self, button: QWidget) -> None:
        """从组中移除按钮"""
        if button in self._buttons:
            self._buttons.remove(button)
            self._layout.removeWidget(button)
            button.setParent(None)
            button.setProperty("position", None)
            self._update_buttons_position()

    def _update_buttons_position(self) -> None:
        """更新按钮的位置属性"""
        count = len(self._buttons)
        if count == 0:
            return

        for i, button in enumerate(self._buttons):
            if count == 1:
                pos = "single"
            elif i == 0:
                pos = "first"
            elif i == count - 1:
                pos = "last"
            else:
                pos = "middle"

            button.setProperty("position", pos)
            button.setProperty("group-vertical", self._vertical)

            button.style().unpolish(button)
            button.style().polish(button)

    def clear(self) -> None:
        """清空所有按钮"""
        while self._buttons:
            self.remove_button(self._buttons[0])


class XPushButtonDropdown(QWidget):
    """Dropdown Button Component 下拉按钮组件

    由主按钮和下拉箭头按钮组成，支持菜单功能。
    """
    clicked = Signal()
    menuTriggered = Signal(str)

    def __init__(
            self,
            text: str = "",
            menu_items: List[Dict] = None,
            variant: Union[str, "XButtonVariant"] = "solid",
            color: Union[str, "XColor"] = "primary",
            size: Union[str, "XSize"] = "default",
            icon: Union[str, "IconName"] = None,
            parent=None
    ):
        """初始化下拉按钮组件

        Args:
            text: 主按钮显示的文本
            menu_items: 菜单项列表，格式如 [{"text": "显示名称", "value": "触发值"}]
            variant: 按钮样式变体（solid/outlined/filled/text/link）
            color: 按钮主题颜色（primary/success/warning/danger/secondary/tertiary）
            size: 按钮尺寸规格（large/default/small/mini）
            icon: 主按钮左侧的图标名称
            parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("xsplitdropdownbutton")
        self._menu_items = menu_items or []
        self._btn_size = size
        self._variant = variant
        self._btn_col = color

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(1)
        self._layout.setAlignment(Qt.AlignVCenter)

        self.main_button = XPushButton(
            text=text, variant=variant, color=color, size=size, icon=icon
        )
        self.main_button.setProperty("position", "first")

        self.dropdown_button = XPushButton(
            text="", variant=variant, color=color, size=size, icon="down"
        )
        self.dropdown_button.setProperty("position", "last")

        self.main_button.clicked.connect(self.clicked.emit)
        self.dropdown_button.clicked.connect(self._show_menu)

        self.menu = XMenu(self)
        self._setup_menu()

        self._layout.addWidget(self.main_button)
        self._layout.addWidget(self.dropdown_button)

        self._apply_split_style()

    def _apply_split_style(self):
        """应用拆分按钮特有的圆角和边框样式"""
        self.main_button.setProperty("position", "first")
        self.dropdown_button.setProperty("position", "last")

        for btn in [self.main_button, self.dropdown_button]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.dropdown_button.setContentsMargins(0, 0, 0, 0)

    def _setup_menu(self):
        """解析菜单项数据并构建 XMenu 内容"""
        self.menu.clear()
        for item in self._menu_items:
            action = self.menu.addAction(item.get("text", ""))
            data = item.get("value", item.get("text"))
            action.triggered.connect(partial(self.menuTriggered.emit, data))

    def _show_menu(self):
        """计算弹出位置并显示下拉菜单"""
        if not self._menu_items:
            return

        popup_pos = self.dropdown_button.mapToGlobal(
            QPoint(0, self.dropdown_button.height() + 2)
        )
        self.menu.popup(popup_pos)

    def set_menu_items(self, items: list):
        """动态更新下拉菜单的内容

        Args:
            items: 新的菜单项列表
        """
        self._menu_items = items
        self._setup_menu()

    def setEnabled(self, enabled: bool):
        """重写设置禁用状态的方法

        Args:
            enabled: True 为启用，False 为禁用
        """
        super().setEnabled(enabled)
        self.main_button.setEnabled(enabled)
        self.dropdown_button.setEnabled(enabled)

        self._apply_split_style()

    def isEnabled(self) -> bool:
        """获取当前组件的启用状态"""
        return self.main_button.isEnabled()
