import os
import pandas as pd
import subprocess
import sys
import re
from datetime import datetime

def install_package(package):
    """如果未安装，则使用pip安装指定的包。"""
    try:
        __import__(package)
    except ImportError:
        print(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def merge_excel_files(input_path, output_filename):
    """
    合并指定文件夹中的所有Excel文件到一个文件中。

    :param input_path: 包含Excel文件的文件夹路径。
    :param output_filename: 合并后输出的Excel文件名。
    """
    # 确保必要的库已安装
    install_package('pandas')
    install_package('openpyxl')

    # 查找所有Excel文件
    excel_files = [f for f in os.listdir(input_path) if f.endswith(('.xlsx', '.xls'))]
    if not excel_files:
        print(f"在路径 '{input_path}' 下没有找到Excel文件。")
        return

    # 读取并合并
    all_data = pd.DataFrame()
    for file in excel_files:
        file_path = os.path.join(input_path, file)
        try:
            df = pd.read_excel(file_path)
            all_data = pd.concat([all_data, df], ignore_index=True)
            print(f"已处理文件: {file}")
        except Exception as e:
            print(f"处理文件 {file} 时出错: {e}")

    # 保存合并后的文件
    if not all_data.empty:
        output_path = os.path.join(input_path, output_filename)
        all_data.to_excel(output_path, index=False)
        print(f"\n所有Excel文件已成功合并到 '{output_path}'")
    else:
        print("没有数据可以合并。")

def get_output_filename(folder_path):
    """根据文件夹内的Excel文件名生成输出文件名，格式为 '2020 - {current year} {total}.xlsx'。"""
    excel_files = [f for f in os.listdir(folder_path) if f.endswith(('.xlsx', '.xls'))]
    if not excel_files:
        return None
    total = 0
    for f in excel_files:
        name = os.path.splitext(f)[0]
        parts = name.split()
        if parts:
            match = re.search(r'\d+', parts[-1])
            if match:
                total += int(match.group())
    current_year = datetime.now().strftime('%Y')
    return f"2020 - {current_year} {total}.xlsx"

if __name__ == "__main__":
    # 获取用户输入
    folder_path = input("请输入包含Excel文件的文件夹路径: ")
    if os.path.isdir(folder_path):
        output_file = get_output_filename(folder_path)
        if output_file:
            print(f"自动生成的输出文件名: {output_file}")
            merge_excel_files(folder_path, output_file)
        else:
            print(f"在路径 '{folder_path}' 下没有找到Excel文件。")
    else:
        print("错误: 输入的路径不是一个有效的文件夹。")