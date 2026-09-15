"""
样式文件加载器（优化版）
QSS File Loader (Optimized)

直接加载和管理 QSS 样式文件，使用更高效的变量替换
"""

import os
import re
from typing import Dict
import importlib.resources as _resources

from .thmem_config import ThemeConfig

# 资源子包名：用 __name__ 推导（zipimport 环境下 __package__ 可能为 None）
_RESOURCES_PKG = __name__.rsplit('.', 1)[0]

# 内置 QSS 文件清单（zipimport 打包环境无法用 importlib.resources.contents 枚举时兜底）
_QSS_FILES = (
    'avatar.qss', 'card.qss', 'carousel.qss', 'checkbox.qss',
    'codeblock.qss', 'collapse.qss', 'combobox.qss', 'dialog.qss',
    'divider.qss', 'groupbox.qss', 'label.qss', 'lineedit.qss',
    'listview.qss', 'listwidget.qss', 'loading_mask.qss', 'menu.qss',
    'navbar.qss', 'navtree.qss', 'notification.qss', 'pagination.qss',
    'popover.qss', 'progressbar.qss', 'pushbutton.qss', 'qdateedit.qss',
    'qdatetimeedit.qss', 'qtimeedit.qss', 'radio.qss', 'scrollarea.qss',
    'spinbox.qss', 'tablewidget.qss', 'tabwidget.qss', 'text_edit.qss',
    'title_bar.qss', 'upload.qss', 'widget.qss',
)


def _list_qss_files(pkg: str) -> list:
    """枚举包内 QSS 文件；zipimport 等无法枚举的环境回退到内置清单"""
    try:
        return [f for f in _resources.contents(pkg) if f.endswith('.qss')]
    except OSError:
        return list(_QSS_FILES)


