"""
CrazyAgentsManage WebUI Application
"""

import os
from flask import Flask, render_template, request, Response
from api import api

app = Flask(__name__)
app.register_blueprint(api)

BASE_PATH = os.environ.get('APP_BASE_PATH', '')


@app.context_processor
def inject_base():
    return {'BASE': BASE_PATH}


@app.after_request
def inject_base_script(response: Response):
    if response.content_type and 'text/html' in response.content_type:
        script = f'<script>window.APP_BASE="{BASE_PATH}";</script>'
        content = response.get_data(as_text=True)
        if '</head>' in content:
            content = content.replace('</head>', script + '</head>')
            response.set_data(content)
    return response


@app.route('/')
def index():
    """主页 - 团队与角色（总入口页面）"""
    return render_template('home.html')


@app.route('/agent')
def agent():
    """智能体管理页面"""
    return render_template('agent.html')


@app.route('/graph')
def graph():
    """知识图谱页面"""
    return render_template('graph.html')


@app.route('/alerts')
def alerts():
    """系统告警页面"""
    return render_template('alerts.html')


@app.route('/tokens')
def tokens():
    """Token管理页面"""
    return render_template('tokens.html')


@app.route('/sessions')
def sessions():
    """会话流水线索引"""
    return render_template('sessions.html')


@app.route('/dashboard')
def dashboard():
    """智能体监控仪表板"""
    return render_template('dashboard.html')


@app.route('/tasks')
def tasks():
    """任务编排"""
    return render_template('tasks.html')


@app.route('/team-memory')
def team_memory():
    """团队记忆管理"""
    return render_template('team-memory.html')


@app.route('/cron')
def cron():
    """定时任务管理"""
    return render_template('cron.html')


@app.route('/skills')
def skills():
    """技能中心"""
    return render_template('skills.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
