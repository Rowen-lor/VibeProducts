import os
import re
from datetime import datetime
import openpyxl

def rename_reports(target_dir, log_callback):
    """
    分析并重命名指定目录下的周报Excel文件。

    :param target_dir: 包含周报文件的目录路径。
    :param log_callback: 用于将日志消息发送回GUI的函数。
    """
    log_callback(f"开始处理文件夹 '{target_dir}' 中的周报...\n")

    for filename in os.listdir(target_dir):
        if filename.endswith(".xlsx"):
            # 防止重命名已处理过的文件
            if re.match(r'^\d{4}( (H1|H2))? \d+\.xlsx$', filename):
                log_callback(f"跳过已重命名的文件: {filename}")
                continue

            file_path = os.path.join(target_dir, filename)
            
            try:
                workbook = openpyxl.load_workbook(file_path, data_only=True)
                sheet = workbook.active

                data_row_count = sheet.max_row - 1
                if data_row_count < 0:
                    data_row_count = 0

                date_cell_value = sheet["M2"].value

                if date_cell_value is None:
                    log_callback(f"警告：文件 '{filename}' 中的日期单元格M2为空。正在跳过文件。")
                    continue

                parsed_date = None
                if isinstance(date_cell_value, datetime):
                    parsed_date = date_cell_value
                elif isinstance(date_cell_value, str):
                    try:
                        parsed_date = datetime.strptime(date_cell_value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            parsed_date = datetime.strptime(date_cell_value, '%Y-%m-%d')
                        except ValueError:
                            pass
                
                if parsed_date is None:
                    log_callback(f"警告：文件 '{filename}' 中的单元格M2不包含有效日期或无法识别的格式。值为：'{date_cell_value}'。正在跳过文件。")
                    continue

                report_date = parsed_date.date()
                year = report_date.year
                month = report_date.month
                
                period = ""
                
                if report_date == datetime(2020, 7, 28).date():
                    period = ""
                elif 1 <= month <= 6:
                    period = "H1"
                elif 7 <= month <= 12:
                    period = "H2"

                output_parts = [str(year)]
                if period:
                    output_parts.append(period)
                output_parts.append(str(data_row_count))
                new_name_base = " ".join(output_parts)
                new_filename = f"{new_name_base}.xlsx"
                new_file_path = os.path.join(target_dir, new_filename)

                try:
                    workbook.close()
                    os.rename(file_path, new_file_path)
                    log_callback(f"重命名 '{filename}' -> '{new_filename}'")
                except OSError as rename_error:
                    log_callback(f"错误：无法重命名文件 '{filename}'。原因: {rename_error}")

            except Exception as e:
                log_callback(f"警告：无法处理文件 '{filename}'。原因：{e}。正在跳过文件。")
                continue
    log_callback("\n所有文件处理完毕。\n")