import os
os.environ["DEEPSEEK_API_KEY"] = "sk-532acbc85a2941858bcb1622a8f39860"

import sys
import threading
import queue
import logging
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 导入新主流程和智能体
from deepseek_finrobot.agents.main import run_trading_cycle
from deepseek_finrobot.agents.my_agents import ExpectAdjustmentAgent
from deepseek_finrobot.utils import get_current_date

# Flask应用
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'templates'),
    static_folder=os.path.join(project_root, 'static')
)

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局变量
analysis_results = {}
analysis_queue = queue.Queue()
current_portfolio = {}
collected_data = {}
current_progress = {"step": "", "progress": 0, "total": 5}
conversation_log = []  # 全局对话内容

print("DEEPSEEK_API_KEY in app.py:", os.environ.get("DEEPSEEK_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        stock_input = request.form.get('stock_codes', '').strip()
        if not stock_input:
            return jsonify({"error": "请输入有效的股票代码"})
        stock_codes = [code.strip() for code in stock_input.split(',') if code.strip()]
        if not stock_codes:
            return jsonify({"error": "请输入有效的股票代码"})

        # 可扩展：前端可传递风险偏好、投资期限参数
        risk_preference = request.form.get('risk_preference', '中等')
        investment_horizon = request.form.get('investment_horizon', '长期')

        # 启动分析线程
        def run_analysis_thread():
            global current_progress
            current_progress = {"step": "", "progress": 0, "total": 5}
            global conversation_log
            conversation_log.clear()
            def log_callback(msg):
                if isinstance(msg, str):
                    conversation_log.append({"role": "agent", "content": msg})
                elif isinstance(msg, dict):
                    conversation_log.append(msg)
                else:
                    conversation_log.append({"role": "agent", "content": str(msg)})
            def progress_callback(step_name):
                global current_progress
                current_progress["step"] = step_name
                current_progress["progress"] += 1
            logger.info(f"分析任务启动，股票代码: {stock_codes}")
            try:
                result = run_trading_cycle(
                    stock_codes,
                    risk_preference=risk_preference,
                    investment_horizon=investment_horizon,
                    progress_callback=progress_callback,
                    log_callback=log_callback
                )
                analysis_results['result'] = result
                # 保存当前投资组合和数据
                global current_portfolio, collected_data
                if result.get('current_portfolio'):
                    current_portfolio = result['current_portfolio']
                if result.get('analyzed_stocks') and result.get('analysis_reports'):
                    collected_data = {code: {} for code in result['analyzed_stocks']}
                # 生成投资组合分析报告
                if current_portfolio:
                    agent = ExpectAdjustmentAgent({})
                    report = agent.dynamic_portfolio_adjustment(current_portfolio, collected_data, log_callback=log_callback)
                    filename = f"{'_'.join(stock_codes)}_dynamic_portfolio.txt"
                    output_dir = os.path.join(project_root, "portfolio")
                    os.makedirs(output_dir, exist_ok=True)
                    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                        f.write(report)
                analysis_queue.put(result)
            except Exception as e:
                logger.error(f"分析线程异常: {e}", exc_info=True)
                analysis_queue.put({"success": False, "message": str(e)})

        thread = threading.Thread(target=run_analysis_thread)
        thread.daemon = True
        thread.start()
        return jsonify({"status": "processing"})
    except Exception as e:
        logger.error(f"/analyze 路由异常: {e}", exc_info=True)
        return jsonify({"error": f"服务器内部错误: {str(e)}"})

@app.route('/check_status')
def check_status():
    try:
        result = analysis_queue.get_nowait()
        return jsonify(result)
    except queue.Empty:
        return jsonify({"status": "processing", "progress": current_progress})

@app.route('/download/portfolio/<symbol>')
def download_portfolio(symbol):
    filename = f"{symbol}_dynamic_portfolio.txt"
    directory = os.path.join(project_root, "portfolio")
    file_path = os.path.join(directory, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return f"File not found: {filename}", 404

@app.route('/download_file')
def download_file():
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404
    filename = os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    # 确保必要的目录存在
    os.makedirs(os.path.join(project_root, 'portfolio'), exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True) 