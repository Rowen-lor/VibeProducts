import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import sys
import os
import re
import subprocess

def install_package(package):
    """如果未安装，则使用pip安装指定的包。"""
    try:
        __import__(package)
    except ImportError:
        print(f"检测到 {package} 未安装，正在尝试自动安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} 安装成功。")
        except Exception as e:
            print(f"自动安装 {package} 失败: {e}")
            print(f"请手动运行 'pip install {package}' 后再试。")
            sys.exit(1)

# 在导入依赖这些包的模块之前，先确保包已安装
install_package('pandas')
install_package('openpyxl')

import pandas as pd
import openpyxl
from merge_excels import merge_excel_files, get_output_filename
from convert_ids_to_urls import convert_ids_to_urls

class RedirectText:
    def __init__(self, text_widget):
        self.text_space = text_widget

    def write(self, string):
        self.text_space.configure(state='normal')
        self.text_space.insert('end', string)
        self.text_space.see('end')
        self.text_space.configure(state='disabled')

    def flush(self):
        pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("脚本工具集")
        self.geometry("600x400")

        # Frame for merge excels
        merge_frame = tk.LabelFrame(self, text="合并 Excel 文件", padx=10, pady=10)
        merge_frame.pack(pady=10, padx=10, fill="x")

        self.folder_path_label = tk.Label(merge_frame, text="未选择文件夹")
        self.folder_path_label.pack(side=tk.LEFT, expand=True, fill="x")

        browse_button = tk.Button(merge_frame, text="选择文件夹", command=self.browse_folder)
        browse_button.pack(side=tk.LEFT, padx=5)

        merge_button = tk.Button(merge_frame, text="开始合并", command=self.run_merge_excels)
        merge_button.pack(side=tk.LEFT, padx=5)

        # Frame for convert ids
        convert_frame = tk.LabelFrame(self, text="转换 ID 为 URL", padx=10, pady=10)
        convert_frame.pack(pady=10, padx=10, fill="x")

        convert_button = tk.Button(convert_frame, text="开始转换", command=self.run_convert_ids)
        convert_button.pack()

        # Output console
        console_frame = tk.LabelFrame(self, text="输出", padx=10, pady=10)
        console_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, state='disabled')
        self.console.pack(fill="both", expand=True)
        
        # Redirect stdout
        sys.stdout = RedirectText(self.console)
        
        self.selected_folder = ""

    def browse_folder(self):
        self.selected_folder = filedialog.askdirectory()
        if self.selected_folder:
            self.folder_path_label.config(text=self.selected_folder)
            print(f"已选择文件夹: {self.selected_folder}\n")

    def run_merge_excels(self):
        if not self.selected_folder:
            print("错误: 请先选择一个包含Excel文件的文件夹。\n")
            return
        
        def task():
            try:
                output_filename = get_output_filename(self.selected_folder)
                if not output_filename:
                    print(f"在路径 '{self.selected_folder}' 下没有找到Excel文件。\n")
                    return

                print(f"自动生成的输出文件名: {output_filename}")
                merge_excel_files(self.selected_folder, output_filename)
            except Exception as e:
                print(f"合并过程中发生错误: {e}\n")

        threading.Thread(target=task).start()

    def run_convert_ids(self):
        def task():
            try:
                print("开始转换 'Status_Inspection.xlsx' 中的ID...\n")
                convert_ids_to_urls()
            except Exception as e:
                print(f"转换过程中发生错误: {e}\n")
        
        threading.Thread(target=task).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()