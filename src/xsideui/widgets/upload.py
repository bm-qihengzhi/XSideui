from pathlib import Path
from typing import List, Optional

from .. import XIcon
from ..utils.qt_compat import (QDragEnterEvent, QDropEvent, QMouseEvent, QDragMoveEvent,QWidget, QVBoxLayout, QFileDialog,QThread, Signal, Qt, QSize, QFileInfo)
from .label import XLabel
from .pushbutton import XPushButton
from ..icon import IconName
from ..xenum import XButtonVariant, XSize
from ..theme import theme_manager



class FileProcessThread(QThread):
    """
    高性能异步文件/文件夹扫描线程
    支持分批（Batching）发送数据，防止在大文件量下导致主线程静止
    """
    files_chunk_processed = Signal(list)  # 分批传出路径列表
    scan_completed = Signal(int)  # 扫描完成，传出总数
    file_error = Signal(str, str)  # 错误上报 (文件名, 错误信息)

    def __init__(self, raw_paths: List[str], accept_types: List[str], max_size: int, mode: int):
        """初始化文件处理线程

        Args:
            raw_paths: 原始路径列表（文件或文件夹）
            accept_types: 接受的文件类型列表（如 [".jpg", ".png"]）
            max_size: 最大文件大小（字节），-1 表示不限制
            mode: 上传模式（0=文件, 1=文件夹, 2=混合）
        """
        super().__init__()
        self.raw_paths = raw_paths
        self.accept_types = [t.lower() for t in accept_types]
        self.max_size = max_size
        self.mode = mode
        self._chunk_size = 200  # 阈值：每200个文件发送一次信号

    def run(self):
        """运行文件扫描任务

        遍历所有路径，根据模式处理文件或文件夹：
        - 文件夹模式：递归扫描所有子文件
        - 文件模式：直接处理文件
        - 混合模式：自动判断并处理

        使用分批发送机制（每200个文件发送一次）防止主线程阻塞
        """
        pending_list = []
        total_count = 0

        for p in self.raw_paths:
            path = Path(p)
            try:
                # 处理文件夹模式
                if path.is_dir() and self.mode in (1, 2):
                    for child in path.rglob("*"):
                        if self.isInterruptionRequested():
                            return
                        if child.is_file() and self._check_file(child):
                            pending_list.append(str(child))
                            if len(pending_list) >= self._chunk_size:
                                self.files_chunk_processed.emit(pending_list)
                                total_count += len(pending_list)
                                pending_list = []
                                self.msleep(5)  # 极短交还CPU控制权，维持UI流畅度

                # 处理文件模式
                elif path.is_file() and self.mode in (0, 2):
                    if self.isInterruptionRequested():
                        return
                    if self._check_file(path):
                        pending_list.append(str(path))
                        if len(pending_list) >= self._chunk_size:
                            self.files_chunk_processed.emit(pending_list)
                            total_count += len(pending_list)
                            pending_list = []
                            self.msleep(5)  # 极短交还CPU控制权，维持UI流畅度
            except Exception as e:
                self.file_error.emit(path.name, str(e))

        # 发送最后一批剩余文件
        if pending_list:
            self.files_chunk_processed.emit(pending_list)
            total_count += len(pending_list)

        self.scan_completed.emit(total_count)

    def _check_file(self, path: Path) -> bool:
        """校验文件是否符合要求

        Args:
            path: 文件路径对象

        Returns:
            True: 文件符合要求
            False: 文件不符合要求（大小超限或类型不匹配）
        """
        # 大小校验
        if self.max_size != -1:
            try:
                if path.stat().st_size > self.max_size: return False
            except:
                return False

        # 后缀校验
        if "*" not in self.accept_types:
            if path.suffix.lower() not in self.accept_types:
                return False
        return True


