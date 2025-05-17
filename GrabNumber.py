# -*- coding: utf-8 -*-
# @Time    : 2025/4/29  17:03
# @Author  : TT
# @FileName: ChangeNumber.py
# @Software: PyCharm
"""
    文件描述:
"""
import aiohttp
import asyncio
import json
import time
from loguru import logger
import ParseXml as p
import WechatCode
import sm
import ua
import sys
from datetime import datetime
import requests

# logger.remove()
# logger.add(sys.stdout,level="INFO",enqueue=True,backtrace=False,diagnose=False)
logger.add(
    "抢号成功记录.log",
    level="INFO",
    mode="w",
    enqueue=True,
    backtrace=False,
    diagnose=False,
    rotation="10 MB",
    retention=3,
    encoding="utf-8",
)
class AsyncXhyy:

    def __init__(self,proxies):
        self.headers = {
            "Content-Type": "application/json",
            "Referer": "https://servicewechat.com/wx7878e855bec324c1/15/page-frame.html",
            "User-Agent": ua.get_ua(),
            "xweb_xhr": "1"
        }
        self.proxies = proxies or None
        self.session = None
        self.token = None
        self.app_id = None
        self.authToken = None
        self.write = p.UniqueFileWriter()
        with open('患者信息.txt', 'r', encoding='utf-8') as f:
            self.patient_list = [eval(x.strip()) for x in f.readlines()]

    async def init_session(self):
        connector = aiohttp.TCPConnector(
            ssl=False,
            limit_per_host=100,
            limit=500,
        )
        self.session = aiohttp.ClientSession(connector=connector)

    async def close_session(self):
        await self.session.close()

    async def send_requests(self, url, data, params=None):
        while True:
            try:
                start = datetime.now()
                async with self.session.post(url, headers=self.headers, params=params, json=data,proxy = self.proxies) as response:
                    print(datetime.now()-start)
                    return await response.json()
            except Exception as e:
                logger.error(e)
                continue
    def judge(self, data, source_name, reservation, patient_name):
        try:
            result = data['data']['data']['data']
            if '成功' in result:
                logger.success(f"[{source_name}][{patient_name}]已抢到→→{reservation['scheduleDate']}→→{reservation['doctorName']}医生的号，挂号费:{reservation['feeSum']}元，请尽快前往支付......")
                # self.write.write(f"[{source_name}][{patient_name}]已抢到→→{reservation['doctorName']}医生的号")
                return 'success'
            logger.error(f"[{source_name}][{patient_name}][{reservation['doctorName']}]{result}")
            return 'fail'
        except KeyError:
            return 'except'

    async def login(self, code):
        url = "https://wxxcx.pumch.cn/hf-hospital/wechatMini/wechatLogin"
        data = {
            "appId": "wx7878e855bec324c1",
            "code": code,
            "terminalId": "wx_mini_client",
            "deviceId": "17433940584045534318",
            "deviceModel": "microsoft"
        }
        resp = await self.send_requests(url, data)
        if resp.get('code') == 20000:
            return resp['data']
        logger.error('登录失败')
        return None

    async def request_interface(self, body, method):
        url = "https://wxxcx.pumch.cn/dhccam-ih/gateway/index"
        params = {"method": method}
        timestamp = int((time.time() * 1000))
        sign = sm.sign(self.app_id, body, method, timestamp, self.token)
        biz_content = sm.encrypt_biz(body)
        data = {
            "method": method,
            "app_id": self.app_id,
            "token_type": "api_credentials",
            "nonce_str": timestamp,
            "version": "v1.0",
            "token": self.token,
            "biz_content": biz_content,
            "sign": sign
        }
        resp = await self.send_requests(url, data, params)
        decrypt_data = sm.decrypt_data(resp['data'])
        try:
            return json.loads(decrypt_data)
        except:
            return decrypt_data

    async def search_doctor(self, doctor_name, doctor_numb):
        body = {"requestXML": f"<Request><terminalId>wx_mini_client</terminalId><keyWord>{doctor_name}</keyWord><hospitalId/></Request>"}
        data = await self.request_interface(body, "patient.opregister.SearchLocOrDoctor.ih")
        try:
            return p.get_doctor_codes(data)[int(doctor_numb) - 1]
        except:
            logger.error('医生编号输入错误')
            return None

    async def get_all_department_info(self, doctorCode, regNo, menzhen_name):
        Get_Doctor_Info_requestXML = {
            "requestXML": f"<Request><terminalId>wx_mini_client</terminalId><regNo>{regNo}</regNo><departmentCode/><doctorCode>{doctorCode}</doctorCode></Request>"
        }
        data = await self.request_interface( Get_Doctor_Info_requestXML,'patient.opregister.GetDoctorCenterInfo.ih')
        department_info = p.extract_department_info(data)
        target = menzhen_name.split('-')
        if not department_info:
            logger.error('未查询到医生门诊信息')
            return None
        for info in department_info:
            if info['departmentName'] == target[0] and info['clinicGroupName'] == target[1]:
                return info

    async def get_alldate_and_scheduleToken(self, department_info, doctorCode, date, time_slot):
        Go_Homepage_RequestXML = {
            "requestXML": f"<Request><terminalId>wx_mini_client</terminalId><departmentCode>{department_info['departmentId']}</departmentCode><clinicGroupId>{department_info['clinicGroupId']}</clinicGroupId><doctorCode>{doctorCode}</doctorCode><visitType>N</visitType></Request>"
        }
        data = await self.request_interface(Go_Homepage_RequestXML, "patient.opregister.getdoctorschedule")
        schedules = p.parse_schedules(data) if data else None
        if not schedules:
            return None
        for sched in schedules:
            if time_slot:
                if sched['scheduleDate'] == date and sched['sessionName'] == time_slot:
                    return sched
            else:
                if sched['scheduleDate'] == date:
                    return sched

    async def lock_number(self, regNo, reservation,source_name, doctor_name, time_slot, patient_name):
        Lock_Body = {
            "body": {
                "apiCode": "patient.opregister.lockorder.ih",
                "apiVersion": "v2.0",
                "force": 0,
                "data": {
                    "requestXML": f"<Request><terminalId>wx_mini_client</terminalId><authToken>{self.authToken}</authToken><regNo>{regNo}</regNo><scheduleCode>{reservation['scheduleCode']}</scheduleCode><scheduleDate>{reservation['scheduleDate']}</scheduleDate><scheduleToken>{reservation['scheduleToken']}</scheduleToken><force>0</force></Request>"
                }
            }
        }
        data = await self.request_interface(Lock_Body, "gateway.message-queue.api-queuing")
        if data.get('msg') != '请求成功':
            logger.error(f"[{source_name}][{patient_name}][{doctor_name}][{time_slot}]{data.get('msg')}")
            return 'fail'
        return self.judge(data, source_name, reservation, patient_name)

    async def process_patient(self,reservation, doctor_name, time_slot, patient_info):
        while True:
            source_name,regNo, patient_name = patient_info[0],patient_info[1],patient_info[2]
            result = await self.lock_number(regNo, reservation,source_name, doctor_name, time_slot, patient_name)
            if result == 'success':
                return result

    async def run(self, doctor_name, doctor_numb, code, date, menzhen_name, time_slot):
        login_res = await self.login(code)
        self.token,self.app_id,self.authToken = login_res['dhccamToken']['access_token'],login_res['dhccamAppId'],login_res['authToken']
        doctorCode = await self.search_doctor(doctor_name, doctor_numb)
        department_info = await self.get_all_department_info(doctorCode,login_res['regNo'],menzhen_name)
        reservation = await self.get_alldate_and_scheduleToken(department_info,doctorCode,date, time_slot)
        logger.info(f"[{doctor_name}][{time_slot}]检测出号余量：{int(reservation['availableNum'])}张")
        # self.patient_list *= 3
        tasks = [self.process_patient(reservation, doctor_name, time_slot, p) for p in self.patient_list]
        await asyncio.gather(*tasks)

    async def main(self, info):
        await self.init_session()
        try:
            await self.run(info[2], info[6], info[1], info[3], info[4], info[5])
        finally:
            await self.close_session()

if __name__ == '__main__':
    # open('抢号成功记录.txt','w').close()
    xhyy = AsyncXhyy(proxies = None)
    with open('手动输入医生信息.txt', 'r', encoding='utf-8') as f:
        info_list = f.readlines()
    # code_list = WechatCode.get_code()
    code_list = requests.get('https://10731pvte2806.vicp.fun/run').json()['data']
    if not code_list or not code_list[0]:
        logger.error('微信code获取失败')
    info_list = [eval(x.strip()) for x in info_list]
    all_info = code_list+info_list[0]
    print(all_info)
    asyncio.run(xhyy.main(all_info))