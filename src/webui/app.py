"""CrazyAgentsManage WebUI Application."""

from flask import Flask, render_template, send_from_directory, request
from api import api
import os

static_folder = os.path.join(os.path.dirname(__file__), 'static')
app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
app.register_blueprint(api)
app.register_blueprint(api, url_prefix='/manage/api', name='manage_api')


# Serve static files at /manage/static/ for nginx compatibility
@app.route('/manage/static/<path:filename>')
def serve_manage_static(filename):
    return send_from_directory(static_folder, filename)


# Determine BASE path: prefer explicit proxy/base configuration, otherwise
# fall back to the direct-access path shape.
@app.context_processor
def inject_base():
    configured_base = os.environ.get('APP_BASE_PATH', '').rstrip('/')
    forwarded_prefix = request.headers.get('X-Forwarded-Prefix', '').rstrip('/')

    if forwarded_prefix:
        return {'BASE': forwarded_prefix}

    if request.path.startswith('/manage'):
        return {'BASE': '/manage'}

    if configured_base:
        return {'BASE': configured_base}

    return {'BASE': ''}


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


@app.route('/timeline')
def timeline():
    return render_template('timeline.html', active_nav='operations')


@app.route('/skills')
def skills():
    return render_template('skills.html')


@app.route('/overview')
def overview():
    return render_template('overview.html')


@app.route('/runtime')
def runtime():
    return render_template('runtime.html')


@app.route('/runtime/sessions')
def runtime_sessions():
    return render_template('sessions.html')


@app.route('/runtime/dashboard')
def runtime_dashboard():
    return render_template('dashboard.html')


@app.route('/runtime/tokens')
def runtime_tokens():
    return render_template('tokens.html')


@app.route('/runtime/agents')
def runtime_agents():
    return render_template('agent.html')


@app.route('/operations')
def operations():
    return render_template('operations.html')


@app.route('/operations/skills')
def operations_skills():
    return render_template('skills.html')


@app.route('/operations/cron')
def operations_cron():
    return render_template('cron.html')


@app.route('/operations/team-memory')
def operations_team_memory():
    return render_template('team-memory.html')


@app.route('/operations/timeline')
def operations_timeline():
    return render_template('timeline.html', active_nav='operations')


@app.route('/operations/alerts')
def operations_alerts():
    return render_template('alerts.html')


@app.route('/governance')
def governance():
    return render_template('governance.html')


@app.route('/governance/graph')
def governance_graph():
    return render_template('graph.html')


@app.route('/collaboration')
def collaboration():
    return render_template('collaboration.html')


@app.route('/collaboration/loops')
def collaboration_loops():
    return render_template('loop-surface.html')


@app.route('/collaboration/tasks')
def collaboration_tasks():
    return render_template('tasks.html')


@app.route('/architecture/philosophy')
def architecture_philosophy():
    return render_template('architecture-philosophy.html')


@app.route('/architecture/product')
def architecture_product():
    return render_template('architecture-product.html')


@app.route('/architecture/tech')
def architecture_tech():
    return render_template('architecture-tech.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5002)
