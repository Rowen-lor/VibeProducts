import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import os
import json
import concurrent.futures
import threading

# 禁用 DevTools 日志
os.environ['DISABLE_DEVTOOLS_LOGGING'] = 'true'

# 配置文件路径
CONFIG_FILE = "login_config.json"

# 全局锁，用于保护对DataFrame的写入
df_lock = threading.Lock()

def create_config_template():
    """创建配置文件模板"""
    config_template = {
        "login_url": "example_url",  # 登录页面URL
        "username": "",  # 用户名
        "password": "",  # 密码
        "headless": True,  # 是否使用无头模式（建议先用False调试）
        "implicit_wait": 10,  # 隐式等待时间
        "page_load_timeout": 30,  # 页面加载超时时间
        "delay_between_requests": 2,  # 请求间隔时间（秒）
        "max_workers": 5, # 新增：最大并发线程数
        "skip_auto_login": False # 新增：是否跳过自动化登录，如果已手动登录并保存cookies
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_template, f, indent=4, ensure_ascii=False)
    
    print(f"已创建配置文件模板: {CONFIG_FILE}")
    print("请填写用户名和密码后重新运行脚本")
    return None

def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        return create_config_template()
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查必要的配置项
        required_fields = ['username', 'password', 'login_url']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            print(f"配置文件缺少必要信息: {', '.join(missing_fields)}")
            print(f"请编辑 {CONFIG_FILE} 文件并填写完整信息")
            return None
        
        # 确保max_workers存在且为正整数
        if 'max_workers' not in config or not isinstance(config['max_workers'], int) or config['max_workers'] <= 0:
            print("配置文件中 'max_workers' 配置不正确，将使用默认值 5")
            config['max_workers'] = 5

        return config
    except json.JSONDecodeError:
        print(f"错误: 配置文件 {CONFIG_FILE} 格式不正确，请检查JSON语法。")
        return None
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return None

def setup_driver(config):
    """设置Chrome浏览器驱动"""
    options = Options()
    
    headless_mode = config.get('headless', False) # 确保默认行为与配置文件模板一致
    # print(f"DEBUG: 从配置文件读取到的headless模式设置: {headless_mode}") # 注释掉调试信息
    if headless_mode:
        options.add_argument('--headless')
    
    # 添加选项避免检测
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--log-level=3') # 抑制不必要的日志输出
    options.add_argument('--silent') # 进一步减少输出
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"]) # 添加 enable-logging
    options.add_experimental_option('useAutomationExtension', False)
    
    # 禁用 WebRTC，进一步减少日志
    options.add_argument("--disable-webrtc")

    # 设置用户代理
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # 隐藏webdriver特征
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 设置超时时间
        driver.implicitly_wait(config.get('implicit_wait', 10))
        driver.set_page_load_timeout(config.get('page_load_timeout', 30))
        
        return driver
    except WebDriverException as e:
        print(f"Chrome驱动初始化失败: {e}")
        print("请确保已安装ChromeDriver并添加到PATH，或检查Chrome浏览器版本是否与ChromeDriver兼容。")
        return None
    except Exception as e:
        print(f"设置浏览器驱动时发生未知错误: {e}")
        return None

