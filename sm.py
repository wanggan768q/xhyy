# -*- coding: utf-8 -*-
# @Time    : 2025/5/4  13:18
# @Author  : TT
# @FileName: sm3.py
# @Software: PyCharm
"""
    文件描述:
       
"""
from gmssl import sm3, func
import json
import binascii
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT

_KEY_HEX = "437974505F33693338254A716D36524D"
_IV_HEX  = "30313032303330343035303630373038"

_key = binascii.unhexlify(_KEY_HEX)
_iv  = binascii.unhexlify(_IV_HEX)

def sign(app_id, body, method, nonce_str, token):
    # 构建基础参数字典
    F = {
        "method": method,
        "app_id": app_id,
        "token_type": "api_credentials",
        "nonce_str": nonce_str,
        "version": "v1.0",
        "token": token,
        "biz_content": body
    }

    # 复制非biz_content/files字段
    t = {}
    for key in F:
        if key not in ['biz_content', 'files']:
            t[key] = F[key]

    # 处理biz_content内容
    biz_content = F['biz_content']

    # 如果biz_content不是字典，尝试解析为字典
    if not isinstance(biz_content, dict):
        try:
            biz_content = json.loads(biz_content)
        except (TypeError, json.JSONDecodeError):
            # 如果解析失败，保持原样（根据实际情况处理）
            pass

    # 合并biz_content字段（处理对象类型值）
    if isinstance(biz_content, dict):
        for k, v in biz_content.items():
            if isinstance(v, (dict, list)):
                # 序列化并转义斜杠
                json_str = json.dumps(v, separators=(',', ':'), ensure_ascii=False)
                json_str = json_str.replace('/', '\\/')
                t[k] = json_str
            else:
                t[k] = v

    # 排序并拼接参数
    sorted_keys = sorted(t.keys())
    param_parts = []
    for key in sorted_keys:
        param_parts.append(f"{key}={t[key]}")
    param_str = '&'.join(param_parts)

    # 添加密钥
    sign_str = param_str + "3u*B)6r9YtSDzMb4"

    # SM3加密处理
    byte_data = sign_str.encode('utf-8')
    hash_list = func.bytes_to_list(byte_data)
    sm3_hash = sm3.sm3_hash(hash_list)
    encrypted_sign = sm3_hash.upper()

    return encrypted_sign

def encrypt_biz(body: dict) -> str:
    plain = json.dumps(body, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    cipher = CryptSM4()
    cipher.set_key(_key, SM4_ENCRYPT)
    encrypted = cipher.crypt_cbc(_iv, plain)
    return binascii.hexlify(encrypted).decode('utf-8').upper()

def decrypt_data(data_hex):
    encrypted = binascii.unhexlify(data_hex)
    cipher = CryptSM4()
    cipher.set_key(_key, SM4_DECRYPT)
    decrypted = cipher.crypt_cbc(_iv, encrypted)
    text = decrypted.decode('utf-8')
    return text

