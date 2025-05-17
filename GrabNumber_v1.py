import asyncio
import aiofiles
import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from logging import Logger
import json
import time
from typing import List, Tuple

logger = Logger(name="optimized_grabber")

class AsyncXhyy:
    def __init__(self, max_concurrency: int = 20, proxies=None):
        # 连接池配置
        self.connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=20,
            ssl=False
        )
        self.timeout = aiohttp.ClientTimeout(total=10)
        self.proxies = proxies
        
        # 动态并发控制
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.success_count = 0
        self.total_attempts = 0
        self.last_adjust = time.time()
        
        # 认证缓存
        self.token = None
        self.token_expiry = 0

    async def __aenter__(self):
        await self.init_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close_session()

    async def init_session(self):
        """初始化连接会话"""
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout
        )

    async def close_session(self):
        """优雅关闭连接"""
        if not self.session.closed:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def lock_number(self, regNo, reservation, source_name, doctor_name, time_slot, patient_name):
        """带重试机制的锁号操作"""
        url = "https://api.example.com/lock"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            async with self.session.post(
                url,
                json={
                    "regNo": regNo,
                    "scheduleToken": reservation['scheduleToken'],
                    "patientInfo": patient_name
                },
                headers=headers
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                self.total_attempts += 1
                if data.get('status') == 'success':
                    self.success_count += 1
                    await self.log_success(patient_name)
                    return 'success'
                return 'retry'
        except Exception as e:
            logger.error(f"锁号异常: {str(e)}")
            raise

    async def dynamic_concurrency_adjust(self):
        """动态调整并发量"""
        if time.time() - self.last_adjust > 30:  # 每30秒调整
            success_rate = self.success_count / max(1, self.total_attempts)
            
            if success_rate > 0.8:
                new_limit = min(self.semaphore._value + 5, 50)
            elif success_rate < 0.3:
                new_limit = max(self.semaphore._value - 5, 5)
            else:
                return
                
            logger.info(f"调整并发数: {self.semaphore._value} -> {new_limit}")
            self.semaphore = asyncio.Semaphore(new_limit)
            self.last_adjust = time.time()
            self.success_count = 0
            self.total_attempts = 0

    async def process_patient(self, reservation, doctor_name, time_slot, patient_info: Tuple):
        """处理单个患者挂号流程"""
        async with self.semaphore:  # 并发控制
            source_name, regNo, patient_name = patient_info
            for _ in range(3):  # 有限重试
                result = await self.lock_number(
                    regNo, reservation, source_name,
                    doctor_name, time_slot, patient_name
                )
                if result == 'success':
                    return
                await asyncio.sleep(1.5**_)  # 指数退避
                
            logger.error(f"{patient_name} 挂号失败")
            await self.log_failure(patient_name)

    async def run(self, doctor_name: str, doctor_numb: str, code: str,
                 date: str, menzhen_name: str, time_slot: str):
        """核心运行流程"""
        # 带缓存的登录
        if not self.token or time.time() > self.token_expiry:
            login_res = await self.login(code)
            self.token = login_res['dhccamToken']['access_token']
            self.token_expiry = time.time() + 3600  # 1小时有效期

        # 医生信息查询
        doctor_code = await self.search_doctor(doctor_name, doctor_numb)
        department_info = await self.get_all_department_info(
            doctor_code, 
            login_res['regNo'],
            menzhen_name
        )
        
        # 号源查询
        reservation = await self.get_alldate_and_scheduleToken(
            department_info,
            doctor_code,
            date,
            time_slot
        )
        
        logger.info(f"[{doctor_name}][{time_slot}] 余量: {reservation['availableNum']}")
        
        # 创建并行任务
        tasks = [
            self.process_patient(reservation, doctor_name, time_slot, p)
            for p in self.patient_list
        ]
        
        # 动态调整并发
        adjust_task = asyncio.create_task(self.auto_adjust())
        await asyncio.gather(*tasks, adjust_task)

    async def auto_adjust(self):
        """后台自动调整并发"""
        while True:
            await self.dynamic_concurrency_adjust()
            await asyncio.sleep(5)

    async def main(self, info: List):
        """主入口"""
        async with self:
            try:
                await self.run(
                    info[2], info[6], info[1],
                    info[3], info[4], info[5]
                )
            except Exception as e:
                logger.critical(f"致命错误: {str(e)}")
                raise

    # 辅助方法
    async def log_success(self, patient_name: str):
        """异步记录成功"""
        async with aiofiles.open('抢号成功记录.txt', 'a') as f:
            await f.write(f"{time.ctime()} {patient_name}\n")

    async def log_failure(self, patient_name: str):
        """异步记录失败"""
        async with aiofiles.open('抢号失败记录.txt', 'a') as f:
            await f.write(f"{time.ctime()} {patient_name}\n")

if __name__ == '__main__':
    # 初始化日志文件
    async def init_files():
        async with aiofiles.open('抢号成功记录.txt', 'w') as f:
            await f.write('')
        async with aiofiles.open('抢号失败记录.txt', 'w') as f:
            await f.write('')

    asyncio.run(init_files())

    # 安全读取配置
    try:
        with open('手动输入医生信息.txt', 'r', encoding='utf-8') as f:
            info_list = [json.loads(line.strip()) for line in f]
    except json.JSONDecodeError as e:
        logger.error(f"配置文件解析错误: {str(e)}")
        exit(1)

    code_list = WechatCode.get_code()
    if not code_list:
        logger.error('微信授权码获取失败')
        exit(1)

    # 运行主程序
    async def main_async():
        async with AsyncXhyy(max_concurrency=20) as xhyy:
            xhyy.patient_list = [...]  # 加载患者列表
            await xhyy.main(code_list + info_list[0])

    asyncio.run(main_async())
