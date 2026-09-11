# XTitleBar

标题栏组件，支持窗口控制、主题切换和自定义组件。

## 导入

```python
from xsideui import XTitleBar
```

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `title` | str | "XmSideUI" | 窗口标题 |
| `logo` | str | "" | 窗口图标路径 |
| `show_min` | bool | True | 是否显示最小化按钮 |
| `show_max` | bool | True | 是否显示最大化按钮 |
| `show_close` | bool | True | 是否显示关闭按钮 |
| `show_dark` | bool | True | 是否显示明暗主题切换按钮 |
| `rounded_buttons` | bool | False | 窗口控制按钮 hover 背景是否使用内缩圆角（XDialog 使用） |
| `parent` | QWidget | None | 父组件 |

## 方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `set_title(title)` | 设置标题 | None |
| `set_logo(icon)` | 设置图标 | None |
| `add_widget(widget)` | 添加自定义组件到中间区 | None |

## 信号

| 信号 | 说明 |
|------|------|
| `windowMinimumed` | 窗口最小化时发出 |
| `windowMaximumed` | 窗口最大化时发出 |
| `windowNormaled` | 窗口还原时发出 |
| `windowClosed` | 窗口关闭时发出 |
| `windowMoved(QPoint)` | 窗口移动时发出，参数为新位置 |

## 示例

```python
# 基础用法
title_bar = XTitleBar(
    title="我的应用",
    logo="path/to/logo.png"
)

# 自定义按钮显示
title_bar = XTitleBar(
    title="我的应用",
    show_min=False,
    show_max=False,
    show_close=True
)

# 设置标题
title_bar.set_title("新标题")

# 设置图标
title_bar.set_logo("path/to/new_logo.png")

# 添加自定义组件
from PySide2.QtWidgets import QLabel
label = QLabel("自定义内容")
title_bar.add_widget(label)

# 监听窗口事件
title_bar.windowMinimumed.connect(lambda: print("最小化"))
title_bar.windowMaximumed.connect(lambda: print("最大化"))
title_bar.windowNormaled.connect(lambda: print("还原"))
title_bar.windowClosed.connect(lambda: print("关闭"))
title_bar.windowMoved.connect(lambda pos: print(f"移动到 {pos}"))

# 双击标题栏切换最大化
# 双击事件已内置，无需额外处理

# 拖拽窗口
# 拖拽事件已内置，无需额外处理
```

## 特性

- ✅ 窗口图标和标题
- ✅ 最小化、最大化、关闭按钮
- ✅ 明暗主题切换按钮
- ✅ 双击标题栏切换最大化
- ✅ 拖拽标题栏移动窗口
- ✅ 中间区支持添加自定义组件
- ✅ 主题适配
