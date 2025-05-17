# -*- coding: utf-8 -*-
# @Time    : 2025/4/10  22:21
# @Author  : TT
# @FileName: ParseXml.py
# @Software: PyCharm
"""
    文件描述:
       
"""

from bs4 import BeautifulSoup
import os
def parse_schedules(xml_content):
    soup = BeautifulSoup(xml_content, 'xml')
    schedules = soup.find_all('Schedule')
    result_list = []
    for schedule in schedules:
        # 提取各字段内容并去除空白
        schedule_code = schedule.find('scheduleCode').text.strip()
        schedule_date = schedule.find('scheduleDate').text.strip()
        department_name = schedule.find('departmentName').text.strip()
        session_name = schedule.find('sessionName').text.strip()
        available_num = schedule.find('availableNum').text.strip()
        fee_sum = schedule.find('feeSum').text.strip()
        clinic_group_name = schedule.find('clinicGroupName').text.strip()
        schedule_token = schedule.find('scheduleToken').text.strip()
        doctor_name = schedule.find('doctorName').text.strip()

        # 构建字典并添加到结果列表
        schedule_dict = {
            'scheduleCode': schedule_code,
            'scheduleDate': schedule_date,
            'departmentName': department_name,
            'sessionName': session_name,
            'availableNum': available_num,
            'feeSum': fee_sum,
            'clinicGroupName': clinic_group_name,
            'scheduleToken': schedule_token,
            'doctorName': doctor_name
        }
        result_list.append(schedule_dict)
    return result_list

def extract_department_info(xml_data):
    soup = BeautifulSoup(xml_data, 'xml')
    items = soup.find_all('Item')
    result = []
    for item in items:
        data = {
            'departmentId': item.find('departmentId').get_text(strip=True) if item.find('departmentId') else '',
            'departmentName': item.find('departmentName').get_text(strip=True) if item.find('departmentName') else '',
            'clinicGroupName': item.find('clinicGroupName').get_text(strip=True) if item.find('clinicGroupName') else '',
            'clinicGroupId': item.find('clinicGroupId').get_text(strip=True) if item.find('clinicGroupId') else ''
        }
        result.append(data)
    return result

def get_doctor_codes(xml_content: str) -> list:
    soup = BeautifulSoup(xml_content, 'xml')
    codes = [code.get_text(strip=True) for code in soup.find_all('doctorCode')]
    return codes

# def merge_lists(code_list, info_list):
#     '''
#     :param code_list: code列表
#     :param info_list: 医生信息
#     :return: 合并后的信息
#     '''
#     if len(code_list) == len(info_list):
#         # 长度相同直接一对一
#         for i in code_list:
#             i.extend(info_list[code_list.index(i)])
#     else:
#         if len(code_list) == 5 and len(info_list) == 1:
#             for sublist in code_list[:5]:
#                 sublist.extend(info_list[0])
#         elif len(code_list) == 10 and len(info_list) == 2:
#             for sublist in code_list[:5]:
#                 sublist.extend(info_list[0])
#                 # 将info_list的第二个子列表添加到code_list的后5个子列表中
#             for sublist in code_list[5:10]:  # 确保只处理到第10个元素（索引5-9）
#                 sublist.extend(info_list[1])
#         else:
#             logger.error('微信数量与医生信息数量不一致')
#     return code_list

# def get_patient_list(data):
#     card_list = data['data']['cardList']
#     result = []
#     for card in card_list:
#         reg_no = card.get('reg_no', '')
#         patient_name = card.get('patient_name', '')
#         result.append([reg_no, patient_name])
#     return result


class UniqueFileWriter:
    def __init__(self, encoding='utf-8'):
        self.encoding = encoding
        self.seen = set()
        if os.path.exists('抢号成功记录.txt'):
            with open('抢号成功记录.txt', 'r', encoding=self.encoding) as f:
                for line in f:
                    self.seen.add(line.rstrip('\n'))

    def write(self, s: str):
        ln = s.rstrip('\n')
        if ln in self.seen:
            return False
        with open('抢号成功记录.txt', 'a', encoding=self.encoding) as f:
            f.write(ln + '\n')
        self.seen.add(ln)
        return True



