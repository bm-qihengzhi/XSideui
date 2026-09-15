"""Optimized theme management for XmSideUI
XmSideUI 优化后的主题管理模块

This module provides optimized theme management functionality:
本模块提供优化的主题管理功能：

1. Fast startup - only load current theme styles
   快速启动 - 只加载当前主题样式
2. Fast switching - use global stylesheet + async preload
   快速切换 - 使用全局样式表 + 异步预加载
3. High efficiency - smart caching + batch updates
   高效运行 - 智能缓存 + 批量更新
"""

import json
from pathlib import Path
from typing import Dict, Optional
import importlib.resources as _resources

from ..utils.qt_compat import QFont, QObject, QSettings, QThread, Signal, QApplication, QWidget, QLabel, \
    QPropertyAnimation, QEasingCurve, QPainter, QPainterPath, QPolygon, \
    QPoint, Qt, Property, QLinearGradient, QColor
from .qss_loader import qss_loader
from .thmem_config import ThemeConfig
from .theme_types import ThemeColors, ThemeType

# 资源子包名：用 __name__ 推导（zipimport 环境下 __package__ 可能为 None）
_RESOURCES_PKG = __name__.rsplit('.', 1)[0]


class ThemeRegistry:
    """主题注册表

    管理所有可用的主题配置
    """

    def __init__(self):
        self._themes: Dict[str, ThemeConfig] = {}
        self._load_builtin_themes()

    def _load_builtin_themes(self):
        """加载内置主题"""
        try:
            light_config = json.loads(
                _resources.read_text(f"{_RESOURCES_PKG}.color_json", 'light.json'))
            dark_config = json.loads(
                _resources.read_text(f"{_RESOURCES_PKG}.color_json", 'dark.json'))

            self.register_theme(
                ThemeConfig(
                    name="light",
                    display_name=light_config.get("display_name", "Light Theme"),
                    colors=ThemeColors(**light_config["colors"]),
                    theme_type=ThemeType.LIGHT,
                    fonts=light_config.get("fonts", {}),
                    spacing=light_config.get("spacing", {}),
                    height=light_config.get("height", {}),
                    border_radius=light_config.get("border_radius", {}),
                    border_width=light_config.get("border_width", {}),
                    opacity=light_config.get("opacity", {}),
                    shadow=light_config.get("shadow", {}),
                    radio=light_config.get("radio", {}),
                    checkbox=light_config.get("checkbox", {}),
                    switch=light_config.get("switch", {})
                )
            )

            self.register_theme(
                ThemeConfig(
                    name="dark",
                    display_name=dark_config.get("display_name", "Dark Theme"),
                    colors=ThemeColors(**dark_config["colors"]),
                    theme_type=ThemeType.DARK,
                    fonts=dark_config.get("fonts", {}),
                    spacing=dark_config.get("spacing", {}),
                    height=dark_config.get("height", {}),
                    border_radius=dark_config.get("border_radius", {}),
                    border_width=dark_config.get("border_width", {}),
                    opacity=dark_config.get("opacity", {}),
                    shadow=dark_config.get("shadow", {}),
                    radio=dark_config.get("radio", {}),
                    checkbox=dark_config.get("checkbox", {}),
                    switch=dark_config.get("switch", {})
                )
            )
        except Exception as e:
            print(f"Warning: Failed to load builtin color_json: {e}")

    def register_theme(self, theme_config: ThemeConfig):
        """注册主题

        Args:
            theme_config: 主题配置
        """
        self._themes[theme_config.name] = theme_config

    def get_theme(self, name: str) -> Optional[ThemeConfig]:
        """获取主题配置

        Args:
            name: 主题名称

        Returns:
            主题配置，如果不存在则返回 None
        """
        return self._themes.get(name)

    def list_themes(self):
        """列出所有主题

        Returns:
            主题配置列表
        """
        return list(self._themes.values())

    def has_theme(self, name: str) -> bool:
        """检查主题是否存在

        Args:
            name: 主题名称

        Returns:
            如果主题存在返回 True，否则返回 False
        """
        return name in self._themes

    def unregister_theme(self, name: str):
        """注销主题

        Args:
            name: 主题名称
        """
        if name in self._themes:
            del self._themes[name]


