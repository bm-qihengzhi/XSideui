from ..utils.qt_compat import QWidget, QDialog, QVBoxLayout, QFrame, QGraphicsDropShadowEffect, QSizeGrip, QColor, \
    QIcon, Qt, QTimer, QEvent, QApplication, QCursor
from .title_bar import XTitleBar


class XDialog(QDialog):
    """
    无边框Dialog窗口容器组件
    """

    def __init__(self,
                 parent=None,
                 title: str = "XDialog",
                 logo: str = None,
                 show_close: bool = True,
                 ):
        super().__init__(parent=parent)
        """初始化无边框对话框容器。

            Args:
                title: 对话框标题文字。
                logo: 标题栏图标路径或图标名称。若为 None 则不显示图标。
                show_close: 是否显示标题栏右侧的关闭按钮。
                parent: 父窗口。设置后对话框将以模态或非模态形式依附于父窗口。
            """
        self.setObjectName("xdialog")
        self._title = title
        self._logo = logo
        self._show_close = show_close
        self._is_maximized = False
        self._original_margins = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._drag_position = None
        self._is_dragging = False

        self._init_widget()

    def _init_widget(self):
        """初始化窗口组件"""
        # 阴影缓冲区 (Margin)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(2, 2, 2, 2)
        self.root_layout.setSpacing(0)

        # 阴影容器 (Shadow Frame)
        self.shadow_frame = QFrame()
        self.shadow_frame.setObjectName("shadow-frame")
        self.root_layout.addWidget(self.shadow_frame)

        # 添加阴影效果（只创建一次，调整大小时通过 enabled 开关复用）
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(12)
        self._shadow.setOffset(0, 4)
        self._shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow_frame.setGraphicsEffect(self._shadow)

        # 内容区域 (业务组件放在这里)
        self.content_layout = QVBoxLayout(self.shadow_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # 标题栏
        self._setup_title_bar()
        self._setup_grips()

    def addWidget(self, widget: QWidget):
        """添加组件到内容区域

        Args:
            widget: 要添加的组件

        Returns:
            self (支持链式调用)
        """
        self.content_layout.addWidget(widget, 1)
        return self

    def addLayout(self, layout):
        """添加布局到内容区域

        Args:
            layout: 要添加的布局

        Returns:
            self (支持链式调用)
        """
        self.content_layout.addLayout(layout, 1)
        return self

    def set_title(self, title: str) -> 'XDialog':
        """设置窗口标题

        Args:
            title: 窗口标题

        Returns:
            self (支持链式调用)
        """
        self._title = title
        self.setWindowTitle(title)
        self.title_bar.set_title(title)
        return self

    def set_logo(self, icon) -> 'XDialog':
        """设置窗口图标

        Args:
            icon: 图标路径或 QIcon 对象

        Returns:
            self (支持链式调用)
        """
        self._logo = icon
        if isinstance(icon, str):
            self.setWindowIcon(QIcon(icon))
        elif isinstance(icon, QIcon):
            self.setWindowIcon(icon)
        self.title_bar.set_logo(icon)
        return self

    def hide_title_bar(self) -> 'XDialog':
        """隐藏标题栏

        Returns:
            self (支持链式调用)
        """
        self.title_bar.hide()
        return self

    def hide_minimize_button(self) -> 'XDialog':
        """隐藏最小化按钮

        Returns:
            self (支持链式调用)
        """
        if hasattr(self.title_bar, 'min_button'):
            self.title_bar.min_button.hide()
        return self

    def hide_maximize_button(self) -> 'XDialog':
        """隐藏最大化按钮

        Returns:
            self (支持链式调用)
        """
        if hasattr(self.title_bar, 'max_button'):
            self.title_bar.max_button.hide()
        return self

    def hide_theme_button(self) -> 'XDialog':
        """隐藏主题切换按钮

        Returns:
            self (支持链式调用)
        """
        if hasattr(self.title_bar, 'theme_btn'):
            self.title_bar.theme_btn.hide()
        return self

    def _setup_title_bar(self):
        """初始化标题栏"""
        self.title_bar = XTitleBar(
            title=self._title,
            logo=self._logo,
            show_min=False,
            show_max=False,
            show_close=self._show_close,
            show_dark=False,
            rounded_buttons=True,
            parent=self
        )

        self.title_bar.windowMinimumed.connect(self.showMinimized)
        self.title_bar.windowClosed.connect(self.close)
        self.content_layout.addWidget(self.title_bar, 0)

        self.title_bar.installEventFilter(self)

    def _setup_grips(self):
        """初始化窗口调整大小的抓手"""
        self.grips = []
        grip_size = 16

        for _ in range(4):
            grip = QSizeGrip(self)
            grip.setStyleSheet("background-color: transparent;")
            grip.setFixedSize(grip_size, grip_size)
            self.grips.append(grip)

        self._update_grips_position()

    def _update_grips_position(self):
        """更新抓手位置"""
        grip_size = 16
        self.grips[0].move(self.width() - grip_size, self.height() - grip_size)
        self.grips[1].move(0, self.height() - grip_size)
        self.grips[2].move(0, 0)
        self.grips[3].move(self.width() - grip_size, 0)

    def showEvent(self, event):
        super().showEvent(event)
        geo = self.frameGeometry()
        p = self.parent()
        if p:
            parent_center = p.mapToGlobal(p.rect().center())
        else:
            screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
            if not screen:
                return
            parent_center = screen.availableGeometry().center()
        geo.moveCenter(parent_center)
        self.move(geo.topLeft())

    def resizeEvent(self, event):
        # 在调整大小开始时，暂时禁用阴影效果，减少 CPU 负担
        if self._shadow.isEnabled():
            self._shadow.setEnabled(False)
        super().resizeEvent(event)
        QTimer.singleShot(100, self._restore_shadow)

        self._update_grips_position()

    def _restore_shadow(self):
        # 重新启用阴影效果
        if not self._shadow.isEnabled():
            self._shadow.setEnabled(True)

    def eventFilter(self, obj, event):
        """事件过滤器，处理标题栏的鼠标事件
        
        Args:
            obj: 事件对象
            event: 事件类型
            
        Returns:
            bool: 是否处理了事件
        """
        if obj == self.title_bar:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._is_dragging = True
                    self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
                    return True
            elif event.type() == QEvent.MouseMove:
                if self._is_dragging and event.buttons() == Qt.LeftButton:
                    self.move(event.globalPos() - self._drag_position)
                    event.accept()
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._is_dragging = False
                    event.accept()
                    return True
        return super().eventFilter(obj, event)
