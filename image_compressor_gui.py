import os
import threading
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image

APP_VERSION = "v3.1.0"

# ================= 压缩核心 =================
def compress_image(input_path, output_path, target_kb):
    target_size = target_kb * 1024
    original_size = os.path.getsize(input_path)

    info = {"resized": 0, "format": "", "success": False, "reason": ""}

    try:
        img = Image.open(input_path)
        fmt = img.format.upper()
        info["format"] = fmt

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            fmt = "JPG"
            info["format"] = fmt

        def try_jpg(image):
            low, high = 5, 95
            best = None
            while low <= high:
                mid = (low + high) // 2
                image.save(output_path, "JPEG", quality=mid, optimize=True, progressive=True)
                if os.path.getsize(output_path) <= target_size:
                    best = mid
                    low = mid + 1
                else:
                    high = mid - 1
            return best

        if fmt == "PNG":
            img.save(output_path, "PNG", optimize=True, compress_level=9)
            if os.path.getsize(output_path) <= target_size:
                info["success"] = True
                return original_size, os.path.getsize(output_path), info
            else:
                fmt = "JPG"
                info["format"] = fmt

        q = try_jpg(img)
        while q is None:
            w, h = img.size
            if w < 300 or h < 300:
                break
            img = img.resize((int(w * 0.9), int(h * 0.9)), Image.LANCZOS)
            info["resized"] += 1
            q = try_jpg(img)

        if os.path.exists(output_path) and os.path.getsize(output_path) <= target_size:
            info["success"] = True
        else:
            info["reason"] = "已降至最低质量 / 分辨率仍无法满足目标大小"

    except Exception as e:
        info["reason"] = str(e)

    return original_size, os.path.getsize(output_path) if os.path.exists(output_path) else 0, info

# ================= 跨平台打开文件 =================
def open_path(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        os.system(f'open "{path}"')
    else:
        os.system(f'xdg-open "{path}"')

# ================= GUI =================
class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"炫酷图片压缩工具 {APP_VERSION}")
        self.geometry("920x620")
        self.resizable(False, False)
        self.files = set()
        self.output_dir = ""

        self.create_ui()
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.drop)

    def create_ui(self):
        # 固定单色背景，避免非法颜色报错
        self.canvas = tk.Canvas(self, width=920, height=620, bg='#2c3e50')
        self.canvas.pack(fill="both", expand=True)

        # 顶部控件
        top_frame = tk.Frame(self.canvas, bg='#2c3e50')
        top_frame.place(x=20, y=20)

        tk.Label(top_frame, text="目标大小 KB：", bg='#2c3e50', fg='white', font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        self.size_entry = tk.Entry(top_frame, width=8, font=('Arial', 12))
        self.size_entry.insert(0, "200")
        self.size_entry.pack(side=tk.LEFT, padx=5)

        # 按钮样式
        button_style = {'font': ('Arial', 12, 'bold'), 'bg': '#2980b9', 'fg': 'white', 'activebackground': '#3498db', 'activeforeground': 'white', 'bd':0, 'relief':'ridge', 'cursor':'hand2'}
        self.select_btn = tk.Button(top_frame, text="选择图片", command=self.select_files, **button_style)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        self.output_btn = tk.Button(top_frame, text="选择输出目录", command=self.select_output_dir, **button_style)
        self.output_btn.pack(side=tk.LEFT, padx=5)
        self.start_btn = tk.Button(top_frame, text="开始压缩", command=self.start, **button_style)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        # 进度条
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("custom.Horizontal.TProgressbar", troughcolor='#34495e', bordercolor='#34495e', background='#1abc9c', thickness=25)
        self.progress = ttk.Progressbar(self.canvas, length=880, style="custom.Horizontal.TProgressbar")
        self.progress.place(x=20, y=70)

        # 树状列表
        columns = ("name", "status", "detail")
        self.tree = ttk.Treeview(self.canvas, columns=columns, show="headings", height=25)
        self.tree.heading("name", text="文件名")
        self.tree.heading("status", text="状态")
        self.tree.heading("detail", text="详情")
        self.tree.place(x=20, y=110)

        self.tree.tag_configure("success", background="#27ae60", foreground='white')
        self.tree.tag_configure("warn", background="#f39c12", foreground='white')
        self.tree.tag_configure("fail", background="#c0392b", foreground='white')

        self.tree.bind("<Double-1>", self.open_file)

    # 文件添加
    def add_file(self, path):
        if path not in self.files:
            self.files.add(path)
            self.tree.insert("", "end", values=(os.path.basename(path), "", ""))

    def drop(self, event):
        for p in self.tk.splitlist(event.data):
            if os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                            self.add_file(os.path.join(root, file))
            elif p.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.add_file(p)

    def select_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        for p in paths:
            self.add_file(p)

    def select_output_dir(self):
        self.output_dir = filedialog.askdirectory(title="选择输出目录")

    # 压缩
    def start(self):
        if not self.files:
            messagebox.showwarning("提示", "请先添加图片")
            return
        try:
            self.target_kb = int(self.size_entry.get())
        except:
            messagebox.showerror("错误", "目标大小必须是数字")
            return
        if not self.output_dir:
            messagebox.showwarning("提示", "请先选择输出目录")
            return
        self.progress["maximum"] = len(self.files)
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        self.progress["value"] = 0
        fail_reasons = []
        for idx, path in enumerate(self.files):
            name = os.path.basename(path)
            out_name = os.path.splitext(name)[0] + f"_{self.target_kb}k" + os.path.splitext(name)[1]
            out = os.path.join(self.output_dir, out_name)
            before, after, info = compress_image(path, out, self.target_kb)

            if info["success"]:
                status = "✅ 达标"
                tag = "success"
            elif info["reason"]:
                status = "❌ 无法达标"
                tag = "fail"
                fail_reasons.append(f"{name}：{info['reason']}")
            else:
                status = "⚠ 已达标（质量下降）"
                tag = "warn"

            detail = f"{before//1024}KB → {after//1024}KB | {info['format']} | 分辨率↓{info['resized']}次"
            item = self.tree.get_children()[idx]
            self.tree.item(item, values=(name, status, detail), tags=(tag,))
            self.progress["value"] += 1

        if fail_reasons:
            messagebox.showerror("部分图片压缩失败", "\n".join(fail_reasons))
        messagebox.showinfo("完成", "全部处理完成")

    def open_file(self, event):
        item = self.tree.selection()
        if not item:
            return
        filename = self.tree.item(item)['values'][0]
        out_name = os.path.splitext(filename)[0] + f"_{self.target_kb}k" + os.path.splitext(filename)[1]
        path = os.path.join(self.output_dir, out_name)
        if os.path.exists(path):
            open_path(path)
        elif self.output_dir:
            open_path(self.output_dir)

if __name__ == "__main__":
    App().mainloop()