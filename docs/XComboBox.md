# XComboBox

下拉框组件(继承QComboBox)，带有自定义样式。

## 示例

![XComboBox示例](./images/XComboBox.png "XComboBox示例")

## 导入

```python
from xsideui import XComboBox
```

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `size` | XSize 或 str | XSize.DEFAULT | 组件尺寸 |
| `border_visible` | bool | True | 是否显示边框 |
| `searchable` | bool | False | 是否支持输入搜索（可编辑+自动补全） |
| `parent` | QWidget | None | 父组件 |

## 方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `set_border_visible(visible)` | 设置边框可见性 | XComboBox |
| `set_size(size)` | 设置组件尺寸 | XComboBox |
| `get_size()` | 获取当前尺寸 | str |

## 示例

```python
# 基础用法
combo = XComboBox()

# 添加选项
combo.addItem("选项1")
combo.addItem("选项2")
combo.addItem("选项3")

# 批量添加
combo.addItems(["选项1", "选项2", "选项3"])

# 带图标添加（兼容 Qt 原生调用形式）
icon = XIcon(IconName.APP, size=16, color=XColor.PRIMARY).icon()
combo.addItem(icon, "选项4")
```

```python
# 自定义尺寸
from xsideui.xenum import XSize

combo = XComboBox(size=XSize.LARGE)
combo = XComboBox(size="large")
combo.set_size(XSize.SMALL)
combo.set_size("small")
```

```python
# 边框显示/隐藏
combo = XComboBox(border_visible=True)
combo = XComboBox(border_visible=False)
combo.set_border_visible(False)
```

```python
# 监听选中变化
combo.currentIndexChanged.connect(lambda idx: print(f"选中索引: {idx}, 内容: {combo.itemText(idx)}"))
```

```python
# 链式调用
combo = XComboBox() \
    .set_size(XSize.LARGE) \
    .set_border_visible(False)

combo.addItems(["选项1", "选项2", "选项3"])
```

```python
# 获取和设置选中项
combo.addItems(["选项1", "选项2", "选项3"])

# 通过索引设置
combo.setCurrentIndex(1)  # 选中"选项2"

# 通过文本查找并设置
combo.setCurrentText("选项3")

# 获取当前选中
print(f"索引: {combo.currentIndex()}")
print(f"文本: {combo.currentText()}")

# 查找文本对应的索引
index = combo.findText("选项2")
print(f"找到索引: {index}")
```

```python
# 禁用组件
combo.setEnabled(False)
```

```python
# 支持输入搜索（可编辑 + 自动补全）
combo = XComboBox(searchable=True)
combo.addItems(["小炒黄牛肉", "生烧排骨", "皮蛋擂辣椒", "Primary"])

# 输入时下拉列表会按包含匹配实时过滤（大小写不敏感）
# 无匹配时 currentIndex() 为 -1
# 点击输入框会清空当前选中并弹出全部选项（占位符「搜索...」提示可搜索），光标在输入框内闪烁
combo.currentIndexChanged.connect(lambda idx: print(f"选中: {combo.itemText(idx)}"))
```

## 特性

- ✅ 四种尺寸（large/default/small/mini）
- ✅ 边框显示/隐藏
- ✅ 输入搜索（可编辑+自动补全过滤）
- ✅ 自定义下拉箭头图标
- ✅ 禁用状态
- ✅ 主题适配
- ✅ 悬停效果
- ✅ 弹出层与组件间距
- ✅ 弹出时不默认选中