class XUpload(QWidget):
    """
    XUpload - 极致性能的上传触发组件

    Signals:
        files_processed(list): 扫描到的路径列表（分批发出）
        scan_finished(int): 整个扫描任务结束，返回成功识别的文件总数
        file_error(str, str): 单个文件读取或校验失败的信息
    """
    files_processed = Signal(list)
    scan_finished = Signal(int)
    file_error = Signal(str, str)

    MODE_FILES = 0
    MODE_FOLDERS = 1
    MODE_BOTH = 2

    def __init__(
            self,
            title: str = "",
            description: str = "",
            mode: int = MODE_BOTH,
            accept_types: Optional[List[str]] = None,
            max_size: int = -1,
            mini_height: int = 200,
            icon_size: int = 48,
            show_border: bool = True,
            parent: Optional[QWidget] = None,
    ):
        """
        初始化高性能上传触发组件。

        Args:
            title (str):
                主标题文本。默认根据 mode 自动显示“点击或拖拽文件/文件夹到此处”。
            description (str):
                辅助描述文本。通常用于说明上传限制（如：支持 png、jpg，大小不超过 5MB）。
            mode (int):
                上传模式。可选值：
                - XUpload.MODE_FILES (0): 仅允许选择/拖拽文件。
                - XUpload.MODE_FOLDERS (1): 仅允许选择/拖拽文件夹。
                - XUpload.MODE_BOTH (2): 同时支持文件和文件夹（默认）。
            accept_types (List[str], optional):
                接受的文件后缀列表。例如 [".jpg", ".png"]。
                默认为 ["*"]，即接受所有类型。
            max_size (int):
                限制单个文件的最大字节数。默认为 -1 (不限制)。
                1MB = 1024 * 1024 字节。
            mini_height (int):
                组件的最小高度。默认为 200 像素。
            icon_size (int):
                上传图标尺寸（像素）。默认为 48。
            show_border (bool):
                是否显示组件的虚线边框。默认为 True。
            parent (Optional[QWidget]):
                父级组件指针。
        """
        super().__init__(parent)
        self._mode = mode
        self._accept_types = accept_types or ["*"]
        self._max_size = max_size
        self._icon_size = icon_size
        self._title_text = title or ("点击或拖拽文件夹到此处" if mode == 1 else "点击或拖拽文件到此处")
        self._description_text = description

        self._thread = None
        self._is_drop_active = False

        # 开启顶级组件接受拖拽，并通过事件穿透确保子组件不干扰
        self.setAcceptDrops(True)
        self._init_ui(mini_height, show_border)

        # 监听主题切换
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _init_ui(self, mini_height, show_border):
        """初始化UI界面

        Args:
            mini_height: 拖拽区域最小高度
            show_border: 是否显示边框
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 交互容器
        self.drop_area = QWidget()
        self.drop_area.setObjectName("xupload-drop-area")
        self.drop_area.setMinimumHeight(mini_height)
        self.drop_area.setCursor(Qt.PointingHandCursor)

        # 初始 QSS 属性
        self.drop_area.setProperty("dragging", "false")
        self.drop_area.setProperty("show-border", str(show_border).lower())

        drop_layout = QVBoxLayout(self.drop_area)
        drop_layout.setSpacing(10)
        drop_layout.setContentsMargins(20, 30, 20, 30)
        drop_layout.addStretch()

        # 1. 图标展示 (根据 mode 自动推断)
        icon_name = IconName.FOLDER_ADD if self._mode == self.MODE_FOLDERS else IconName.UPLOAD
        self.icon_view = XPushButton(variant=XButtonVariant.LINK, size=XSize.LARGE)
        self._icon_name = icon_name  # 保存图标名称
        self.icon_view.setIcon(XIcon.get(icon_name, size=self._icon_size).icon())
        self.icon_view.setIconSize(QSize(self._icon_size, self._icon_size))
        # 关键：确保子组件不响应鼠标和拖拽事件，使其穿透到父容器
        self.icon_view.setAttribute(Qt.WA_TransparentForMouseEvents)
        drop_layout.addWidget(self.icon_view, alignment=Qt.AlignCenter)

        # 2. 主标题
        self.title_label = XLabel(self._title_text).set_font_size(16)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        drop_layout.addWidget(self.title_label)

        # 3. 次要描述
        if self._description_text:
            self.description_label = XLabel(self._description_text).set_font_size(12)
            self.description_label.setAlignment(Qt.AlignCenter)
            self.description_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            drop_layout.addWidget(self.description_label)

        drop_layout.addStretch()
        layout.addWidget(self.drop_area)

    # --- 拖拽交互逻辑 ---

    def _paths_match_mode(self, urls) -> bool:
        """校验拖入路径的类型是否符合当前模式

        Args:
            urls: 拖拽对象的 URL 列表

        Returns:
            True: 路径类型与模式匹配
            False: 不匹配（含空列表）
        """
        if not urls:
            return False
        for url in urls:
            path = url.toLocalFile()
            if not path:
                return False
            info = QFileInfo(path)
            if self._mode == self.MODE_FOLDERS and not info.isDir():
                return False
            if self._mode == self.MODE_FILES and not info.isFile():
                return False
        return True

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件处理

        当拖拽对象进入组件区域时触发，检查是否包含URL数据且路径类型匹配当前模式
        """
        if event.mimeData().hasUrls() and self._paths_match_mode(event.mimeData().urls()):
            event.acceptProposedAction()
            self._update_dragging_style(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """拖拽移动事件处理

        拖拽对象在组件区域内移动时触发
        """
        if event.mimeData().hasUrls() and self._paths_match_mode(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """拖拽离开事件处理

        拖拽对象离开组件区域时触发，恢复默认样式
        """
        self._update_dragging_style(False)

    def dropEvent(self, event: QDropEvent):
        """拖拽释放事件处理

        拖拽对象在组件区域释放时触发，提取文件路径并开始扫描
        """
        self._update_dragging_style(False)
        urls = event.mimeData().urls()
        if not urls:
            return
        if not self._paths_match_mode(urls):
            first = urls[0].toLocalFile() or "未知"
            self.file_error.emit(first, "模式不匹配")
            event.ignore()
            return
        self._is_drop_active = True
        paths = [url.toLocalFile() for url in urls]
        if paths:
            self._start_scan(paths)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件处理

        点击容器任意位置触发文件选择对话框。
        拖拽释放后紧跟的一次鼠标释放不触发对话框，避免误弹。
        """
        if self._is_drop_active:
            self._is_drop_active = False
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            self._open_file_dialog()
            event.accept()

    # --- 核心逻辑 ---

    def _update_dragging_style(self, is_dragging: bool):
        """更新拖拽样式

        通过设置 QSS 属性并触发样式刷新来改变拖拽区域的外观

        Args:
            is_dragging: 是否处于拖拽状态
        """
        val = "true" if is_dragging else "false"
        if self.drop_area.property("dragging") != val:
            self.drop_area.setProperty("dragging", val)
            self.drop_area.style().unpolish(self.drop_area)
            self.drop_area.style().polish(self.drop_area)

    def _open_file_dialog(self):
        """打开文件选择对话框

        根据当前模式显示不同的对话框：
        - 文件夹模式：显示文件夹选择对话框
        - 文件模式：显示多文件选择对话框
        """
        dialog = QFileDialog(self)
        dialog.setWindowModality(Qt.WindowModal)
        if self._mode == self.MODE_FOLDERS:
            dialog.setWindowTitle("选择文件夹")
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)
            if dialog.exec_():
                paths = dialog.selectedFiles()
                if paths:
                    self._start_scan([paths[0]])
        else:
            dialog.setWindowTitle("选择文件")
            dialog.setFileMode(QFileDialog.ExistingFiles)
            dialog.setNameFilter(self._get_dialog_filter())
            if dialog.exec_():
                files = dialog.selectedFiles()
                if files:
                    self._start_scan(files)

    def _start_scan(self, paths: List[str]):
        """启动文件扫描任务

        创建并启动异步扫描线程，更新UI状态显示处理中

        Args:
            paths: 待扫描的路径列表
        """
        if self._thread and self._thread.isRunning():
            self._stop_thread()

        # 进入处理状态
        self.drop_area.setCursor(Qt.WaitCursor)
        self.title_label.setText("解析路径中...")


        self._thread = FileProcessThread(paths, self._accept_types, self._max_size, self._mode)
        self._thread.files_chunk_processed.connect(self.files_processed)
        self._thread.scan_completed.connect(self._on_scan_finished)
        self._thread.file_error.connect(self.file_error)
        self._thread.start()

    def _stop_thread(self):
        """停止并等待后台扫描线程结束"""
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.wait(3000)

    def closeEvent(self, event):
        """组件关闭时停止后台线程，避免回调访问已销毁对象"""
        self._stop_thread()
        super().closeEvent(event)

    def _on_scan_finished(self, count: int):
        """扫描完成回调

        恢复UI状态并发送完成信号

        Args:
            count: 成功扫描的文件总数
        """
        if self._thread is None:
            return
        self.drop_area.setCursor(Qt.PointingHandCursor)
        self.title_label.setText(self._title_text)
        self.scan_finished.emit(count)

    def _get_dialog_filter(self) -> str:
        """生成文件对话框过滤器字符串

        Returns:
            文件过滤器字符串，如 "All Files (*.*)" 或 "Support (*.jpg *.png)"
        """
        if "*" in self._accept_types:
            return "All Files (*.*)"
        exts = " ".join([f"*{e}" for e in self._accept_types])
        return f"Support ({exts})"

    # --- 链式配置方法 ---
    def set_accept_types(self, types: List[str]) -> 'XUpload':
        """设置接受的文件类型

        Args:
            types: 文件类型列表，如 [".jpg", ".png"]

        Returns:
            self: 支持链式调用
        """
        self._accept_types = types
        return self

    def set_max_size(self, bytes_val: int) -> 'XUpload':
        """设置最大文件大小

        Args:
            bytes_val: 最大文件大小（字节），-1 表示不限制

        Returns:
            self: 支持链式调用
        """
        self._max_size = bytes_val
        return self

    def _on_theme_changed(self, theme_name):
        """主题切换处理

        重新设置图标以保持正确的尺寸
        """
        if hasattr(self, '_icon_name') and hasattr(self, '_icon_size'):
            self.icon_view.setIcon(XIcon.get(self._icon_name, size=self._icon_size).icon())
            self.icon_view.setIconSize(QSize(self._icon_size, self._icon_size))