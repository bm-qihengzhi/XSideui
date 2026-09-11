"""图片组件，支持多种适应模式、懒加载和缓存"""
from enum import Enum
from typing import Optional, Union


from ..utils.qt_compat import QFrame, QAction, QFileDialog, QApplication, QPixmap, QPainter, QSize, QImage, QPainterPath, Qt, Signal, QTimer, QRectF, QVariantAnimation

from .menu import XMenu
from ..theme import theme_manager
from ..icon import IconName
from ..xenum import XColor
from .. import XIcon


class XImage(QFrame):
    """图片组件"""

    class FitMode(Enum):
        """图片适应模式"""
        CONTAIN = "contain"
        COVER = "cover"
        FILL = "fill"
        NONE = "none"

    loaded = Signal()
    error = Signal()
    clicked = Signal()

    def __init__(
        self,
        source: Union[str, QPixmap, QImage, bytes] = "",
        fit: Union['XImage.FitMode', str] = FitMode.CONTAIN,
        alt: str = "",
        min_size: int = 32,
        lazy: bool = False,
        parent=None
    ):
        """
            初始化图片组件。

            Args:
                source: 图片资源。支持多种格式：
                    - str: 本地文件路径或 Base64 编码字符串。
                    - QPixmap / QImage: 直接传入 Qt 图像对象。
                    - bytes: 图片的二进制数据。
                fit: 图片缩放适配模式。
                    - 'contain': 保持比例，缩放至完全装入容器（默认）。
                    - 'cover': 保持比例，缩放至填满容器（可能被裁剪）。
                    - 'fill': 不顾比例，拉伸填满。
                    - 'none': 居中原始尺寸显示。
                alt: 备用文本。当图片加载失败或无法显示时，用于辅助说明。
                min_size: 组件的最小尺寸限制（像素）。
                    由于该值同时影响最小宽度和高度，建议用于控制组件的最小占位。
                lazy: 是否开启懒加载。开启后，仅当组件滚动到可视区域时才执行图片解码和加载逻辑。
                parent: 父级窗口或布局容器。
            """
        super().__init__(parent)

        self.setObjectName("ximage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(min_size, min_size)

        self._source = source
        self._fit = self._parse_fit(fit)
        self._alt = alt
        self._lazy = lazy

        self._loading = False
        self._error = False
        self._loaded = False
        self._opacity = 1.0

        self._original_pixmap: Optional[QPixmap] = None
        self._scaled_pixmap: Optional[QPixmap] = None
        self._cached_target_size = None
        self._cached_dpr = 1.0
        self._check_timer: Optional[QTimer] = None

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._update_scaled_pixmap)

        self._connect_theme_changed()

        if lazy:
            self._check_timer = QTimer(self)
            self._check_timer.timeout.connect(self._check_visibility)
            self._check_timer.start(500)
        elif source:
            self.load_image()

    def _parse_fit(self, fit: Union['XImage.FitMode', str]) -> str:
        """解析适应模式"""
        if isinstance(fit, XImage.FitMode):
            return fit.value
        return fit

    def _connect_theme_changed(self):
        """连接主题变化信号"""
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name):
        """处理主题变化"""
        self._scaled_pixmap = None
        self.update()

    def _get_theme_colors(self):
        """获取主题颜色"""
        return theme_manager.colors

    def _get_border_radius(self):
        """获取圆角半径"""
        theme = theme_manager.registry.get_theme(theme_manager.theme_name)
        if theme and theme.border_radius:
            radius_str = theme.border_radius.get('m', '8px')
            return int(radius_str.replace('px', ''))
        return 8

    def _show_placeholder(self):
        """显示占位图"""
        self._error = False
        self._loaded = False
        self._loading = False
        self._scaled_pixmap = None
        self.update()

    def _show_error(self):
        """显示错误状态"""
        self._error = True
        self._loading = False
        self._scaled_pixmap = None
        self.update()

    def _check_visibility(self):
        """检查可见性，懒加载图片"""
        if not self._loaded and not self._loading and not self._error and self.isVisible():
            if self._check_timer:
                self._check_timer.stop()
            self.load_image()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        """右键菜单事件"""
        if not self._loaded or not self._original_pixmap:
            return

        menu = XMenu(self)

        save_action = QAction("保存图片", self)
        save_action.triggered.connect(self._save_image)
        menu.addAction(save_action)

        copy_action = QAction("复制图片", self)
        copy_action.triggered.connect(self._copy_image)
        menu.addAction(copy_action)

        menu.addSeparator()

        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self._refresh_image)
        menu.addAction(refresh_action)

        menu.exec_(event.globalPos())

    def _save_image(self):
        """保存图片到文件"""
        if not self._original_pixmap:
            return

        dialog = QFileDialog(self)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setWindowTitle("保存图片")
        dialog.setNameFilter("PNG 文件 (*.png);;JPEG 文件 (*.jpg);;所有文件 (*.*)")

        if dialog.exec_():
            paths = dialog.selectedFiles()
            if paths:
                self._original_pixmap.save(paths[0])

    def _copy_image(self):
        """复制图片到剪贴板"""
        if not self._original_pixmap:
            return

        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self._original_pixmap)

    def _refresh_image(self):
        """刷新图片"""
        if self._source:
            self._loaded = False
            self._loading = False
            self._error = False
            self._scaled_pixmap = None
            self.load_image()

    def _load_from_cache(self, path: str) -> Optional[QPixmap]:
        """从缓存加载图片"""
        return _get_cached_image(path)

    def _save_to_cache(self, path: str, pixmap: QPixmap):
        """保存图片到缓存"""
        _cache_image(path, pixmap)

    def load_image(self):
        """加载图片"""
        if not self._source or self._loaded or self._loading:
            return

        try:
            self._error = False
            self._loading = True

            if isinstance(self._source, str):
                if self._source.startswith('data:image/'):
                    import base64
                    header, encoded = self._source.split(',',1)
                    image_data = base64.b64decode(encoded)
                    image = QImage()
                    if not image.loadFromData(image_data):
                        self._loading = False
                        self._show_error()
                        return
                    self._original_pixmap = QPixmap.fromImage(image)
                    self._finish_loading()
                else:
                    cached = self._load_from_cache(self._source)
                    if cached:
                        self._original_pixmap = cached
                        self._finish_loading()
                        return

                    image = QImage(self._source)
                    if image.isNull():
                        self._loading = False
                        self._show_error()
                        return
                    self._original_pixmap = QPixmap.fromImage(image)
                    self._save_to_cache(self._source, self._original_pixmap)
                    self._finish_loading()

            elif isinstance(self._source, QPixmap):
                self._original_pixmap = self._source
                self._finish_loading()

            elif isinstance(self._source, QImage):
                self._original_pixmap = QPixmap.fromImage(self._source)
                self._finish_loading()

            elif isinstance(self._source, bytes):
                image = QImage()
                if not image.loadFromData(self._source):
                    self._loading = False
                    self._show_error()
                    return
                self._original_pixmap = QPixmap.fromImage(image)
                self._finish_loading()

            else:
                raise ValueError("Unsupported image source type")

        except Exception as e:
            print(f"Error loading image: {e}")
            self._loading = False
            self._show_error()
            self.error.emit()

    def _finish_loading(self):
        """完成加载，播放淡入动画"""
        self._loading = False
        self._loaded = True
        self._update_scaled_pixmap()
        self.loaded.emit()

        self.updateGeometry()

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(300)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.valueChanged.connect(self._on_opacity_changed)
        self._anim.start()

    def _on_opacity_changed(self, value):
        """透明度变化回调"""
        self._opacity = value
        self.update()

    def _update_scaled_pixmap(self):
        """更新缩放缓存"""
        if not self._original_pixmap or not self._loaded:
            return

        rect = self.rect()
        target_size = rect.size()
        dpr = self.devicePixelRatioF()

        if (self._cached_target_size == target_size and 
            abs(self._cached_dpr - dpr) < 0.01 and 
            self._scaled_pixmap):
            return

        self._cached_target_size = target_size
        self._cached_dpr = dpr
        self._scaled_pixmap = None

        if target_size.width() <= 1 or target_size.height() <= 1:
            return

        pixmap_dpr = self._original_pixmap.devicePixelRatioF()
        if pixmap_dpr <= 0:
            pixmap_dpr = 1.0

        logical_pixmap_size = self._original_pixmap.size() / pixmap_dpr

        if self._fit == "none":
            self.update()
            return

        if self._fit == "contain":
            scaled_logical_size = logical_pixmap_size.scaled(target_size, Qt.KeepAspectRatio)
        elif self._fit == "cover":
            scaled_logical_size = logical_pixmap_size.scaled(target_size, Qt.KeepAspectRatioByExpanding)
        elif self._fit == "fill":
            scaled_logical_size = target_size
        else:
            scaled_logical_size = logical_pixmap_size.scaled(target_size, Qt.KeepAspectRatio)

        physical_size = scaled_logical_size * dpr
        self._scaled_pixmap = self._original_pixmap.scaled(
            physical_size,
            Qt.KeepAspectRatio if self._fit == "contain" else (
                Qt.KeepAspectRatioByExpanding if self._fit == "cover" else Qt.IgnoreAspectRatio
            ),
            Qt.SmoothTransformation
        )
        self._scaled_pixmap.setDevicePixelRatio(dpr)
        self.update()

    # def sizeHint(self):
    #     """返回基于用户设定最小高度的建议尺寸"""
    #     # 基础高度：优先使用用户设置的 minimumHeight，否则用默认值
    #     h = self.minimumHeight() if self.minimumHeight() > 0 else 64
    #
    #     if self._original_pixmap and not self._original_pixmap.isNull():
    #         # 根据图片比例计算建议宽度
    #         ratio = self._original_pixmap.width() / self._original_pixmap.height()
    #         return QSize(int(h * ratio), h)
    #
    #     # 没有图片时，默认返回一个正方形
    #     return QSize(h, h)

    # def minimumSizeHint(self):
    #     """返回最小推荐尺寸"""
    #     # 如果图片已加载，返回图片尺寸
    #     if self._original_pixmap:
    #         return self._original_pixmap.size()
    #
    #     # 返回最小尺寸
    #     min_w = self.minimumWidth()
    #     min_h = self.minimumHeight()
    #     if min_w > 0 and min_h > 0:
    #         return QSize(min_w, min_h)
    #
    #     return QSize(60, 60)  # 默认最小尺寸



    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        dpr = self.devicePixelRatioF()
        colors = self._get_theme_colors()
        radius = self._get_border_radius()

        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), radius, radius)
        painter.setClipPath(path)

        painter.fillRect(rect, Qt.transparent)

        if self._loaded and self._original_pixmap:
            painter.setOpacity(self._opacity)
            self._draw_image(painter, rect, dpr)
        elif self._error:
            self._draw_state_icon(painter, rect, dpr, XColor.DANGER)
        else:
            self._draw_state_icon(painter, rect, dpr, XColor.TERTIARY)

    def _draw_image(self, painter: QPainter, rect, dpr: float):
        """绘制图片"""
        if not self._original_pixmap:
            return

        pixmap = self._original_pixmap
        pixmap_dpr = pixmap.devicePixelRatioF()
        if pixmap_dpr <= 0:
            pixmap_dpr = 1.0
        logical_pixmap_size = pixmap.size() / pixmap_dpr

        if self._fit == "none":
            target_rect = self._center_rect(logical_pixmap_size, rect.size())
            source_rect = QRectF(0, 0, pixmap.width(), pixmap.height())
            painter.drawPixmap(target_rect, pixmap, source_rect)
            return

        scaled_pixmap_valid = False
        if self._scaled_pixmap:
            scaled_dpr = self._scaled_pixmap.devicePixelRatioF()
            if scaled_dpr <= 0:
                scaled_dpr = dpr

            if abs(scaled_dpr - dpr) < 0.01:
                scaled_logical_size = self._scaled_pixmap.size() / scaled_dpr

                expected_size = self._get_expected_size(logical_pixmap_size, rect.size())
                if (abs(scaled_logical_size.width() - expected_size.width()) < 1 and
                    abs(scaled_logical_size.height() - expected_size.height()) < 1):
                    scaled_pixmap_valid = True
                    target_rect = self._center_rect(scaled_logical_size, rect.size())
                    source_rect = QRectF(0, 0, self._scaled_pixmap.width(), self._scaled_pixmap.height())
                    painter.drawPixmap(target_rect, self._scaled_pixmap, source_rect)

        if not scaled_pixmap_valid:
            if self._fit == "contain":
                scaled_size = logical_pixmap_size.scaled(rect.size(), Qt.KeepAspectRatio)
            elif self._fit == "cover":
                scaled_size = logical_pixmap_size.scaled(rect.size(), Qt.KeepAspectRatioByExpanding)
            elif self._fit == "fill":
                scaled_size = rect.size()
            else:
                scaled_size = logical_pixmap_size.scaled(rect.size(), Qt.KeepAspectRatio)

            target_rect = self._center_rect(scaled_size, rect.size())
            source_rect = QRectF(0, 0, pixmap.width(), pixmap.height())
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(target_rect, pixmap, source_rect)

    def _get_expected_size(self, logical_pixmap_size, container_size):
        """获取预期尺寸"""
        if self._fit == "contain":
            return logical_pixmap_size.scaled(container_size, Qt.KeepAspectRatio)
        elif self._fit == "cover":
            return logical_pixmap_size.scaled(container_size, Qt.KeepAspectRatioByExpanding)
        elif self._fit == "fill":
            return container_size
        else:
            return logical_pixmap_size.scaled(container_size, Qt.KeepAspectRatio)

    def _draw_state_icon(self, painter: QPainter, rect, dpr: float, color: XColor):
        """绘制状态图标"""
        icon_size = max(24, min(rect.width(), rect.height()) // 3)
        icon_pixmap = XIcon(
            IconName.IMAGE_ERROR,
            color=color,
            size=int(icon_size * dpr)
        ).pixmap()
        icon_pixmap.setDevicePixelRatio(dpr)

        icon_dpr = icon_pixmap.devicePixelRatioF()
        if icon_dpr <= 0:
            icon_dpr = dpr
        icon_rect = self._center_rect(
            icon_pixmap.size() / icon_dpr,
            rect.size()
        )
        source_rect = QRectF(0, 0, icon_pixmap.width(), icon_pixmap.height())
        painter.drawPixmap(icon_rect, icon_pixmap, source_rect)

    def _center_rect(self, size, container_size) -> QRectF:
        """计算居中矩形"""
        x = (container_size.width() - size.width()) / 2.0
        y = (container_size.height() - size.height()) / 2.0
        return QRectF(x, y, size.width(), size.height())

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        if not self._loaded and not self._loading:
            self._show_placeholder()
            if self._lazy and self._source and self._check_timer and not self._check_timer.isActive():
                self._check_visibility()

    def resizeEvent(self, event):
        """尺寸变化事件"""
        super().resizeEvent(event)
        self._resize_timer.start(100)



    def closeEvent(self, event):
        """关闭事件"""
        if self._check_timer:
            self._check_timer.stop()
            self._check_timer.deleteLater()
            self._check_timer = None

        try:
            theme_manager.theme_changed.disconnect(self._on_theme_changed)
        except Exception:
            pass

        super().closeEvent(event)

    def set_source(self, source: Union[str, QPixmap, QImage, bytes]):
        """设置图片源"""
        self._source = source
        self._loaded = False
        self._loading = False
        self._error = False
        self._scaled_pixmap = None
        self._original_pixmap = None

        if source:
            self.load_image()
        else:
            self._show_placeholder()

        self.updateGeometry()

    def set_fit(self, fit: Union['XImage.FitMode', str]):
        """设置适应模式"""
        new_fit = self._parse_fit(fit)
        if new_fit != self._fit:
            self._fit = new_fit
            self._scaled_pixmap = None
            self._update_scaled_pixmap()
            self.update()


_image_cache = {}


def _cache_image(path: str, pixmap: QPixmap):
    """缓存图片"""
    _image_cache[path] = pixmap


def _get_cached_image(path: str) -> Optional[QPixmap]:
    """获取缓存的图片"""
    return _image_cache.get(path)


def clear_image_cache():
    """清除图片缓存"""
    global _image_cache
    _image_cache.clear()
