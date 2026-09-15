# 1.1.0
---
## 增加
- XCombobox 增加可搜索选项
- XUpload 增加图标支持参数

## 优化
- XUpload 修复已知BUG
- XDialog 修复关闭按钮显示方形的问题
- XLinedit 统一文字左侧内边距


# 0.9.7
---
## 增强
- XNavSimple 优化Item流畅度
- 优化QSS读取方法

# 0.9.6版本
---
## 新增组件
- XListView 新增列表视图组件
- XTextDivider 新增带文字分割线组件，导出到包顶层

## 增强
- XBadge 优化销毁机制
- XTable / XImage / XSwitch 整体优化
- 优化 Win10 下窗口阴影效果
- XImage 修复衍生问题

## Bug 修复
- XNotification: 修复关闭按钮不显示时右侧缺少边距的问题
- XNotification: 图标尺寸从 20 调整为 18，视觉更协调
- XCarousel: 修复程序强制关闭时定时器引发的 KeyboardInterrupt / RuntimeError
- XDialog: 调整 parent 参数至第一位，兼容 `super().__init__(parent)` 默认写法

## 重构
- XTitleBar: 标题栏按钮改为 `_TitleBarButton`（QPushButton 自绘），移除对 XPushButton 的依赖
  - 移除 eventFilter，悬浮/按下效果由 paintEvent 直接处理
  - 关闭按钮悬浮显示红色背景 + 白色图标
  - 所有按钮为直角绘制，解决 Win10 无边框窗口下按钮圆角不协调的问题