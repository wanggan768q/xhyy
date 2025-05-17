# -*- coding: utf-8 -*-
# @Time    : 2025/4/19  18:00
# @Author  : TT
# @FileName: http.py
# @Software: PyCharm
"""
    文件描述:
       
"""
from flask import Flask, jsonify
import WechatCode

app = Flask(__name__)

@app.route('/run', methods=['GET'])
def run_python_script():
    try:
        code = getCode.get_code()
        return jsonify({"status": "success", "data": code})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6666)