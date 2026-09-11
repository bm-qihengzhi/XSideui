from typing import Union

from ..utils.qt_compat import QFrame, QHBoxLayout, QLabel, QSizePolicy, QIcon, Signal, QPoint, Qt, QPushButton, QPainter, QColor, QRect, QSize

from ..icon import IconName, XIcon
from ..theme import theme_manager
from ..xenum import XColor
from .label import XLabel


_HOVER_MARGIN = 4


def _resolve_hover_radius() -> int:
    """从主题解析按钮 hover 背景圆角（radius_s），失败回退 4px"""
    try:
        return int(str(theme_manager.border_radius.get("s", "4px")).replace("px", "").strip())
    except (ValueError, TypeError):
        return 4


class _TitleBarButton(QPushButton):
    def __init__(self, icon_name, is_close=False, parent=None, rounded=False):
        super().__init__(parent)
        self._icon_name = icon_name
        self._is_close = is_close
        self._rounded = rounded
        self._hover_radius = _resolve_hover_radius() if rounded else 0
        self.setFixedSize(36, 36)
        self.setIconSize(QSize(16, 16))
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def setButtonIcon(self, icon_name):
        self._icon_name = icon_name
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        rect = self.rect()

        bg = None
        if self._is_close:
            if self.isDown():
                bg = QColor("#f1707a")
            elif self.underMouse():
                bg = QColor("#e81123")
        else:
            if self.isDown():
                bg = QColor(128, 128, 128, 40)
            elif self.underMouse():
                bg = QColor(128, 128, 128, 25)

        if bg is not None:
            if self._rounded:
                p.setRenderHint(QPainter.Antialiasing, True)
                p.setPen(Qt.NoPen)
                p.setBrush(bg)
                m = _HOVER_MARGIN
                p.drawRoundedRect(
                    rect.adjusted(m, m, -m, -m),
                    self._hover_radius,
                    self._hover_radius,
                )
                p.setRenderHint(QPainter.Antialiasing, False)
            else:
                p.fillRect(rect, bg)

        if self._is_close and (self.underMouse() or self.isDown()):
            color = "#FFFFFF"
        else:
            color = theme_manager.colors.secondary

        icon = XIcon.get(name=self._icon_name, size=16, color=color).icon()
        icon_size = self.iconSize()
        x = (rect.width() - icon_size.width()) // 2
        y = (rect.height() - icon_size.height()) // 2
        icon.paint(p, QRect(x, y, icon_size.width(), icon_size.height()))


class XTitleBar(QFrame):
    """标题栏组件"""

    windowMinimumed = Signal()
    windowMaximumed = Signal()
    windowsMaxOrNor = Signal()
    windowNormaled = Signal()
    windowClosed = Signal()
    windowMoved = Signal(QPoint)

    def __init__(
        self,
        title: str = "XSideUI",
        logo: str = '',
        show_min: bool = True,
        show_max: bool = True,
        show_close: bool = True,
        show_dark: bool = True,
        rounded_buttons: bool = False,
        parent=None
    ):
        """初始化标题栏

        Args:
            title: 窗口标题
            logo: 窗口图标路径
            show_min: 是否显示最小化按钮
            show_max: 是否显示最大化按钮
            show_dark: 是否显示明暗主题切换按钮
            show_close: 是否显示关闭按钮
            rounded_buttons: 窗口控制按钮 hover 背景是否使用内缩圆角
            parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("xtitlebar")
        self._title = title
        self._logo = logo or XIcon(name=IconName.XSIDEUI, color=XColor.PRIMARY).icon()
        self._show_min = show_min
        self._show_max = show_max
        self._show_dark = show_dark
        self._show_close = show_close
        self._rounded_buttons = rounded_buttons
        self._drag_pos = QPoint()
        self._is_dragging = False
        self.setMinimumHeight(36)
        
        theme_manager.initialize()
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 左侧：图标 + 标题
        self.left_layout = QHBoxLayout()
        self.left_layout.setContentsMargins(10, 0, 0, 0)
        self.left_layout.setSpacing(8)

        if self._logo:
            self.icon_label = QLabel()
            self.icon_label.setObjectName("xtitlebarlogo")
            self.icon_label.setFixedSize(18, 18)
            self.left_layout.addWidget(self.icon_label)

            self.set_logo(self._logo)

        self.title_label = XLabel(self._title)
        self.left_layout.addWidget(self.title_label)

        # 中间区：用来接收用户 add_widget 的组件
        self.middle_layout = QHBoxLayout()
        self.middle_layout.addStretch(1)

        # 右侧：按钮组
        self.right_layout = QHBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        self._setup_window_buttons()

        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.middle_layout, 1)
        self.main_layout.addLayout(self.right_layout)

    def add_widget(self, widget):
        """标题栏添加自定义组件"""
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        if self.middle_layout.count() == 0:
            self.middle_layout.addStretch(1)
        self.middle_layout.addWidget(widget)

    def _setup_window_buttons(self):
        if self._show_dark:
            icon_name = IconName.MOON if theme_manager.is_dark else IconName.SUN
            self.theme_btn = _TitleBarButton(icon_name, parent=self, rounded=self._rounded_buttons)
            self.theme_btn.clicked.connect(self._toggle_theme)
            self.right_layout.addWidget(self.theme_btn)

        if self._show_min:
            self.min_button = _TitleBarButton(IconName.MINUS, parent=self, rounded=self._rounded_buttons)
            self.min_button.clicked.connect(self.windowMinimumed.emit)
            self.right_layout.addWidget(self.min_button)

        if self._show_max:
            self.max_button = _TitleBarButton(IconName.FULL_SCREEN, parent=self, rounded=self._rounded_buttons)
            self.max_button.clicked.connect(self._toggle_maximize)
            self.right_layout.addWidget(self.max_button)

        if self._show_close:
            self.close_button = _TitleBarButton(IconName.CLOSE, is_close=True, parent=self, rounded=self._rounded_buttons)
            self.close_button.clicked.connect(self.windowClosed.emit)
            self.right_layout.addWidget(self.close_button)

    def _toggle_theme(self):
        theme_manager.toggle_theme()
        if theme_manager.is_dark:
            self.theme_btn.setButtonIcon(IconName.MOON)
        else:
            self.theme_btn.setButtonIcon(IconName.SUN)

    def _toggle_maximize(self):
        """切换最大化状态"""
        self.windowsMaxOrNor.emit()


    def set_logo(self, icon: Union[str, QIcon]):
        """设置图标"""
        if not self._logo:
            self.icon_label = QLabel()
            self.icon_label.setObjectName("xtitlebarlogo")
            self.icon_label.setFixedSize(18, 18)
            self.left_layout.insertWidget(0, self.icon_label)

        if icon:
            try:
                if isinstance(icon, str):
                    if icon.startswith(":") or icon.endswith((".png", ".svg", ".jpg", ".jpeg")):
                        pix = QIcon(icon).pixmap(18, 18)
                    else:
                        from src.xsideui.icon import get_icon
                        pix = get_icon(icon).pixmap(18, 18)
                elif isinstance(icon, QIcon):
                    pix = icon.pixmap(18, 18)
                else:
                    return
                self.icon_label.setPixmap(pix)
            except Exception as e:
                print(f"Failed to set logo: {e}")

    def set_title(self, title: str):
        """设置标题"""
        if title:
            self.title_label.setText(title)