def auto_login(driver, config, max_retries=3):
    """尝试自动化登录"""
    login_url = config['login_url']
    username = config['username']
    password = config['password']
    
    for attempt in range(max_retries):
        try:
            # print(f"正在尝试登录: {login_url} (尝试 {attempt + 1}/{max_retries})") # 注释掉调试信息
            driver.get(login_url)
            wait = WebDriverWait(driver, 10)
            
            # 等待用户名输入框出现
            username_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='username' or @id='username' or @type='text']")))
            username_field.send_keys(username)
            # print(f"已输入用户名: {username}") # 注释掉调试信息
            
            # 等待密码输入框出现
            password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='password' or @id='password' or @type='password']")))
            password_field.send_keys(password)
            # print("已输入密码") # 注释掉调试信息
            
            # 等待登录按钮出现并点击
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' or @id='login-button' or @class='login-button'] | //input[@type='submit' or @id='login-button' or @class='login-button']")))
            login_button.click()
            # print("已点击登录按钮") # 注释掉调试信息
            
            # 等待页面跳转或某个登录成功后的元素出现
            # 这里需要根据实际登录成功后的页面特征来判断
            # 尝试判断登录是否成功：检查URL是否已跳转，或等待登录成功后的特定元素
            # 假设登录成功后会跳转到非登录页，或者某个特定元素（如用户头像、仪表盘链接）会出现
            # 请根据实际登录成功后的页面特征调整这里的判断逻辑
            time.sleep(config.get('delay_between_requests', 2)) # 给页面一些时间加载
            
            # 尝试通过URL判断
            if driver.current_url != login_url and "login" not in driver.current_url:
                # print("自动化登录：URL已跳转，初步判断登录成功。") # 注释掉调试信息
                return True
            
            # 尝试通过查找登录成功后的特定元素判断
            # 示例：查找页面中是否有id为'main-content'或class为'dashboard'的元素
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'ant-layout-header')] | //div[@id='root']"))) # 示例：可替换为实际登录成功后的页面元素
                # print("自动化登录：找到登录成功后的特定元素，判断登录成功。") # 注释掉调试信息
                return True
            except TimeoutException:
                # print(f"自动化登录：未找到登录成功后的特定元素，当前URL: {driver.current_url}") # 注释掉调试信息
                # 检查是否有错误消息
                try:
                    error_message_element = driver.find_element(By.XPATH, "//*[contains(@class, 'error-message') or contains(@class, 'ant-alert-message') or contains(@class, 'ant-notification-notice-description')]")
                    if error_message_element.is_displayed():
                        print(f"登录页面错误信息: {error_message_element.text}") # 保留错误信息
                except NoSuchElementException:
                    pass # 没有找到错误信息是正常的
                
                if attempt < max_retries - 1:
                    # print("自动化登录未成功，重试中...") # 注释掉调试信息
                    continue
                # print("自动化登录多次尝试失败。") # 注释掉调试信息
                return False
                
        except TimeoutException as e:
            print(f"自动化登录过程中元素加载超时: {login_url} - {e}") # 保留错误信息
            if attempt < max_retries - 1:
                # print("重试中...") # 注释掉调试信息
                time.sleep(2)
                continue
            return False
        except NoSuchElementException as e:
            print(f"自动化登录过程中未找到必要元素: {e}") # 保留错误信息
            if attempt < max_retries - 1:
                # print("重试中...") # 注释掉调试信息
                time.sleep(2)
                continue
            return False
        except Exception as e:
            print(f"自动化登录过程中发生未知错误: {e}") # 保留错误信息
            if attempt < max_retries - 1:
                # print("重试中...") # 注释掉调试信息
                time.sleep(2)
                continue
            return False
    return False

