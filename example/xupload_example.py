"""
XUpload 上传组件使用示例
展示上传组件的各种用法和主题适配
"""
import ctypes
import sys
try:
    from PySide2.QtWidgets import QApplication, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QWidget
except ImportError:
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,  QWidget

from src.xsideui import XLabel, XWidget, XUpload, XListWidget


class XUploadDemo(XWidget):
    def __init__(self):
        super(XUploadDemo, self).__init__()
        self._init_ui()

    def _init_ui(self):
        self.set_title('XUpload Demo')
        self.resize(600, 800)
        self.set_logo(r'..\resources\logo.png')

        content_widget = QWidget()
        self.addWidget(content_widget)
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20,20,20,20)
        main_layout.setSpacing(20)

        # 添加标题
        main_layout.addWidget(XLabel("XUpload 上传组件示例", style=XLabel.Style.H1))
        main_layout.addWidget(XLabel("上传组件、异步扫描、分批发出、多模式、格式大小限制", style=XLabel.Style.H4))
        upload = XUpload(
            mode=XUpload.MODE_BOTH,
            mini_height=200,
            icon_size= 32,
            title='测试上次区域',
            description='拓展文件到此区域',
        )
        main_layout.addWidget(upload)

        # 文件列表显示
        file_list = XListWidget()
        file_list.setMaximumHeight(150)
        upload.files_processed.connect(lambda files: self.add_files_to_list(file_list, files))
        upload.file_error.connect(lambda name, error: print(f"错误: {name} - {error}"))

        main_layout.addWidget(XLabel("文件路径展示", style=XLabel.Style.H4))
        main_layout.addWidget(file_list)



    def add_files_to_list(self,list_widget: QListWidget, files: list):
        """将文件添加到列表中"""
        for file_path in files:
            item = QListWidgetItem(file_path)
            list_widget.addItem(item)
        print(f"已添加 {len(files)} 个文件")






if __name__ == "__main__":
    if sys.platform == 'win32':
        # 确保windows任务栏能正确显示图标，字符串标识符（格式：公司名.产品名.子模块.版本号）
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.myproduct.subelement.version')
    app = QApplication(sys.argv)
    demo = XUploadDemo()
    demo.show()
    sys.exit(app.exec_())