class ThemePreloadThread(QThread):
    """主题预加载线程
    
    在后台预加载主题样式，避免阻塞主线程
    """
    preload_finished = Signal(str)
    preload_failed = Signal(str, str)

    def __init__(self, theme_name: str, theme_config: ThemeConfig):
        super().__init__()
        self._theme_name = theme_name
        self._theme_config = theme_config
        self._should_stop = False

    def stop(self):
        """安全停止线程"""
        self._should_stop = True
        self.wait(1000)  # 等待最多 1 秒

    def run(self):
        """在后台线程中预加载样式"""
        try:
            # 预加载 QSS 文件
            qss_loader.load_theme_stylesheet(self._theme_config)

            if not self._should_stop:
                self.preload_finished.emit(self._theme_name)
        except Exception as e:
            print(f"[预加载] 预加载失败: {e}")
            self.preload_failed.emit(self._theme_name, str(e))


class ThemeTransitioner(QLabel):
    """主题切换过渡遮罩 - 横向对角扫掠版 (Diagonal Wipe)"""

    def __init__(self, target_widget: QWidget, duration=600):
        super().__init__(target_widget)
        # 1. 捕获旧外观
        self._pixmap = target_widget.grab()
        self.setGeometry(target_widget.rect())
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # 2. 动画属性
        self._progress = 0.0
        self.ani = QPropertyAnimation(self, b"progress")
        self.ani.setDuration(duration)
        self.ani.setStartValue(0.0)
        self.ani.setEndValue(1.0)
        self.ani.setEasingCurve(QEasingCurve.InOutQuart)  # 对角线路径长，用 InOut 曲线更顺滑
        self.ani.finished.connect(self.deleteLater)

        self.show()
        self.ani.start()

    @Property(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 性能提示：对于 Pixmap 绘制，有时关闭 Antialiasing 反而更快，且不影响效果
        painter.setRenderHints(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        total_len = (w + h)
        current_x = total_len * self._progress

        # 1. 依然保持高性能的“硬裁剪”绘制旧图
        painter.save()
        painter.setClipPath(self._create_wipe_path(w, h, current_x))
        painter.drawPixmap(0, 0, self._pixmap)
        painter.restore()

        # 2. 【核心优化】绘制柔和的扫掠光带 (视觉欺骗)
        # 我们在 current_x 的位置画一个宽约 60px 的渐变带
        glow_width = 60

        # 渐变方向：垂直于扫掠线 (从左上到右下)
        # 这里的坐标计算要和你的扫掠线对齐
        gradient = QLinearGradient(current_x - glow_width, 0, current_x, glow_width)
        # 关键：颜色从 透明 -> 半透明白 -> 透明
        gradient.setColorAt(0, Qt.transparent)
        gradient.setColorAt(0.5, QColor(255, 255, 255, 60))  # 柔和的亮部
        gradient.setColorAt(1, Qt.transparent)

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)

        # 构造一个覆盖在切割线上的斜向长条矩形
        glow_polygon = QPolygon([
            QPoint(int(current_x), 0),
            QPoint(int(current_x - glow_width), 0),
            QPoint(0, int(current_x - glow_width)),
            QPoint(0, int(current_x))
        ])

        # 随进度变淡，收尾更自然
        painter.setOpacity(1.0 - (self._progress * 0.5))
        painter.drawPolygon(glow_polygon)

    # def paintEvent(self, event):
    #     painter = QPainter(self)
    #     painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    #
    #     w, h = self.width(), self.height()
    #     # 简化计算：直接用平移坐标系
    #     painter.save()
    #
    #     # 1. 计算斜线位置
    #     # 我们不再构建复杂的 5 点多边形，而是直接旋转画布
    #     # 将原点移到中心并旋转 45 度，这样扫掠就变成了简单的矩形移动
    #     total_len = (w + h)
    #     current_x = total_len * self._progress
    #
    #     # 创建遮罩区域
    #     path = QPainterPath()
    #     # 直接定义一个覆盖右下半部分的巨大矩形
    #     # 随着 progress 增加，这个矩形向右下移动，露出的旧图越来越少
    #     path.addRect(current_x, 0, w * 2, h * 2)
    #
    #     # 2. 剪裁并绘制
    #     # 逆向思维：只画“还没被扫过”的部分
    #     painter.setClipPath(self._create_wipe_path(w, h, current_x))
    #     painter.drawPixmap(0, 0, self._pixmap)
    #
    #     # 3. 扫掠光效（用简单的直线代替复杂的 path）
    #     painter.setClipping(False)
    #     pen = QPen(Qt.white, 2)
    #     painter.setPen(pen)
    #     painter.setOpacity(0.5 * (1 - self._progress))  # 随进度变淡
    #     # 只需要画一条从 top_point 到 left_point 的斜线
    #     painter.drawLine(QPoint(int(current_x), 0), QPoint(0, int(current_x)))
    #     painter.restore()

    def _create_wipe_path(self, w, h, offset):
        # 构建一个简单的三角形/四边形用于裁剪
        path = QPainterPath()
        polygon = QPolygon([
            QPoint(int(offset), 0),
            QPoint(w, 0),
            QPoint(w, h),
            QPoint(0, h),
            QPoint(0, int(offset))
        ])
        path.addPolygon(polygon)
        return path


class Theme(QObject):
    """优化后的主题管理器单例类
    
    优化策略：
    1. 快速启动 - 只加载当前主题的样式
    2. 快速切换 - 立即应用全局样式表 + 后台预加载
    3. 高效运行 - 智能缓存 + 批量更新
    
    Examples:
        # Switch theme mode 切换主题模式
        theme_manager.set_theme("dark")
        
        # Toggle between light/dark 明暗主题切换
        theme_manager.toggle_theme()
        
        # Set theme colors 设置主题色
        theme_manager.set_primary_color("#FF0000")
    """

    theme_changed = Signal(str)
    theme_changing = Signal(str)
    theme_preloaded = Signal(str)
    _instance = None

    def __new__(cls):
        """Ensure singleton pattern
        确保单例模式
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize theme manager
        初始化主题管理器
        """
        if not hasattr(self, 'initialized'):
            super().__init__()
            self._settings = QSettings('XmSideUI', 'Theme')

            self._registry = ThemeRegistry()

            saved_theme_name = self._settings.value('theme_name', 'light')
            self._current_theme = self._get_theme_or_default(saved_theme_name)

            self._custom_primary_colors: Dict[str, str] = {}
            self._preload_thread = None
            self._preloaded_themes = set()
            self._stylesheet_applied = False  # 标记是否已应用样式表
            self._font_cache = {}  # 字体缓存

            # 启动时只加载当前主题的样式（快速启动）
            self._preload_current_theme()

            self.initialized = True

    def initialize(self):
        """初始化主题系统（自动调用，无需手动调用）
        
        内部自动调用，用户无需关心
        """
        if not self._stylesheet_applied:
            self._apply_global_stylesheet()
            self._stylesheet_applied = True
            print(f"[主题] 主题系统初始化完成")

    def _ensure_initialized(self):
        """确保主题系统已初始化（内部方法）"""
        if not self._stylesheet_applied:
            self.initialize()

    def _get_theme_or_default(self, theme_name: str) -> ThemeConfig:
        """获取主题配置，如果不存在则返回默认主题"""
        theme = self._registry.get_theme(theme_name)
        if theme is None:
            theme = self._registry.get_theme("light")
        return theme

    def _preload_current_theme(self):
        """预加载当前主题的样式（启动时调用）"""
        # 预加载 QSS 文件
        qss_loader.load_theme_stylesheet(self._current_theme)
        self._preloaded_themes.add(self._current_theme.name)

        # 尝试应用全局样式表（如果 QApplication 已创建）
        self._apply_global_stylesheet_if_ready()

    def _apply_global_stylesheet_if_ready(self):
        """如果 QApplication 已创建，则应用全局样式表"""
        app = QApplication.instance()
        if app is not None:
            self._apply_global_stylesheet()
            self._stylesheet_applied = True

    def _preload_theme_async(self, theme_name: str, theme_config: ThemeConfig):
        """异步预加载主题样式（切换主题时调用）"""
        if theme_name in self._preloaded_themes:
            print(f"[预加载] 主题 {theme_name} 已预加载，跳过")
            return

        # 安全停止之前的预加载线程
        if self._preload_thread and self._preload_thread.isRunning():
            self._preload_thread.stop()  # 使用安全的 stop() 方法

        # 创建新的预加载线程
        self._preload_thread = ThemePreloadThread(theme_name, theme_config)
        self._preload_thread.preload_finished.connect(self._on_preload_finished)
        self._preload_thread.preload_failed.connect(self._on_preload_failed)
        self._preload_thread.start()

    def _on_preload_finished(self, theme_name: str):
        """预加载完成回调"""
        self._preloaded_themes.add(theme_name)
        self.theme_preloaded.emit(theme_name)
        print(f"[预加载] 主题 {theme_name} 预加载完成")

    def _on_preload_failed(self, theme_name: str, error: str):
        """预加载失败回调"""
        print(f"[预加载] 主题 {theme_name} 预加载失败: {error}")

    def get_font(self, size_key="size_m", weight_key="weight_regular") -> QFont:
        """获取字体（带缓存和跨平台支持）

        Args:
            size_key: 字体尺寸键（如 "size_s", "size_m", "size_l"）
            weight_key: 字体权重键（如 "weight_regular", "weight_medium", "weight_bold"）

        Returns:
            QFont: 字体对象
        """
        # 生成缓存键
        cache_key = (size_key, weight_key)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        fonts_cfg = self.fonts

        # Debug 信息
        import sys
        from ..utils.qt_compat import QFontDatabase

        # 获取字体族列表
        family_str = fonts_cfg.get("family", "")
        if not family_str:
            # 使用跨平台默认字体
            families = self._get_default_font_families()
        else:
            families = [f.strip().strip('"') for f in family_str.split(',')]

        # 验证字体族是否可用
        font_db = QFontDatabase()
        available_families = font_db.families()
        valid_families = [f for f in families if f in available_families]

        # 如果没有可用的字体，使用系统默认
        if not valid_families:
            valid_families = ["sans-serif"]

        # 获取尺寸
        size_str = fonts_cfg.get(size_key, "14px")
        pixel_size = int(size_str.replace("px", ""))

        # 获取权重
        css_weight = int(fonts_cfg.get(weight_key, "400"))
        qt_weight = self._css_weight_to_qt_weight(css_weight)

        # 创建字体
        font = QFont()
        font.setFamilies(valid_families)  # 使用验证后的字体族
        font.setPixelSize(pixel_size)
        font.setWeight(qt_weight)
        font.setStyleStrategy(QFont.PreferAntialias)

        # 缓存字体
        self._font_cache[cache_key] = font
        return font

    def _css_weight_to_qt_weight(self, css_weight: int) -> int:
        """将 CSS 字体权重转换为 Qt 字体权重

        Args:
            css_weight: CSS 字体权重（100-900）

        Returns:
            Qt 字体权重（0-99）
        """
        if css_weight <= 400:
            return QFont.Normal  # 50
        elif css_weight <= 500:
            return QFont.Medium  # 57
        elif css_weight <= 600:
            return QFont.DemiBold  # 63
        else:
            return QFont.Bold  # 75

    def _get_default_font_families(self) -> list:
        """获取跨平台默认字体族列表

        Returns:
            字体族列表，按优先级排序
        """
        import sys
        platform = sys.platform

        # 跨平台默认字体配置
        default_families = {
            'win32': ['Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei'],
            'darwin': ['PingFang SC', 'STHeiti', 'Helvetica'],
            'linux': ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei']
        }

        return default_families.get(platform, ['sans-serif'])

    @property
    def colors(self) -> ThemeColors:
        """Get current theme colors
        获取当前主题颜色
        """
        return self._current_theme.colors

    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark
        检查当前是否为暗色主题
        """
        return self._current_theme.theme_type == ThemeType.DARK

    @property
    def theme_name(self) -> str:
        """Get current theme name
        获取当前主题名称
        """
        return self._current_theme.name

    @property
    def theme_type(self) -> ThemeType:
        """Get current theme type
        获取当前主题类型
        """
        return self._current_theme.theme_type

    @property
    def registry(self) -> ThemeRegistry:
        """Get theme registry
        获取主题注册表
        """
        return self._registry

    @property
    def fonts(self) -> Dict[str, str]:
        """Get current theme fonts
        获取当前主题字体配置
        """
        return self._current_theme.fonts

    @property
    def spacing(self) -> Dict[str, str]:
        """Get current theme spacing
        获取当前主题间距配置
        """
        return self._current_theme.spacing

    @property
    def height(self) -> Dict[str, str]:
        """Get current theme height
        获取当前主题高度配置
        """
        return self._current_theme.height

    @property
    def border_radius(self) -> Dict[str, str]:
        """Get current theme border radius
        获取当前主题圆角配置
        """
        return self._current_theme.border_radius

    @property
    def radio(self) -> Dict[str, Dict[str, int]]:
        """Get current theme radio button config
        获取当前主题单选按钮配置
        """
        return self._current_theme.radio

    @property
    def checkbox(self) -> Dict[str, Dict[str, int]]:
        """Get current theme checkbox config
        获取当前主题复选框配置
        """
        return self._current_theme.checkbox

    @property
    def switch(self) -> Dict[str, Dict[str, int]]:
        """Get current theme switch config
        获取当前主题开关配置
        """
        return self._current_theme.switch

    def set_theme(self, theme_name: str, animate: bool = True):
        """设置主题（优化版）
        
        优化策略：
        1. 立即应用全局样式表（快速响应）
        2. 后台预加载新主题样式（下次切换更快）
        
        Args:
            theme_name: 主题名称
            
        Raises:
            ValueError: 如果主题不存在
        """
        theme = self._registry.get_theme(theme_name)
        if theme is None:
            raise ValueError(f"Theme '{theme_name}' not found")

        # --- 动画准备阶段 ---
        transitioner = None
        if animate:
            app = QApplication.instance()
            # 找到当前活跃的主窗口作为动画目标
            active_win = app.activeWindow()
            if active_win:
                transitioner = ThemeTransitioner(active_win, duration=450)

        self.theme_changing.emit(theme_name)

        # 1. 应用新主题（立即响应）
        old_primary = self._current_theme.colors.primary
        self._current_theme = theme

        if theme_name in self._custom_primary_colors:
            primary_color = self._custom_primary_colors[theme_name]
            self._current_theme = self._current_theme.with_primary_color(primary_color)

        self._settings.setValue('theme_name', theme_name)

        # 2. 立即应用全局样式表（快速切换）
        self._apply_global_stylesheet()

        # 3. 后台预加载新主题样式（异步）
        self._preload_theme_async(theme_name, self._current_theme)

        self.theme_changed.emit(theme_name)

    def _apply_global_stylesheet(self):
        """应用全局样式表
        
        生成并应用全局样式表，实现快速切换
        """

        # 加载 QSS 文件
        global_stylesheet = qss_loader.load_theme_stylesheet(self._current_theme)

        # 应用到整个应用
        QApplication.instance().setStyleSheet(global_stylesheet)

    def toggle_theme(self):
        """明暗切换主题（优化版）"""
        current_type = self._current_theme.theme_type
        new_type = ThemeType.DARK if current_type == ThemeType.LIGHT else ThemeType.LIGHT

        for theme in self._registry.list_themes():
            if theme.theme_type == new_type:
                self.set_theme(theme.name)
                return

    def set_primary_colors(self, color_map: Dict[str, str]):
        """一次性设置多种模式的主题色

        Args:
            color_map: 字典格式，例如 {"light": "#eb2f96", "dark": "#722ed1"}
        """
        if not isinstance(color_map, dict):
            print("[主题] 错误: 参数必须是一个字典，例如 {'light': '#color1', 'dark': '#color2'}")
            return

        changed_current = False

        for theme_name, primary_color in color_map.items():
            # 1. 记录到自定义颜色映射表中
            self._custom_primary_colors[theme_name] = primary_color

            # 2. 同步更新注册表中的配置对象
            theme_cfg = self._registry.get_theme(theme_name)
            if theme_cfg:
                new_cfg = theme_cfg.with_primary_color(primary_color)
                self._registry.register_theme(new_cfg)

                # 3. 如果修改的是当前正在激活的主题，标记需要更新 UI
                if theme_name == self._current_theme.name:
                    self._current_theme = new_cfg
                    changed_current = True
            else:
                print(f"[主题] 警告: 未找到名为 '{theme_name}' 的主题，已跳过颜色设置")

        # 4. 如果当前主题被修改了，统一触发一次 UI 更新
        if changed_current:
            self._apply_global_stylesheet_if_ready()
            self.theme_changed.emit()

    def register_custom_theme(self, theme_config: ThemeConfig):
        """注册自定义主题
        
        Args:
            theme_config: 主题配置
        """
        self._registry.register_theme(theme_config)

    def unregister_theme(self, theme_name: str):
        """注销主题
        
        Args:
            theme_name: 主题名称
        """
        self._registry.unregister_theme(theme_name)

    def color_with_alpha(self, color: str, alpha: float) -> str:
        """获取带透明度的颜色"""
        if color.startswith('#'):
            color = color[1:]
        if len(color) == 6:
            r = int(color[:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        return color


# Global theme instance 全局主题实例
if not hasattr(Theme, '_instance'):
    Theme._instance = Theme()
theme_manager = Theme()
