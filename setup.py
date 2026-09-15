from setuptools import setup, find_packages

def read_file(filename):
    with open(filename, encoding='utf-8') as f:
        return f.read()


setup(
    name="xsideui",
    version="1.2.0",
    author="heng zhi qi",
    author_email="bmscriptsbox@163.com",
    description="A modern PySide2 / PySide6 component library with rich UI components and theme support",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/bmscriptsbox/xsideui",

    # 包配置
    package_dir={"": "src"},
    packages=find_packages(where="src"),

    # 包含的数据文件
    package_data={
        'xsideui': ['**/*.qss', '**/*.ui', '**/*.json'],  # 更具体的包名和文件类型
        'xsideui.color_json': ['**/*.json'],  # 主题文件
    },
    include_package_data=True,  # 包含版本控制中的文件

    # 分类器
    classifiers=[
        "Development Status :: 4 - Beta",  # 升级为 Beta
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: PySide",
        "Operating System :: OS Independent",  # 跨平台
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
    ],

    # Python 版本要求
    python_requires=">=3.8",

    # 依赖管理（可选）
    install_requires=[
        # 不强制安装 PySide，让用户自己选择
    ],

    # # 可选依赖
    # extras_require={
    #     'pyside2': ['PySide2>=5.15.0'],
    #     'pyside6': ['PySide6>=6.0.0'],
    #     'dev': ['pytest>=6.0', 'black>=22.0', 'flake8>=4.0'],
    # },

    # 项目相关 URLs
    project_urls={
        "Documentation": "https://github.com/bmscriptsbox/xsideui/wiki",
        "Source": "https://github.com/bmscriptsbox/xsideui",
        "Tracker": "https://github.com/bmscriptsbox/xsideui/issues",
    },

    # 关键词
    keywords="pyside2 pyside6 qt gui ui components theme",
)