def get_status_from_url(driver, url, xpath, max_retries=3):
    """从指定URL获取状态信息"""
    for attempt in range(max_retries):
        try:
            # print(f"线程 {threading.current_thread().name}: 正在访问: {url} (尝试 {attempt + 1}/{max_retries})") # 注释掉调试信息
            driver.get(url)
            
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3) # 额外等待确保动态内容加载
            
            try:
                # 优先检查是否存在“Completion”步骤，以确定页面类型
                completion_title_xpath = "//div[@class='step_title' and text()='Completion']"
                driver.find_element(By.XPATH, completion_title_xpath)
                
                # 如果存在，说明是新页面类型，使用新逻辑判断状态
                try:
                    # 检查与“Completion”关联的SVG元素是否存在
                    svg_xpath = f"{completion_title_xpath}/ancestor::div[contains(@class, 'item_step_process')]//svg"
                    driver.find_element(By.XPATH, svg_xpath)
                    status = "Finished"
                    print(f"线程 {threading.current_thread().name}: 检测到 'Completion' 步骤已完成 (SVG), 状态: {status}")
                    return status
                except NoSuchElementException:
                    # 没有找到SVG，说明“Completion”步骤未完成
                    status = "Not Finished Yet" # 或其他表示未完成的状态
                    print(f"线程 {threading.current_thread().name}: 'Completion' 步骤未完成, 状态: {status}")
                    return status

            except NoSuchElementException:
                # 未找到“Completion”步骤，回退到旧的、通用的状态获取逻辑
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    status = element.text.strip()
                    
                    if status:
                        print(f"线程 {threading.current_thread().name}: 获取到状态: {status}") # 保留获取到状态的打印
                        return status
                    else:
                        # print(f"线程 {threading.current_thread().name}: 元素内容为空") # 注释掉调试信息
                        alt_text = element.get_attribute('title') or element.get_attribute('alt') or element.get_attribute('value')
                        if alt_text:
                            print(f"线程 {threading.current_thread().name}: 从属性获取到: {alt_text}") # 保留从属性获取到状态的打印
                            return alt_text.strip()
                        
                        if attempt < max_retries - 1:
                            # print(f"线程 {threading.current_thread().name}: 重试中...") # 注释掉调试信息
                            time.sleep(2)
                            continue
                        return "元素内容为空"
                        
                except NoSuchElementException:
                    # print(f"线程 {threading.current_thread().name}: 未找到指定元素 (XPath: {xpath})") # 注释掉，只返回状态
                    # print(f"线程 {threading.current_thread().name}: 当前页面标题: {driver.title}") # 注释掉调试信息
                    # print(f"线程 {threading.current_thread().name}: 当前页面URL: {driver.current_url}") # 注释掉调试信息
                    
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return "元素未找到"
                
        except TimeoutException:
            # print(f"线程 {threading.current_thread().name}: 页面加载超时: {url}") # 注释掉，只返回状态
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return "页面加载超时"
        except WebDriverException as e:
            # print(f"线程 {threading.current_thread().name}: WebDriver错误: {e}") # 注释掉，只返回状态
            if attempt < max_retries - 1:
                # print(f"线程 {threading.current_thread().name}: 重试中...") # 注释掉调试信息
                time.sleep(3)
                continue
            return f"WebDriver错误: {str(e)}"
        except Exception as e:
            # print(f"线程 {threading.current_thread().name}: 获取状态失败: {str(e)}") # 注释掉，只返回状态
            if attempt < max_retries - 1:
                # print(f"线程 {threading.current_thread().name}: 重试中...") # 注释掉调试信息
                time.sleep(3)
                continue
            return f"错误: {str(e)}"
    
    return "多次尝试失败"

def process_url_task(url_info, config, xpath, df):
    """单个URL处理任务，每个任务有自己的driver实例"""
    index, url = url_info
    thread_name = threading.current_thread().name
    # print(f"[{thread_name}] 开始处理第 {index + 1} 行URL: {url}") # 注释掉调试信息
    
    driver = None
    status = "初始化失败"
    try:
        driver = setup_driver(config)
        if driver is None:
            # print(f"[{thread_name}] 驱动初始化失败，跳过URL: {url}") # 注释掉，只返回状态
            status = "驱动初始化失败"
            return index, status
        
        # 自动化登录
        # 只有当skip_auto_login为False时才尝试登录
        if not config.get('skip_auto_login', False):
            if not auto_login(driver, config):
                # print(f"[{thread_name}] 自动化登录失败，跳过URL: {url}") # 注释掉，只返回状态
                status = "自动化登录失败"
                return index, status
        else:
            # print(f"[{thread_name}] 跳过自动化登录 (skip_auto_login=True)") # 注释掉，只返回状态
            pass # 无需打印跳过信息

        if pd.isna(url) or str(url).strip() == '':
            print(f"[{thread_name}] 第 {index + 1} 行URL为空，跳过")
            status = '空URL'
        else:
            url = str(url).strip()
            status = get_status_from_url(driver, url, xpath)
            
    except Exception as e:
        # print(f"[{thread_name}] 处理URL {url} 时发生未捕获错误: {e}") # 注释掉，只返回状态
        status = f"未捕获错误: {str(e)}"
    finally:
        if driver:
            # print(f"[{thread_name}] 关闭浏览器...") # 注释掉调试信息
            driver.quit()
    
    return index, status