class QSSLoader:
    """QSS 文件加载器（优化版）
    
    优化策略：
    1. 使用正则表达式一次性替换所有变量
    2. 使用更高效的缓存键生成
    3. 预编译正则表达式
    """
    
    def __init__(self, qss_dir: str = None):
        """初始化 QSS 加载器
        
        Args:
            qss_dir: QSS 文件目录，如果为 None 则使用默认目录
        """
        if qss_dir is None:
            self._qss_dir = None  # 改为 None，使用时再决定从哪里读
        else:
            self._qss_dir = qss_dir

        self._cache = {}
        
        # 预编译变量匹配正则
        self._var_pattern = re.compile(r'\{(\w+)\}')
    
    def load(self, qss_file: str, variables: Dict[str, str] = None) -> str:
        """加载 QSS 文件
        
        Args:
            qss_file: QSS 文件名（如 "label.qss"）
            variables: 变量字典（如 {"primary_color": "#165DFF"}）
            
        Returns:
            QSS 样式字符串
        """

        
        # 检查缓存
        cache_key = self._make_cache_key(qss_file, variables)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if self._qss_dir:
            file_path = os.path.join(self._qss_dir, qss_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                qss = f.read()
        else:
            qss = _resources.read_text(f"{_RESOURCES_PKG}.qss", qss_file)
        
        # 替换变量（使用正则表达式一次性替换）
        if variables:
            qss = self._var_pattern.sub(
                lambda m: variables.get(m.group(1), m.group(0)),
                qss
            )
        
        # 缓存结果
        self._cache[cache_key] = qss
        
        return qss

    
    def load_theme_stylesheet(self, theme_config: ThemeConfig) -> str:
        """加载主题样式表
        
        Args:
            theme_config: 主题配置
            
        Returns:
            完整的主题 QSS 样式字符串
        """
        # 准备颜色变量
        variables = {
            "primary": theme_config.colors.primary,
            "secondary": theme_config.colors.secondary,
            "tertiary": theme_config.colors.tertiary,
            "success": theme_config.colors.success,
            "warning": theme_config.colors.warning,
            "danger": theme_config.colors.danger,
            "link": theme_config.colors.link,
            "text_0": theme_config.colors.text_0,
            "text_1": theme_config.colors.text_1,
            "text_2": theme_config.colors.text_2,
            "text_3": theme_config.colors.text_3,
            "text_disabled": theme_config.colors.text_disabled,
            "bg_0": theme_config.colors.bg_0,
            "bg_1": theme_config.colors.bg_1,
            "bg_2": theme_config.colors.bg_2,
            "fill": theme_config.colors.fill,
            "border": theme_config.colors.border,
            "shadow": theme_config.colors.shadow,
            "code_keyword": theme_config.colors.code_keyword,
            "code_string": theme_config.colors.code_string,
            "code_comment": theme_config.colors.code_comment,
            "code_function": theme_config.colors.code_function,
            "code_number": theme_config.colors.code_number,
            "code_operator": theme_config.colors.code_operator,
        }
        
        # 添加带透明度的颜色变量
        def _color_with_alpha(color: str, alpha: float) -> str:
            if color.startswith('#'):
                color = color[1:]
            if len(color) == 6:
                r = int(color[:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:], 16)
                return f"rgba({r}, {g}, {b}, {alpha})"
            return color
        
        variables.update({
            "primary_alpha_1": _color_with_alpha(theme_config.colors.primary, 0.1),
            "primary_alpha_3": _color_with_alpha(theme_config.colors.primary, 0.3),
            "primary_alpha_5": _color_with_alpha(theme_config.colors.primary, 0.5),
            "primary_alpha_8": _color_with_alpha(theme_config.colors.primary, 0.8),
            "primary_alpha_10": _color_with_alpha(theme_config.colors.primary, 0.1),
            "success_alpha_1": _color_with_alpha(theme_config.colors.success, 0.1),
            "success_alpha_3": _color_with_alpha(theme_config.colors.success, 0.3),
            "success_alpha_5": _color_with_alpha(theme_config.colors.success, 0.5),
            "success_alpha_8": _color_with_alpha(theme_config.colors.success, 0.8),
            "warning_alpha_1": _color_with_alpha(theme_config.colors.warning, 0.1),
            "warning_alpha_3": _color_with_alpha(theme_config.colors.warning, 0.3),
            "warning_alpha_5": _color_with_alpha(theme_config.colors.warning, 0.5),
            "warning_alpha_8": _color_with_alpha(theme_config.colors.warning, 0.8),
            "danger_alpha_1": _color_with_alpha(theme_config.colors.danger, 0.1),
            "danger_alpha_3": _color_with_alpha(theme_config.colors.danger, 0.3),
            "danger_alpha_5": _color_with_alpha(theme_config.colors.danger, 0.5),
            "danger_alpha_8": _color_with_alpha(theme_config.colors.danger, 0.8),
            "tertiary_alpha_1": _color_with_alpha(theme_config.colors.tertiary, 0.1),
            "tertiary_alpha_3": _color_with_alpha(theme_config.colors.tertiary, 0.3),
            "tertiary_alpha_5": _color_with_alpha(theme_config.colors.tertiary, 0.5),
            "tertiary_alpha_8": _color_with_alpha(theme_config.colors.tertiary, 0.8),
            "secondary_alpha_1": _color_with_alpha(theme_config.colors.secondary, 0.1),
            "secondary_alpha_3": _color_with_alpha(theme_config.colors.secondary, 0.3),
            "secondary_alpha_5": _color_with_alpha(theme_config.colors.secondary, 0.5),
            "secondary_alpha_8": _color_with_alpha(theme_config.colors.secondary, 0.8),
            "fill_alpha_1": _color_with_alpha(theme_config.colors.fill, 0.1),
            "fill_alpha_2": _color_with_alpha(theme_config.colors.fill, 0.2),
            "fill_alpha_3": _color_with_alpha(theme_config.colors.fill, 0.3),
            "fill_alpha_4": _color_with_alpha(theme_config.colors.fill, 0.4),
            "fill_alpha_6": _color_with_alpha(theme_config.colors.fill, 0.6),
            "fill_alpha_8": _color_with_alpha(theme_config.colors.fill, 0.8),
            "text_1_alpha_1": _color_with_alpha(theme_config.colors.text_1, 0.1),
            "text_1_alpha_2": _color_with_alpha(theme_config.colors.text_1, 0.2),
            "text_1_alpha_3": _color_with_alpha(theme_config.colors.text_1, 0.3),
            "text_1_alpha_8": _color_with_alpha(theme_config.colors.text_1, 0.8),

        })

        # 添加字体变量
        if theme_config.fonts:
            variables.update({f"font_{k}": v for k, v in theme_config.fonts.items()})
        
        # 添加间距变量
        if theme_config.spacing:
            variables.update({f"spacing_{k}": v for k, v in theme_config.spacing.items()})
        
        # 添加高度变量
        if theme_config.height:
            variables.update({f"height_{k}": v for k, v in theme_config.height.items()})
        
        # 添加圆角变量
        if theme_config.border_radius:
            variables.update({f"radius_{k}": v for k, v in theme_config.border_radius.items()})
        
        # 添加边框宽度变量
        if theme_config.border_width:
            variables.update({f"border_{k}": v for k, v in theme_config.border_width.items()})
        
        # 添加透明度变量
        if theme_config.opacity:
            variables.update({f"opacity_{k}": v for k, v in theme_config.opacity.items()})
        
        # 添加阴影变量
        if theme_config.shadow:
            variables.update({f"shadow_{k}": v for k, v in theme_config.shadow.items()})
        
        # 检查缓存
        cache_key = f"theme:{theme_config.colors.primary}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 加载所有 QSS 文件
        qss_parts = []

        if self._qss_dir:
            qss_files = [f for f in os.listdir(self._qss_dir) if f.endswith('.qss')]
        else:
            qss_files = _list_qss_files(f"{_RESOURCES_PKG}.qss")

        # 检查 base.qss
        if 'base.qss' in qss_files:
            base_qss = self.load("base.qss", variables)
            qss_parts.append(base_qss)

        for filename in qss_files:
            if filename not in ["base.qss", "theme.qss"]:
                component_qss = self.load(filename, variables)
                qss_parts.append(component_qss)
        
        # 合并并缓存
        result = "\n".join(qss_parts)
        self._cache[cache_key] = result
        
        return result
    
    def _make_cache_key(self, qss_file: str, variables: Dict[str, str] = None) -> str:
        """生成缓存键（优化版）
        
        Args:
            qss_file: QSS 文件名
            variables: 变量字典
            
        Returns:
            缓存键字符串
        """
        if not variables:
            return qss_file
        
        # 使用 frozenset 代替 tuple(sorted())，更高效
        vars_hash = hash(frozenset(variables.items()))
        return f"{qss_file}:{vars_hash}"
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
    
    def invalidate_theme(self, theme_primary: str):
        """使指定主题的缓存失效
        
        Args:
            theme_primary: 主题主色
        """
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"theme:{theme_primary}")]
        for key in keys_to_remove:
            del self._cache[key]


# 全局实例
qss_loader = QSSLoader()
