# -*- coding: utf-8 -*-
# @Time    : 2025/4/3  23:45
# @Author  : TT
# @FileName: WechatCode.py
# @Software: PyCharm
"""
    文件描述:
"""

import requests
import json
import re
import psutil

def get_all_processes():
    pid = ''
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            process_info = proc.info
            if process_info['name'] == 'WeChat.exe':
                pid=process_info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 处理进程已结束、权限不足或僵尸进程的情况
            pass
    return pid

def get_code():
    pid = get_all_processes()
    code_dict = []
    # for pid in all_pid:
    try:
        url = f'http://127.0.0.1:{pid+1}/mili'
        data = {"事件类型":"小程序取参数","appid":"wx7878e855bec324c1"}
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-16')
        res = requests.post(url,data=json_data)
        res.encoding='utf-16'
        code = re.search(r'(?<="code\\":\\")(.+?)(?=\\",\\"err_msg\\")',res.text).group()
        name = re.search(r'(?<=来源昵称\[)(.+?)(?=\])',res.text).group()
        code_dict= [name,code]
    except Exception as e:
        print(e)
    return code_dict