def main():
    print("=== 状态检查脚本 (多线程版) ===")
    
    config = load_config()
    if config is None:
        return
    
    excel_file = r"D:\Rowen\Scripts\Status_inspection.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在: {excel_file}")
        return
    
    try:
        df = pd.read_excel(excel_file)
        # print(f"成功读取Excel文件，共 {len(df)} 行数据")
        # print(f"列名: {list(df.columns)}")
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return
    
    if len(df.columns) < 2:
        print("错误: Excel文件列数不足，至少需要2列")
        return
    
    url_column = df.iloc[:, 1]
    valid_urls_count = sum(1 for url in url_column if pd.notna(url) and str(url).strip())
    print(f"将处理第二列的 {valid_urls_count} 个有效URL")
    
    # 如果没有 New_Status 列，则在 Status 列后插入
    if 'New_Status' not in df.columns:
        status_col = None
        for idx, col in enumerate(df.columns):
            if col.lower() == 'status':
                status_col = idx
                break
        if status_col is not None:
            df.insert(status_col + 1, 'New_Status', '')
            print("已在Status列后创建New_Status列")
        else:
            df['New_Status'] = ''
            print("未找到Status列，已在末尾创建New_Status列")
    
    # 显式转换列类型为字符串，以避免FutureWarning
    df['New_Status'] = df['New_Status'].astype(str)
    
    xpath = "/html/body/div[1]/div/section/section/main/div/div/div/div/div/div/div[1]/div[1]/span[2]"
    # print(f"目标XPath: {xpath}")
    
    results = [] # 存储每个任务的结果 (index, status)
    
    # 使用ThreadPoolExecutor进行多线程处理
    max_workers = config.get('max_workers', 5)
    print(f"将使用 {max_workers} 个并发线程。")

    # 准备任务列表 (index, url)
    tasks = [(index, url) for index, url in enumerate(url_column)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务并获取Future对象
        future_to_url = {executor.submit(process_url_task, task, config, xpath, df): task for task in tasks}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            original_index, original_url = future_to_url[future]
            try:
                index, status = future.result()
                results.append((index, status))
                # print(f"\n--- 处理完成: {i + 1}/{len(tasks)} ---") # 注释掉调试信息
                # print(f"第 {index + 1} 行URL: {original_url} -> 状态: {status}") # 注释掉调试信息

                # 实时更新DataFrame并保存，这里需要加锁
                with df_lock:
                    df.loc[index, 'New_Status'] = status
                    # 每处理5个URL保存一次，或者根据需要调整保存频率
                    if (i + 1) % 5 == 0 or (i + 1) == len(tasks):
                        try:
                            df.to_excel(excel_file, index=False)
                            # print(f"💾 已保存中间结果 ({i + 1}/{len(tasks)})") # 注释掉调试信息
                        except Exception as e:
                            # print(f"保存中间结果失败: {e}") # 注释掉，只返回状态
                            pass # 不打印中间保存失败信息，因为最终会尝试保存
                
            except Exception as exc:
                # print(f"处理URL {original_url} (行 {original_index + 1}) 时发生异常: {exc}") # 注释掉，只返回状态
                results.append((original_index, f"异常: {exc}"))
                with df_lock:
                    df.loc[original_index, 'New_Status'] = f"异常: {exc}"

    # 统计结果
    success_count = 0
    error_count = 0
    for index, status in results:
        if status not in ["错误", "页面加载超时", "元素未找到", "多次尝试失败", "元素内容为空", "驱动初始化失败", "自动化登录失败"] and not status.startswith("错误:") and not status.startswith("WebDriver错误:") and not status.startswith("未捕获错误:") and not status.startswith("异常:"):
            success_count += 1
        else:
            error_count += 1

    # 最终保存结果
    try:
        df.to_excel(excel_file, index=False)
        print(f"\n=== 🎉 处理完成 ===")
        print(f"结果已保存到: {excel_file}")
        print(f"✓ 成功处理: {success_count} 个")
        print(f"✗ 处理失败: {error_count} 个")
        if (success_count + error_count) > 0:
            print(f"📊 成功率: {success_count/(success_count+error_count)*100:.1f}%")
        else:
            print("没有可处理的URL。")
    except Exception as e:
        print(f"保存Excel文件失败: {e}")
        backup_file = excel_file.replace('.xlsx', '_backup.xlsx')
        try:
            df.to_excel(backup_file, index=False)
            print(f"已保存到备份文件: {backup_file}")
        except Exception as e2:
            print(f"保存备份文件也失败: {e2}")

def cleanup_chrome_processes():
    """清理所有残留的Chrome进程"""
    print("\n正在清理Chrome进程...")
    try:
        # /F: 强制终止 /IM: 指定映像名称 /T: 终止指定进程及其所有子进程
        # > nul 2>&1: 抑制命令的输出
        os.system('taskkill /F /IM chrome.exe /T > nul 2>&1')
        print("Chrome进程清理完成。")
    except Exception as e:
        print(f"清理Chrome进程时出错: {e}")

if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup_chrome_processes()