# pyinstaller --onefile --add-data "C:\pycharm\shibaba\model;model" main.py
# pyinstaller --onefile --add-data "E:\Project\PyCharm\HAVVK\model;model" main.py
# import os

# os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import os
import json
import random
import tkinter as tk
import tkinter.messagebox as messagebox
import pyautogui
import time
from screeninfo import get_monitors
from PIL import ImageGrab
import keyboard
import threading
import easyocr
import sys
import uuid
import socket
import hashlib
import numpy as np
import base64
import sys
import win32api
import win32con
import logging
from logging import handlers
from datetime import datetime
import glob
import platform
import subprocess
from logging import Filter
import cv2
import webbrowser
from version import VERSION
def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持打包后的环境"""
    try:
        # PyInstaller创建临时文件夹，并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def anti_debug():
    if sys.gettrace() is not None:  # 检测是否被调试
        sys.exit("Debugger detected!")


anti_debug()


class VersionFilter(Filter):
    def filter(self, record):
        record.version = VERSION
        return True

class UILogHandler(logging.Handler):
    """自定义日志处理器，将日志输出到UI界面"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        """输出日志记录到UI文本框"""
        try:
            msg = self.format(record)
            # 在主线程中更新UI
            self.text_widget.after(0, self._append_to_text, msg)
        except Exception:
            self.handleError(record)
    
    def _append_to_text(self, msg):
        """在文本框中添加日志消息"""
        try:
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)  # 自动滚动到最新日志
            self.text_widget.config(state=tk.DISABLED)
            
            # 限制日志行数，避免内存占用过多
            lines = self.text_widget.get('1.0', tk.END).split('\n')
            if len(lines) > 1000:  # 保留最新1000行
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.delete('1.0', f'{len(lines)-1000}.0')
                self.text_widget.config(state=tk.DISABLED)
        except Exception as e:
            print(f"UI日志输出错误: {e}")


# 配置文件路径
CONFIG_FILE = "config.json"
# 在文件顶部添加新的常量定义
LICENSE_KEY_FILE = "license.key"  # 新增的许可证保存文件
DEBUG_IMAGE_DIR = "debug_images"
LOG_DIR = "logs"
MAX_DEBUG_FILES = 100  # 最大截图保存数量

# 60刷新率下的时间延迟
MOVE_CLICK_DELAY = 0.08  # 从鼠标移动到鼠标点击的时间间隔，设置过小会导致点击失败，建议：0.08
PURCHASE_CAP_DELAY = 0.15  # 非拉满模式下，点击完物品之后到截图价格必要等待时间。设置过小会导致“未识别到文本”，建议：0.15
ITEM_200_BUTTON_DELAY = 0.05  # 拉满模式下，点击完物品之后到点击200按钮之间的等待时间，设置过小会点击不到200按钮，建议：0.05
PURCHASE_CAP_DELAY_200 = 0.06  # 拉满模式下，点击完200必须加上延迟，否则截图会截到拉满之前的值，建议：0.06
PURCHASE_RESULT_CAP_DELAY = 0.4  # 设置购买成功次数时，点击购买后，识别购买结果时的截图，必要的等待文字弹出时间。设置过小会导致识别失败，建议：0.4

# 如果没有logs文件夹，先创建
os.makedirs(LOG_DIR, exist_ok=True)  # 自动创建调试图片保存目录
# 配置
logger = logging.getLogger('log')
logger.setLevel(level=logging.DEBUG)  # logger记录日志的等级，设置为最低
# 输出格式
formatter = logging.Formatter(
    '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - v%(version)s: %(message)s'
)
# 输出到控制台的日志handler设置
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)  # 输出日志的等级，次低
stream_handler.setFormatter(formatter)  # 格式化
stream_handler.addFilter(VersionFilter())  # 添加过滤器
# 输出到文件的日志handler设置
time_rotating_file_handler = handlers.TimedRotatingFileHandler(filename='logs/log.log', when='D',
                                                               encoding='utf-8')  # 按天分割文件
time_rotating_file_handler.setLevel(logging.DEBUG)  # 输出日志的等级，最低
time_rotating_file_handler.setFormatter(formatter)  # 格式化
time_rotating_file_handler.addFilter(VersionFilter())  # 添加过滤器
# 输出到控制台和文件
logger.addHandler(stream_handler)
logger.addHandler(time_rotating_file_handler)


class DeltaLootBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("哈弗克军火商" + VERSION)
        # 其他初始化代码...
        os.makedirs(DEBUG_IMAGE_DIR, exist_ok=True)  # 自动创建调试图片保存目录

        # 获取屏幕分辨率
        self.monitor = get_monitors()[0]
        logger.info(f"屏幕分辨率: {self.monitor.width}x{self.monitor.height}")
        # 设置窗口初始尺寸和最小尺寸
        window_height = int(self.monitor.height * 0.6)  # 增加高度到60%
        window_width = int(self.monitor.width * 0.7)   # 宽度设为屏幕宽度的70%
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(800, 600)  # 设置最小尺寸
        self.root.resizable(True, True)  # 允许窗口大小调整

        # 在类初始化方法中添加列配置
        self.root.columnconfigure(1, weight=1)  # 保持右侧自动扩展
        self.root.rowconfigure(8, weight=1)  # 底部留出弹性空间

        # 创建UI组件后添加自动验证逻辑
        self.create_main_ui()
        
        # 设置UI日志处理器
        self.setup_ui_logger()

        # 自动加载先前的输入
        self.load_previous_input()
        
        # 如果鼠标点击延迟输入框为空，设置默认值
        if not self.move_click_delay_entry.get():
            self.move_click_delay_entry.insert(0, '0.15')
        
        # 如果重启间隔输入框为空，设置默认值
        if not self.restart_interval_entry.get():
            self.restart_interval_entry.insert(0, '10')


        # 其他初始化
        self.running = False
        self.timer_thread = None  # 计时器线程
        self.timer_cancelled = False  # 计时器取消标志
        self.hotkey_setup()

        # 加载模型路径
        model_path = 'model'
        if getattr(sys, 'frozen', False):
            model_path = os.path.join(sys._MEIPASS, 'model')
        # self.reader = easyocr.Reader(['en'], download_enabled=True, model_storage_directory=model_path)  # 英文识别
        self.charactor_reader = easyocr.Reader(['ch_sim', 'en'], download_enabled=True,
                                               model_storage_directory=model_path)  # 中英文识别

    def setup_ui_logger(self):
        """设置UI日志处理器"""
        # 创建自定义处理器
        ui_handler = UILogHandler(self.log_text)
        ui_handler.setLevel(logging.INFO)  # 只显示INFO及以上级别的日志
        
        # 设置格式
        ui_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', 
                                       datefmt='%H:%M:%S')
        ui_handler.setFormatter(ui_formatter)
        ui_handler.addFilter(VersionFilter())
        
        # 添加到logger
        logger.addHandler(ui_handler)
        
        # 添加欢迎信息
        logger.info("哈弗克军火商已启动，准备就绪")
    
    def hotkey_setup(self):
        # 设置快捷键，F12 控制开始暂停或取消计时
        keyboard.add_hotkey('F12', self.toggle_bot_or_cancel_timer)

    def toggle_bot_or_cancel_timer(self):
        """F12热键处理：如果有计时器在运行则取消，否则开始/暂停抢货"""
        # 如果有计时器在运行，取消计时器
        if self.timer_thread and self.timer_thread.is_alive() and not self.timer_cancelled:
            self.cancel_timer()
            return
        
        # 否则执行原来的开始/暂停逻辑
        if self.running:
            self.running = False
            logger.info("抢货已暂停")
        else:
            self.check_start_time_and_start()
    
    def toggle_bot(self):
        """原始的开始/暂停方法，供内部调用"""
        if self.running:
            self.running = False
            logger.info("抢货已暂停")
        else:
            self.running = True
            logger.info("抢货已开始")
            self.start_bot()

    def validate_number_input(self, value):
        """验证输入是否为数字（用于输入框验证）"""
        if value == "":
            return True  # 允许空值
        try:
            int(value)
            return len(value) <= 2  # 限制最多2位数字
        except ValueError:
            return False
    
    def validate_time_format(self, hour_str, minute_str):
        """验证时间格式是否正确"""
        # 如果都为空，表示立即开始
        if not hour_str.strip() and not minute_str.strip():
            return True
        
        # 如果只有一个为空，返回False
        if not hour_str.strip() or not minute_str.strip():
            return False
        
        try:
            hour = int(hour_str.strip())
            minute = int(minute_str.strip())
            
            # 验证小时范围 0-23
            if hour < 0 or hour > 23:
                return False
            
            # 验证分钟范围 0-59
            if minute < 0 or minute > 59:
                return False
            
            return True
        except ValueError:
            return False
    
    def parse_start_time(self, hour_str, minute_str):
        """解析开始时间，返回小时和分钟"""
        if not hour_str.strip() and not minute_str.strip():
            return None, None
        
        try:
            hour = int(hour_str.strip())
            minute = int(minute_str.strip())
            return hour, minute
        except ValueError:
            return None, None
    
    def calculate_delay_seconds(self, target_hour, target_minute):
        """计算到目标时间的延迟秒数"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # 如果目标时间已过，设置为明天的同一时间
        if target_time <= now:
            target_time += timedelta(days=1)
        
        delay = (target_time - now).total_seconds()
        return delay, target_time
    
    def check_start_time_and_start(self):
        """检查开始时间并启动"""
        hour_str = self.start_hour_entry.get().strip()
        minute_str = self.start_minute_entry.get().strip()
        
        # 验证时间格式
        if not self.validate_time_format(hour_str, minute_str):
            logger.error("开始时间格式错误，请输入正确的小时(0-23)和分钟(0-59)")
            messagebox.showerror("时间格式错误", "请输入正确的小时(0-23)和分钟(0-59)")
            return
        
        # 如果没有设置时间，立即开始
        if not hour_str and not minute_str:
            self.toggle_bot()
            return
        
        # 解析时间
        hour, minute = self.parse_start_time(hour_str, minute_str)
        if hour is None or minute is None:
            logger.error("开始时间解析失败")
            messagebox.showerror("时间解析错误", "时间解析失败，请检查输入")
            return
        
        # 计算延迟
        delay_seconds, target_time = self.calculate_delay_seconds(hour, minute)
        
        logger.info(f"计划在 {target_time.strftime('%Y-%m-%d %H:%M:%S')} 开始抢货，倒计时 {int(delay_seconds)} 秒")
        
        # 启动计时器
        self.start_timer(delay_seconds, target_time)
    
    def start_timer(self, delay_seconds, target_time):
        """启动计时器"""
        self.timer_cancelled = False
        self.timer_thread = threading.Thread(target=self._timer_worker, args=(delay_seconds, target_time))
        self.timer_thread.start()
    
    def _timer_worker(self, delay_seconds, target_time):
        """计时器工作线程"""
        remaining = int(delay_seconds)
        
        while remaining > 0 and not self.timer_cancelled:
            if remaining <= 60:  # 最后一分钟每秒更新
                logger.info(f"倒计时：{remaining} 秒后开始抢货")
                time.sleep(1)
                remaining -= 1
            elif remaining <= 300:  # 最后5分钟每10秒更新
                logger.info(f"倒计时：{remaining} 秒后开始抢货")
                time.sleep(10)
                remaining -= 10
            else:  # 超过5分钟每分钟更新
                minutes = remaining // 60
                logger.info(f"倒计时：{minutes} 分钟后开始抢货")
                time.sleep(60)
                remaining -= 60
        
        if not self.timer_cancelled:
            logger.info("计时结束，开始抢货！")
            # 在主线程中启动机器人
            self.root.after(0, self.toggle_bot)
    
    def cancel_timer(self):
        """取消计时器"""
        self.timer_cancelled = True
        if self.timer_thread:
            logger.info("计时器已取消")
            self.timer_thread = None
    
    def start_bot(self):
        if not self.running:
            return

        # 保存当前输入
        self.save_current_input()

        # 启动线程执行抢货操作，避免阻塞UI
        bot_thread = threading.Thread(target=self.run_bot)
        bot_thread.start()

    def create_main_ui(self):
        """创建主功能部分的UI"""
        # 创建主框架 - 左右布局
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧控制面板
        left_frame = tk.Frame(main_frame, relief=tk.RAISED, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # 右侧日志面板
        right_frame = tk.Frame(main_frame, relief=tk.RAISED, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 在左侧面板中创建控件
        padx = 8
        pady = 5  # 主功能区间距

        # 官方网站链接 - 显眼位置
        website_frame = tk.Frame(left_frame, bg='#e6f3ff', relief=tk.RAISED, bd=2)
        website_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=padx, pady=(pady, 10))
        website_label = tk.Label(website_frame, text="🌐 官方网站: sjz.tenee.top", 
                                fg='#0066cc', bg='#e6f3ff', font=('Arial', 10, 'bold'),
                                cursor='hand2')
        website_label.pack(pady=5)
        website_label.bind("<Button-1>", self.open_website)
        
        # 物品信息
        self.item_name_label = tk.Label(left_frame, text="物品名称:")
        self.item_name_label.grid(row=1, column=0, sticky="w", padx=padx, pady=pady)
        self.item_name_entry = tk.Entry(left_frame, width=25)
        self.item_name_entry.grid(row=1, column=1, sticky="w", padx=padx, pady=pady)
        self.purchase_num_label = tk.Label(left_frame, text="(不填默认抢第一个)")
        self.purchase_num_label.grid(row=1, column=2, sticky="w", padx=padx, pady=pady)

        # 是否为枪械
        self.is_gun_var_lable = tk.Label(left_frame, text="物品是否是枪械:")
        self.is_gun_var_lable.grid(row=2, column=0, sticky="w", padx=padx, pady=pady)
        self.is_gun_var = tk.BooleanVar(value=False)  # 默认不勾选
        self.is_gun_check = tk.Checkbutton(
            left_frame,
            text="是枪械",
            variable=self.is_gun_var
        )
        self.is_gun_check.grid(row=2, column=1, sticky='w', padx=padx, pady=pady)

        # 购买页是否可兑换
        self.exchangeable_lable = tk.Label(left_frame, text="购买页是否可兑换:")
        self.exchangeable_lable.grid(row=3, column=0, sticky="w", padx=padx, pady=pady)
        self.exchangeable_var = tk.BooleanVar(value=False)  # 默认不勾选
        self.exchangeable_check = tk.Checkbutton(
            left_frame,
            text="可兑换",
            variable=self.exchangeable_var
        )
        self.exchangeable_check.grid(row=3, column=1, sticky='w', padx=padx, pady=pady)
        
        # 1k显示屏备用方案
        self.use_1k_backup_label = tk.Label(left_frame, text="1k显示屏备用方案:")
        self.use_1k_backup_label.grid(row=3, column=2, sticky="w", padx=padx, pady=pady)
        self.use_1k_backup_var = tk.BooleanVar(value=False)  # 默认不勾选
        self.use_1k_backup_check = tk.Checkbutton(
            left_frame,
            text="启用备用方案",
            variable=self.use_1k_backup_var
        )
        self.use_1k_backup_check.grid(row=3, column=3, sticky='w', padx=padx, pady=pady)

        # 单次数量拉满选项
        self.full_quantity_label = tk.Label(left_frame, text="购买数量是否拉满:")
        self.full_quantity_label.grid(row=4, column=0, sticky="w", padx=padx, pady=pady)
        self.full_quantity_var = tk.BooleanVar(value=False)  # 默认不勾选
        self.full_quantity_check = tk.Checkbutton(
            left_frame,
            text="拉满",
            variable=self.full_quantity_var
        )
        self.full_quantity_check.grid(row=4, column=1, sticky='w', padx=padx, pady=pady)

        # 价格上限
        self.price_high_label = tk.Label(left_frame, text="最高购买价格:")
        self.price_high_label.grid(row=5, column=0, sticky="w", padx=padx, pady=pady)
        self.price_high_entry = tk.Entry(left_frame, width=15)
        self.price_high_entry.grid(row=5, column=1, sticky="w", padx=padx, pady=pady)

        # 开始时间
        self.start_time_label = tk.Label(left_frame, text="开始时间:")
        self.start_time_label.grid(row=6, column=0, sticky="w", padx=padx, pady=pady)
        
        # 创建时间输入框架
        time_frame = tk.Frame(left_frame)
        time_frame.grid(row=6, column=1, sticky="w", padx=padx, pady=pady)
        
        # 注册数字验证函数
        vcmd = (self.root.register(self.validate_number_input), '%P')
        
        # 小时输入框
        self.start_hour_entry = tk.Entry(time_frame, width=3, validate='key', validatecommand=vcmd)
        self.start_hour_entry.pack(side=tk.LEFT)
        
        # 分隔符
        tk.Label(time_frame, text=":").pack(side=tk.LEFT, padx=2)
        
        # 分钟输入框
        self.start_minute_entry = tk.Entry(time_frame, width=3, validate='key', validatecommand=vcmd)
        self.start_minute_entry.pack(side=tk.LEFT)
        
        self.start_time_unit_label = tk.Label(left_frame, text="小时:分钟，不填立即开始")
        self.start_time_unit_label.grid(row=6, column=2, sticky="w", padx=padx, pady=pady)

        # 定时（分钟）
        self.pause_clock_label = tk.Label(left_frame, text="定时停止（分钟）:")
        self.pause_clock_label.grid(row=7, column=0, sticky="w", padx=padx, pady=pady)
        self.pause_clock_entry = tk.Entry(left_frame, width=15)
        self.pause_clock_entry.grid(row=7, column=1, sticky="w", padx=padx, pady=pady)

        # 检测间隔
        self.detect_time_label = tk.Label(left_frame, text="检测间隔:")
        self.detect_time_label.grid(row=8, column=0, sticky="w", padx=padx, pady=pady)
        self.detect_time_entry = tk.Entry(left_frame, width=15)
        self.detect_time_entry.grid(row=8, column=1, sticky="w", padx=padx, pady=pady)
        self.detect_time_unit_label = tk.Label(left_frame, text="秒(默认0.05)")
        self.detect_time_unit_label.grid(row=8, column=2, sticky="w", padx=padx, pady=pady)

        # 鼠标点击延迟
        self.move_click_delay_label = tk.Label(left_frame, text="鼠标点击延迟:")
        self.move_click_delay_label.grid(row=9, column=0, sticky="w", padx=padx, pady=pady)
        self.move_click_delay_entry = tk.Entry(left_frame, width=15)
        self.move_click_delay_entry.grid(row=9, column=1, sticky="w", padx=padx, pady=pady)
        self.move_click_delay_unit_label = tk.Label(left_frame, text="秒(默认0.15)")
        self.move_click_delay_unit_label.grid(row=9, column=2, sticky="w", padx=padx, pady=pady)

        # 风险项分割线
        self.risk_separator = tk.Label(left_frame,
                                       text="-------------------设置以下选项可能产生误买或多买------------------")
        self.risk_separator.grid(row=10, columnspan=4, sticky="w", padx=padx, pady=pady)

        # 购买次数
        self.purchase_num_label = tk.Label(left_frame, text="购买成功次数:")
        self.purchase_num_label.grid(row=11, column=0, sticky="w", padx=padx, pady=pady)
        self.purchase_num_entry = tk.Entry(left_frame, width=15)
        self.purchase_num_entry.grid(row=11, column=1, sticky="w", padx=padx, pady=pady)
        self.purchase_num_label = tk.Label(left_frame, text="(不限次数可不填)")
        self.purchase_num_label.grid(row=11, column=2, sticky="w", padx=padx, pady=pady)

        # 误购保护分组框
        risk_frame = tk.LabelFrame(
            left_frame,
        )
        risk_frame.grid(
            row=12,
            column=0,
            columnspan=4,
            padx=8,
            pady=5,
            sticky="ew"
        )

        # 关闭误购保护（调整到分组框内部）
        self.close_anti_cheat_label = tk.Label(risk_frame, text="关闭误购保护:")
        self.close_anti_cheat_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.close_anti_cheat_var = tk.BooleanVar(value=False)
        self.close_anti_cheat_check = tk.Checkbutton(
            risk_frame,
            text="关闭",
            variable=self.close_anti_cheat_var,
            command=self.toggle_price_low
        )
        self.close_anti_cheat_check.grid(row=0, column=1, sticky='w', padx=5, pady=2)

        # 价格下限（调整到分组框内部）
        self.price_low_label = tk.Label(risk_frame, text="请设置最低购买价格:")
        self.price_low_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)

        self.price_low_entry = tk.Entry(risk_frame, width=15, state=tk.DISABLED)
        self.price_low_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # 绑定变量状态监听
        self.close_anti_cheat_var.trace_add("write", self.on_anti_cheat_toggle)
        # 初始化状态
        self.toggle_price_low()

        # 定时重启分组框
        restart_frame = tk.LabelFrame(
            left_frame,
            text="定时切换模式设置"
        )
        restart_frame.grid(
            row=13,
            column=0,
            columnspan=4,
            padx=8,
            pady=5,
            sticky="ew"
        )

        # 启用定时重启
        self.auto_restart_var = tk.BooleanVar(value=True)  # 默认启用
        self.auto_restart_check = tk.Checkbutton(
            restart_frame,
            text="启用定时切换模式",
            variable=self.auto_restart_var
        )
        self.auto_restart_check.grid(row=0, column=0, sticky='w', padx=5, pady=2)

        # 重启间隔
        self.restart_interval_label = tk.Label(restart_frame, text="重启间隔:")
        self.restart_interval_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.restart_interval_entry = tk.Entry(restart_frame, width=10)
        self.restart_interval_entry.grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.restart_interval_unit_label = tk.Label(restart_frame, text="分钟(默认10)")
        self.restart_interval_unit_label.grid(row=0, column=3, sticky="w", padx=5, pady=2)

        # 开始提示
        self.start_label = tk.Label(left_frame, text="在交易行界面按【F12】开始/暂停")
        self.start_label.grid(row=14, columnspan=2, pady=15)
        
        # 右侧日志显示区域
        self.log_label = tk.Label(right_frame, text="实时日志:", font=("Arial", 12, "bold"))
        self.log_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # 创建日志文本框和滚动条
        log_container = tk.Frame(right_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_container, height=25, wrap=tk.WORD, state=tk.DISABLED, 
                               font=("Consolas", 9), bg="#f8f8f8")
        log_scrollbar = tk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def open_website(self, event):
        """打开官方网站"""
        try:
            webbrowser.open("https://sjz.tenee.top")
            logger.info("已打开官方网站: sjz.tenee.top")
        except Exception as e:
            logger.error(f"打开网站失败: {str(e)}")

    def run_bot(self):

        if self.monitor.width == 1920 and self.monitor.height == 1080:  # 1K
            if self.use_1k_backup_var.get():
                logger.info("检测到当前屏幕为1080p分辨率，使用备用方案")
                self.click_positions = self.get_click_positions_1k_2()
            else:
                logger.info("检测到当前屏幕为1080p分辨率")
                self.click_positions = self.get_click_positions_1k()
        elif self.monitor.width == 2560 and self.monitor.height == 1440:  # 2K
            self.click_positions = self.get_click_positions_2k()
            logger.info("检测到当前屏幕为2K分辨率")
        elif self.monitor.width == 3840 and self.monitor.height == 2160:  # 4K
            logger.info("检测到当前屏幕为4K分辨率")
            self.click_positions = self.get_click_positions_4k()
        elif self.monitor.width == 2560 and self.monitor.height == 1600:  # 16:10的2K
            logger.info("检测到当前屏幕为2560x1600分辨率")
            self.click_positions = self.get_click_positions_2560x1600()
        elif self.monitor.width == 1600 and self.monitor.height == 900:
            logger.info("检测到当前屏幕为1600x900分辨率")
            self.click_positions = self.get_click_positions_1600x900()
        elif self.monitor.width == 1920 and self.monitor.height == 1200:  # 16:10的1k
            logger.info("检测到当前屏幕为1920x1200分辨率")
            self.click_positions = self.get_click_positions_1920x1200()
        elif self.monitor.width == 3440 and self.monitor.height == 1440:  # 3440x1440
            logger.info("检测到当前屏幕为3440x1440分辨率")
            self.click_positions = self.get_click_positions_3440x1440()
        else:
            logger.info("不支持的当前屏幕的分辨率，请联系管理员更新软件版本")
            return

        # 模拟点击三角洲行动窗口，并执行抢货逻辑
        self.ultra_fast_click(self.click_positions['market'],self.user_delay_time(ITEM_200_BUTTON_DELAY))
        # 如果输入了物品名称，把它填到输入框
        if self.item_name_entry.get():
            # 点击输入框
            self.ultra_fast_click(self.click_positions['input_field'])
            # 清空
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            time.sleep(0.01)
            # 模拟键盘输入物品名称
            self.typewrite(self.item_name_entry.get())

        # 先进行预识别，获取当前市场价，用于后续检测价格识别错误问题
        last_correct_price = self.pre_capture()

        attempt_count = 0  # 尝试购买次数
        success_count = 0  # 购买成功次数
        ocr_fail_count = 0  # 识别失败次数
        refresh_count = 0  # 刷新次数
        start_time = time.time()  # 记录开始时间
        last_restart_time = start_time  # 记录上次重启时间
        low_price = last_correct_price  # 最低正常价格，用于抢卡时判断当日补货价
        while self.running:
            # 模拟点击物品位置
            self.ultra_fast_click(self.click_positions['item'])

            # 拉满
            if self.full_quantity_var.get():
                self.ultra_fast_click(self.get_200_button_pos(), self.user_delay_time(ITEM_200_BUTTON_DELAY))
                # 是枪械，则识别绿色按钮
                if self.is_gun_var.get():
                    price = self.get_price_ocr(self.click_positions['price_area_green'],
                                               float(self.price_high_entry.get()),
                                               self.user_delay_time(PURCHASE_CAP_DELAY_200))
                # 不是枪械，识别平均价格
                else:
                    price = self.get_price_ocr(self.get_price_area(),
                                               float(self.price_high_entry.get()),
                                               self.user_delay_time(PURCHASE_CAP_DELAY_200))
            # 不拉满
            else:
                # 是枪械，则识别绿色按钮
                if self.is_gun_var.get():
                    price = self.get_price_ocr(self.click_positions['price_area_green'],
                                               float(self.price_high_entry.get()),
                                               self.user_delay_time(PURCHASE_CAP_DELAY))
                # 不是枪械，识别平均价格
                else:
                    price = self.get_price_ocr(self.get_price_area(), float(self.price_high_entry.get()),
                                               self.user_delay_time(PURCHASE_CAP_DELAY))

            # 校验识别到的price
            # 如果关闭了误购保护,只需要判断价格是否在设定范围内
            if self.close_anti_cheat_var.get():
                is_buy_price, ocr_fail_count, last_correct_price = self.price_check_unsafe(price,
                                                                                           float(
                                                                                               self.price_high_entry.get()),
                                                                                           float(
                                                                                               self.price_low_entry.get()),
                                                                                           last_correct_price,
                                                                                           ocr_fail_count)
            else:
                # 未关闭误购保护，需要判断价格在设定范围内，且价格高于上次价格的一半以上，或和上次价格位数相同
                is_buy_price, ocr_fail_count, last_correct_price = self.price_check(price,
                                                                                    float(self.price_high_entry.get()),
                                                                                    last_correct_price, ocr_fail_count)
            if is_buy_price:
                # 符合条件，购买
                logger.info(f"价格满足条件，购买: {price}")
                self.ultra_fast_click(self.get_buy_button_pos())
                attempt_count += 1
                # 根据购买成功次数停止程序
                if len(self.purchase_num_entry.get()):
                    if self.get_purchase_result_ocr(self.click_positions['purchase_result'],
                                                    self.user_delay_time(PURCHASE_RESULT_CAP_DELAY)):
                        success_count += 1
                        if success_count >= int(self.purchase_num_entry.get()):
                            self.running = False
                            logger.info("已达到购买次数，抢货已暂停")
                self.press_esc()
            else:
                # 价格不符合条件，不购买
                self.press_esc()
                if ocr_fail_count > 4:
                    pyautogui.click(self.click_positions['market'])
                    time.sleep(0.01)
                    pyautogui.click(self.click_positions['market'])
                    time.sleep(0.01)
                    pyautogui.click(self.click_positions['market'])
                    ocr_fail_count = 0
            # 更新最低正常价
            if price is not None and low_price is not None and price < low_price:
                low_price = price
            # 更新刷新次数
            refresh_count += 1
            # 每50次刷新打印一次最低正常价
            if refresh_count % 50 == 0:
                logger.info(f"当前刷到过的最低价: {low_price}")
            # 定时停止
            if len(self.pause_clock_entry.get()):
                elapsed_time = time.time() - start_time
                if elapsed_time >= float(self.pause_clock_entry.get()) * 60:
                    self.running = False
                    logger.info("已达到定时停止时间，抢货已暂停")
            
            # 定时重启检查
            if self.auto_restart_var.get() and len(self.restart_interval_entry.get()):
                try:
                    restart_interval = float(self.restart_interval_entry.get()) * 60  # 转换为秒
                    elapsed_since_restart = time.time() - last_restart_time
                    if elapsed_since_restart >= restart_interval:
                        logger.info(f"达到定时切换模式间隔({self.restart_interval_entry.get()}分钟)，开始执行切换模式")
                        if self.auto_restart_purchase():
                            last_restart_time = time.time()  # 更新重启时间
                            logger.info("定时重启完成，继续抢购")
                        else:
                            logger.warning("定时切换模式失败，停止抢购")
                            self.running = False
                except ValueError:
                    logger.warning("切换模式间隔设置无效，跳过定时切换模式")
                except Exception as e:
                    logger.error(f"定时切换模式检查出错: {str(e)}", exc_info=True)

    def get_price_ocr(self, price_area, target_high_price, pre_delay=0.0, max_retry=3):
        time.sleep(pre_delay)
        for _ in range(max_retry):
            
            # 截取价格区域并进行预处理
            screenshot = ImageGrab.grab(bbox=price_area)
            screenshot_arr = np.array(screenshot)
            result = self.charactor_reader.readtext(screenshot_arr, detail=0)

            if result:
                # EasyOCR返回的是文本列表，合并为单个字符串再提取数字
                text = ''.join(result)
                digits = ''.join(filter(str.isdigit, text))
                try:
                    price = float(digits)

                    # 调试用：启动子线程保存截图（不阻塞主线程）
                    threading.Thread(
                        target=self.save_image_to_disk,
                        args=(screenshot, price,),
                        daemon=True  # 设置为守护线程，主退出时自动结束
                    ).start()

                    if price < target_high_price:
                        # 启动子线程保存购买截图（不阻塞主线程）
                        threading.Thread(
                            target=self.save_image_to_disk,
                            args=(screenshot, price,),
                            daemon=True  # 设置为守护线程，主退出时自动结束
                        ).start()
                    return price
                except ValueError:
                    logger.error("价格格式错误:", text)
                    return None
            else:
                logger.info("未识别到文本，等待")
                time.sleep(0.05)
        logger.warning("OCR连续失败")
        return None



    def get_purchase_result_ocr(self, purchase_result, pre_delay=0.0):
        time.sleep(pre_delay)
        # 截取购买结果提示区域并进行预处理
        screenshot = ImageGrab.grab(bbox=purchase_result)
        screenshot_arr = np.array(screenshot)
        result = self.charactor_reader.readtext(screenshot_arr, detail=0)

        # 启动子线程保存购买结果截图（不阻塞主线程）
        threading.Thread(
            target=self.save_image_to_disk,
            args=(screenshot, result,),
            daemon=True  # 设置为守护线程，主退出时自动结束
        ).start()
        if result:
            # EasyOCR返回的是文本列表，合并为单个字符串再提取关键字符
            text = ''.join(result)
            # 处理购买结果判断
            # 定义关键词集合（使用Unicode精确匹配）
            failure_keywords = {'失', '败', '售'}
            success_keywords = {'成', '功', '存', '入'}
            success_cheaper_keywords = {'用', '更', '交'}
            # 转换为字符集合（去重优化）
            char_set = set(text)
            # 如果字符集内包含failure_keywords同时也包含success_keywords或success_cheaper_keywords，返回True
            if char_set & failure_keywords and char_set & success_keywords:
                logger.info("购买结果包含失败和成功的关键词，可能存在误判，视为购买成功")
                return True
            # 优先判断失败条件（业务逻辑优先级）
            if char_set & failure_keywords:
                logger.info("购买失败，最低价格道具已售完")
                return False
            # 再判断成功条件
            elif char_set & success_keywords:
                if char_set & success_cheaper_keywords:
                    logger.info("购买成功，价格更新，已用更低价格成交")
                    return True
                logger.info("购买成功，已存入仓库")
                return True

            # 无匹配时的默认处理
            logger.info("购买结果识别失败，默认视为购买成功")
            return True

        else:
            logger.info("未识别到购买结果文本，默认视为购买成功")
            return True

    def scale_positions(self, pos_dict, x_scale, y_scale=None):
        if y_scale is None:
            y_scale = x_scale
        out = {}
        for k, v in pos_dict.items():
            if isinstance(v, tuple):
                out[k] = tuple(round(v[i] * (x_scale if i % 2 == 0 else y_scale))
                               for i in range(len(v)))
            else:
                out[k] = v
        return out
    def get_click_positions_1k(self):
        # 根据分辨率返回不同的点击坐标
        return {
            'market': (712, 52),
            'input_field': (180, 172),
            'item': (618, 225),
            'item_price': (791, 278, 893, 300),
            'price_area_green': (1517.0, 904.0, 1769.0, 954.0),  # 绿色
            'price_area': (1630, 875, 1753, 900),  # 均价
            'buy_button': (1575, 937),
            'purchase_result': (675, 154, 1245, 184),  # 购买结果
            '200_button': (1745, 845),  # 200按钮位置
            '200_button_s4_exchangeable': (1760, 800),  # s4赛季，可兑换商品，200按钮位置
            'buy_button_s4_exchangeable': (1663, 880),  # s4赛季，可兑换商品，购买按钮位置
            'price_area_s4_exchangeable': (1577.0, 822.0, 1757.0, 845.0),  # s4赛季，可兑换商品，均价位置
    }

    def get_click_positions_1k_2(self):
        return self.scale_positions(self.get_click_positions_2k(), 0.75)
    def get_click_positions_2k(self):
        return {
            'market': (950, 70),
            'input_field': (240, 230),
            'item': (824, 300),
            'item_price': (1055, 370, 1190, 440),
            'price_area_green': (2130.0, 1200.0, 2260.0, 1240.0),  #绿色
            'price_area': (2175.0, 1150.0, 2310.0, 1180.0),  #均价
            'buy_button': (2180, 1220),  # 购买按钮位置
            'purchase_result': (900, 205, 1660, 290),  # 购买结果
            '200_button': (2327, 1110),  # 200按钮位置
            '200_button_s4_exchangeable': (2325, 1035),  # s4赛季，可兑换商品，200按钮位置
            'buy_button_s4_exchangeable': (2100, 1150),  # s4赛季，可兑换商品，购买按钮位置
            'price_area_s4_exchangeable': (2175.0, 1075.0, 2312.0, 1100.0),  # s4赛季，可兑换商品，均价位置
        }

    def get_click_positions_4k(self):
        """从2K坐标自动换算得到4K坐标(乘以1.5)"""
        return self.scale_positions(self.get_click_positions_2k(), 1.5)

    def get_click_positions_1600x900(self):
        """从2K坐标自动换算得到1600x900坐标(乘以0.625)"""
        return self.scale_positions(self.get_click_positions_2k(), 0.625)
    # 16:10的2k
    def get_click_positions_2560x1600(self):
        return {
            'market': (950, 70),
            'input_field': (240, 230),
            'item': (880, 350),
            'item_price': (1059, 370, 1190, 430),
            'price_area_green': (2130.0, 1360.0, 2270.0, 1400.0),  #绿色
            'price_area': (2175.0, 1310.0, 2310.0, 1340.0),  #均价

            'buy_button': (2190, 1380),  # 购买按钮位置
            'purchase_result': (700, 180, 1635, 285),  # 购买结果
            '200_button': (2325, 1270),  # 200按钮位置
            '200_button_s4_exchangeable': (2325, 1195),  # s4赛季，可兑换商品，200按钮位置
            'buy_button_s4_exchangeable': (2170, 1300),  # s4赛季，可兑换商品，购买按钮位置
            'price_area_s4_exchangeable': (2175, 1235, 2312, 1260),  # s4赛季，可兑换商品，均价位置
        }

    # 16:10的1k
    def get_click_positions_1920x1200(self):
        """从2560x1600坐标自动换算得到1920x1200坐标(乘以0.75)"""
        return self.scale_positions(self.get_click_positions_2560x1600(), 0.75)
    def get_click_positions_3440x1440(self):
        return {
            'market': (1390, 70),
            'input_field': (700, 230),
            'item': (1300, 300),
            'item_price': (1495, 370, 1630, 440),
            'price_area_green': (2570.0, 1200.0, 2710.0, 1240.0),  #绿色
            'price_area': (2615.0, 1150.0, 2750.0, 1180.0),  #均价

            'buy_button': (2620, 1220),  # 购买按钮位置
            'purchase_result': (1010, 205, 2070, 290),  # 购买结果
            '200_button': (2765, 1110),  # 200按钮位置
            '200_button_s4_exchangeable': (2765, 1035),  # s4赛季，可兑换商品，200按钮位置
            'buy_button_s4_exchangeable': (2620, 1150),  # s4赛季，可兑换商品，购买按钮位置
            'price_area_s4_exchangeable': (2615.0, 1075.0, 2750.0, 1100.0),  # s4赛季，可兑换商品，均价位置
        }

    def typewrite(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'v')

    def load_previous_input(self):
        """从配置文件加载之前的输入"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # 先清空输入框，再插入配置值，避免重复累加
                self.item_name_entry.delete(0, tk.END)
                self.item_name_entry.insert(0, config_data.get('item_name', ''))
                self.price_high_entry.delete(0, tk.END)
                self.price_high_entry.insert(0, config_data.get('price_threshold', ''))
                self.purchase_num_entry.delete(0, tk.END)
                self.purchase_num_entry.insert(0, config_data.get('purchase_number', ''))
                self.start_hour_entry.delete(0, tk.END)
                self.start_hour_entry.insert(0, config_data.get('start_hour', ''))
                self.start_minute_entry.delete(0, tk.END)
                self.start_minute_entry.insert(0, config_data.get('start_minute', ''))
                self.detect_time_entry.delete(0, tk.END)
                self.detect_time_entry.insert(0, config_data.get('detect_time', '0.05'))
                self.move_click_delay_entry.delete(0, tk.END)
                self.move_click_delay_entry.insert(0, config_data.get('move_click_delay', '0.15'))
                self.restart_interval_entry.delete(0, tk.END)
                self.restart_interval_entry.insert(0, config_data.get('restart_interval', '10'))
                self.full_quantity_var.set(config_data.get('full_quantity', False))
                self.auto_restart_var.set(config_data.get('auto_restart', True))
                # self.is_gun_var.set(config_data.get('is_gun', False)) # 枪械选项不读取，防止用户误勾选
                self.exchangeable_var.set(config_data.get('exchangeable', True))
                self.use_1k_backup_var.set(config_data.get('use_1k_backup', False))
        else:
            # 如果没有配置文件，设置默认值
            self.detect_time_entry.insert(0, '0.05')
            self.move_click_delay_entry.insert(0, '0.15')
            self.restart_interval_entry.insert(0, '10')

    def save_current_input(self):
        """保存当前输入到配置文件"""
        config_data = {
            'item_name': self.item_name_entry.get(),
            'price_threshold': self.price_high_entry.get(),
            'purchase_number': self.purchase_num_entry.get(),
            'start_hour': self.start_hour_entry.get(),
            'start_minute': self.start_minute_entry.get(),
            'detect_time': self.detect_time_entry.get(),
            'move_click_delay': self.move_click_delay_entry.get(),
            'restart_interval': self.restart_interval_entry.get(),
            'full_quantity': self.full_quantity_var.get(),
            'auto_restart': self.auto_restart_var.get(),
            # 'is_gun': self.is_gun_var.get() # 枪械选项不保存，防止用户误勾选
            'exchangeable': self.exchangeable_var.get(),
            'use_1k_backup': self.use_1k_backup_var.get()
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)

    def ultra_fast_click(self, position, pre_delay=0.0):
        time.sleep(pre_delay)
        win32api.SetCursorPos((position[0], position[1]))
        # 使用用户设置的鼠标点击延迟，如果没有设置或格式错误则使用默认值
        try:
            move_delay = float(self.move_click_delay_entry.get()) if self.move_click_delay_entry.get() else MOVE_CLICK_DELAY
        except ValueError:
            move_delay = MOVE_CLICK_DELAY
        time.sleep(move_delay)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0)

    def press_esc(self):
        # 按下ESC
        win32api.keybd_event(0x1B, 0, 0, 0)
        # 释放ESC
        win32api.keybd_event(0x1B, 0, win32con.KEYEVENTF_KEYUP, 0)

    def save_image_to_disk(self, image, price):
        """在子线程中保存图片到磁盘"""
        try:
            # 生成带时间戳的唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"ocr_debug_{timestamp}_{price}.png"
            file_path = os.path.join(DEBUG_IMAGE_DIR, filename)

            # 直接使用PIL的Image对象保存，明确指定格式避免encoderinfo错误
            image.save(file_path, format='PNG')
            logger.debug(f"截图已保存至: {file_path}")
        except Exception as e:
            logger.error(f"保存截图失败: {str(e)}", exc_info=True)
        if len(os.listdir(DEBUG_IMAGE_DIR)) > MAX_DEBUG_FILES:
            self.cleanup_old_files()

    def cleanup_old_files(self):
        """清理旧的调试图片文件，保留最新的 MAX_DEBUG_FILES 个文件"""

    try:
        # 获取所有调试图片文件，按修改时间排序（旧文件在前）
        files = glob.glob(os.path.join(DEBUG_IMAGE_DIR, "ocr_debug_*.png"))
        files.sort(key=os.path.getmtime)

        # 计算需要删除的文件数量
        num_files_to_delete = len(files) - MAX_DEBUG_FILES
        if num_files_to_delete > 0:
            logger.info(f"清理 {num_files_to_delete} 个旧调试文件...")

            # 删除最旧的N个文件
            for i in range(num_files_to_delete):
                os.remove(files[i])
                logger.debug(f"已删除旧文件: {files[i]}")

    except Exception as e:
        logger.error(f"清理旧文件时出错: {str(e)}", exc_info=True)

    def price_check(self, price, target_price, last_correct_price, ocr_fail_count):
        # 可以购买的条件 1、price有值且不是0  2、price小于target_price 3、price不小于last_correct_price的0.5倍
        if price:
            if price > last_correct_price * 0.5 or len(str(price)) == len(str(last_correct_price)):
                # 价格如果大于上次的一半，或，和上次位数相同，视为识别正确
                last_correct_price = price
                if price < target_price:
                    return True, ocr_fail_count, last_correct_price
                else:
                    logger.info(f"价格不低于设定值,不购买:{price}")
                    return False, ocr_fail_count, last_correct_price
            else:
                logger.error(f"价格过低，触发误购保护:{price}")
                return False, ocr_fail_count, last_correct_price
        else:
            logger.error("ocr识别错误，或退出了交易行页面")
            ocr_fail_count += 1
            return False, ocr_fail_count, last_correct_price

    def price_check_unsafe(self, price, high_price, low_price, last_correct_price, ocr_fail_count):
        # 可以购买的条件 price在high_price和low_price之间
        if price:
            if price < high_price and price > low_price:
                return True, ocr_fail_count, last_correct_price
            else:
                logger.info(f"价格不在区间{low_price}到{high_price}内，不购买：{price}")
                return False, ocr_fail_count, last_correct_price
        else:
            logger.error("ocr识别错误，或退出了交易行页面")
            ocr_fail_count += 1
            return False, ocr_fail_count, last_correct_price

    def pre_capture(self):
        logger.info("前五次只刷新不购买，用于识别校验")
        # 创建价格数组存储五次price的结果
        price_results = []

        # 识别物品右下角的价格,添加到数组
        price = self.get_price_ocr(self.click_positions['item_price'], float(self.price_high_entry.get()),
                                   self.user_delay_time(PURCHASE_CAP_DELAY))
        logger.info(f"检测到物品右下角价格：{price}")
        if price is not None:  # 确保price不是None再添加
            price_results.append(price)
        time.sleep(0.1)

        # 进行五次识别并存储到数组
        for i in range(5):
            if self.running == False:
                break
            # ESC
            # 模拟点击物品位置
            self.ultra_fast_click(self.click_positions['item'])
            time.sleep(0.1)
            # 截图并进行价格识别
            price = self.get_price_ocr(self.get_price_area(), float(self.price_high_entry.get()),
                                       self.user_delay_time(PURCHASE_CAP_DELAY))
            logger.info(f"第{i + 1}次刷新检测到价格：{price}")
            # 将识别到的价格添加到结果数组中
            if price is not None:  # 确保price不是None再添加
                price_results.append(price)
            # ESC
            self.press_esc()
            time.sleep(0.1)

        if not price_results:  # 如果没有识别到任何价格
            logger.warning("前5次价格识别均失败，尝试点击市场重试")
            # 点击市场按钮重试，而不是直接停止
            for retry in range(3):
                self.ultra_fast_click(self.click_positions['market'])
                time.sleep(0.1)
            logger.info("已点击市场重试，继续运行程序")
            return 9999999999  # 返回一个默认价格继续运行

        # 取所有出现过的最大价格作为正确识别参考价
        current_price = max(price_results)

        logger.debug(f"检测到正常市场价为：{current_price}")
        return current_price

    def toggle_price_low(self, *args):
        """根据误购保护状态切换价格下限输入可用性"""
        if self.close_anti_cheat_var.get():
            self.price_low_entry.config(state=tk.NORMAL)
            self.price_low_entry.delete(0, tk.END)  # 可选：清空原有输入
            self.price_low_entry.insert(0, "0")  # 可选：设置默认值
        else:
            self.price_low_entry.config(state=tk.DISABLED)
            self.price_low_entry.delete(0, tk.END)  # 可选：自动清空

    def on_anti_cheat_toggle(self, *args):
        """误购保护状态变更时的综合处理"""
        self.toggle_price_low()
        # 可以添加其他关联操作，例如：
        if self.close_anti_cheat_var.get():
            logger.warning("已关闭误购保护")
            messagebox.showwarning("已关闭误购保护",
                                   "将可能买到识别错误的商品，请勿用于购买高价物品。\n\n 请自行判断物品价格不可能低于多少，填写购买下限，可一定程度避免误购")

    def user_delay_time(self, default_delay):
        if len(self.detect_time_entry.get()):
            return max(0, float(self.detect_time_entry.get()) + default_delay)
        else:
            return default_delay
    
    def find_image_on_screen(self, template_path, threshold=0.6):
        """在屏幕上查找指定图片的位置，支持多分辨率自适应识别"""
        try:
            # 截取屏幕
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # 读取模板图片
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"无法读取模板图片: {template_path}")
                return None
            
            # 获取当前屏幕分辨率
            screen_width = screenshot.width
            screen_height = screenshot.height
            logger.debug(f"当前屏幕分辨率: {screen_width}x{screen_height}")
            
            # 定义多个缩放比例进行匹配（基于2K分辨率的模板图片）
            # 2K基准分辨率为2560x1440
            base_width, base_height = 2560, 1440
            
            # 计算当前分辨率相对于2K的缩放比例
            scale_x = screen_width / base_width
            scale_y = screen_height / base_height
            base_scale = min(scale_x, scale_y)  # 使用较小的缩放比例保持比例
            
            # 尝试多个缩放比例进行匹配
            scales = [base_scale, base_scale * 0.9, base_scale * 1.1, base_scale * 0.8, base_scale * 1.2]
            
            best_match = None
            best_confidence = 0
            best_scale = 1.0
            
            for scale in scales:
                if scale <= 0:
                    continue
                    
                # 缩放模板图片
                template_height, template_width = template.shape[:2]
                new_width = int(template_width * scale)
                new_height = int(template_height * scale)
                
                if new_width <= 0 or new_height <= 0:
                    continue
                    
                scaled_template = cv2.resize(template, (new_width, new_height))
                
                # 模板匹配
                result = cv2.matchTemplate(screenshot_cv, scaled_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                logger.debug(f"缩放比例 {scale:.3f}，匹配度: {max_val:.3f}")
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_match = max_loc
                    best_scale = scale
                    best_template_size = (new_width, new_height)
            
            if best_confidence >= threshold:
                # 计算匹配区域的中心点
                center_x = best_match[0] + best_template_size[0] // 2
                center_y = best_match[1] + best_template_size[1] // 2
                logger.info(f"找到图片 {template_path}，最佳匹配度: {best_confidence:.3f}，缩放比例: {best_scale:.3f}，位置: ({center_x}, {center_y})")
                return (center_x, center_y)
            else:
                logger.debug(f"未找到图片 {template_path}，最高匹配度: {best_confidence:.3f}")
                return None
        except Exception as e:
            logger.error(f"图像识别出错: {str(e)}", exc_info=True)
            return None
    
    def auto_restart_purchase(self):
        """自动重启抢购流程"""
        try:
            logger.info("开始执行自动重启抢购流程")
            
            # 保存当前物品名称
            current_item_name = self.item_name_entry.get()
            logger.info(f"保存当前物品名称: {current_item_name}")
            
            # 停止当前抢购
            self.running = False
            time.sleep(1)
            
            # 按ESC直到出现全面战场图片
            logger.info("寻找全面战场界面...")
            max_attempts = 10
            for attempt in range(max_attempts) :
                # 按ESC键
                pyautogui.press('escape')
                time.sleep(1)
                
                # 查找全面战场图片
                quanmian_pos = self.find_image_on_screen(get_resource_path("image/quanmianzhanchang.png"))
                if quanmian_pos:
                    logger.info(f"找到全面战场，点击位置: {quanmian_pos}")
                    self.ultra_fast_click(quanmian_pos,self.user_delay_time(ITEM_200_BUTTON_DELAY))
                    time.sleep(1)
                    break
                
                if attempt == max_attempts - 1:
                    logger.warning("未能找到全面战场界面")
                    return False
            
            # 按ESC直到出现烽火地带图片
            logger.info("寻找烽火地带界面...")
            for attempt in range(max_attempts):
                # 按ESC键
                pyautogui.press('escape')
                time.sleep(1)
                
                # 查找烽火地带图片
                fenghuodidai_pos = self.find_image_on_screen(get_resource_path("image/fenghuodidai.png"))
                if fenghuodidai_pos:
                    logger.info(f"找到烽火地带，点击位置: {fenghuodidai_pos}")
                    self.ultra_fast_click(fenghuodidai_pos,self.user_delay_time(ITEM_200_BUTTON_DELAY))
                    time.sleep(1)
                    break
                
                if attempt == max_attempts - 1:
                    logger.warning("未能找到烽火地带界面")
                    return False
            
            # 点击market位置
            logger.info("点击market位置...")
            market_pos = self.get_market_button_pos()
            if market_pos:
                self.ultra_fast_click(market_pos,self.user_delay_time(ITEM_200_BUTTON_DELAY))
                time.sleep(1)
                logger.info("已点击market")
            else:
                logger.warning("未能获取market位置")
                return False
            
            # 重新输入物品名称
            if current_item_name:
                logger.info(f"重新输入物品名称: {current_item_name}")
                # 点击输入框
                self.ultra_fast_click(self.click_positions['input_field'])
                time.sleep(0.1)
                # 清空输入框
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                time.sleep(0.01)
                # 模拟键盘输入物品名称
                self.typewrite(current_item_name)
                time.sleep(0.5)
            
            # 重新开启抢购
            logger.info("重新开启抢购...")
            self.running = True
            time.sleep(1)
            
            logger.info("自动重启抢购流程完成")
            return True
            
        except Exception as e:
            logger.error(f"自动重启抢购流程出错: {str(e)}", exc_info=True)
            return False

    def get_200_button_pos(self):
        # 根据可兑换按钮是否勾选，切换不同的点击位置
        if self.exchangeable_var.get():
            return self.click_positions['200_button_s4_exchangeable']
        else:
            return self.click_positions['200_button']

    def get_buy_button_pos(self):
        # 根据可兑换按钮是否勾选，切换不同的点击位置
        if self.exchangeable_var.get():
            return self.click_positions['buy_button_s4_exchangeable']
        else:
            return self.click_positions['buy_button']

    def get_price_area(self):
        # 根据可兑换按钮是否勾选，切换不同的点击位置
        if self.exchangeable_var.get():
            return self.click_positions['price_area_s4_exchangeable']
        else:
            return self.click_positions['price_area']
    
    def get_market_button_pos(self):
        """获取market按钮位置"""
        return self.click_positions['market']

    def update_ui_log(self, message):
        """更新UI中的日志显示"""
        try:
            # 直接使用logger输出，因为已经配置了UI日志处理器
            logger.info(message)
        except Exception as e:
            logger.error(f"更新UI日志失败: {str(e)}")
    
    def run(self):
        self.root.mainloop()


# Example usage
if __name__ == "__main__":
        bot = DeltaLootBot()
        bot.run()

