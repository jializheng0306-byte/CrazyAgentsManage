"""
CrazyAgentsManage WebUI Application
"""

from flask import Flask, render_template, url_for
from api import api

app = Flask(__name__, static_url_path='/manage/static')
app.config['APPLICATION_ROOT'] = '/manage'
app.register_blueprint(api)


@app.context_processor
def inject_base():
    return {'BASE': '/manage'}


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/agent')
def agent():
    return render_template('agent.html')


@app.route('/graph')
def graph():
    return render_template('graph.html')


@app.route('/alerts')
def alerts():
    return render_template('alerts.html')


@app.route('/tokens')
def tokens():
    return render_template('tokens.html')


@app.route('/sessions')
def sessions():
    return render_template('sessions.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/tasks')
def tasks():
    return render_template('tasks.html')


@app.route('/team-memory')
def team_memory():
    return render_template('team-memory.html')


@app.route('/cron')
def cron():
    return render_template('cron.html')


@app.route('/skills')
def skills():
    return render_template('skills.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5002)
