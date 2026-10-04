# 图片压缩工具

基于 Python + Pillow + TkinterDnD 的桌面端图片批量压缩工具，支持拖拽上传和目标大小控制。

## 功能

- 拖拽图片到窗口即可压缩
- 按目标 KB 大小自动调整质量与分辨率
- 支持 JPG / PNG 格式（PNG 自动转 JPG）
- 批量处理
- 多线程避免界面卡顿
- 打包为单文件 exe（PyInstaller）

## 技术栈

- Python 3
- Pillow（图像处理）
- Tkinter + tkinterdnd2（GUI + 拖拽）
- PyInstaller（打包）

## 运行

```bash
pip install pillow tkinterdnd2
python image_compressor_gui.py
```

## 打包

```bash
pyinstaller --onefile --windowed --icon=icon.ico image_compressor_gui.py
```
