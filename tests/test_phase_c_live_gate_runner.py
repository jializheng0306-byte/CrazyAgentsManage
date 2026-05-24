import importlib.util
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'runtime' / 'run_phase_c_collaboration_live_gate.py'
SPEC = importlib.util.spec_from_file_location('phase_c_live_gate_runner', MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_run_gate_sets_manage_base_and_output_dir(monkeypatch, tmp_path):
    captured = {}

    def fake_run(cmd, cwd, text, capture_output, env, check):
        captured['cmd'] = cmd
        captured['cwd'] = cwd
        captured['env'] = env
        return SimpleNamespace(returncode=0, stdout='ok', stderr='')

    monkeypatch.setattr(MODULE.subprocess, 'run', fake_run)

    result = MODULE.run_gate('http://127.0.0.1:58080/manage', tmp_path)

    assert result.returncode == 0
    assert captured['cmd'] == ['node', 'tests/phase_c_collaboration_live_gate_check.js']
    assert captured['cwd'] == MODULE.ROOT
    assert captured['env']['BASE_URL'] == 'http://127.0.0.1:58080/manage'
    assert captured['env']['OUTPUT_DIR'] == str(tmp_path)


def test_main_uses_tunnel_as_canonical_gate_and_public_probe_is_non_blocking(monkeypatch, tmp_path, capsys):
    calls = []

    def fake_start_tunnel(local_port, remote_port, remote_bind_host):
        calls.append(('start', local_port, remote_port, remote_bind_host))
        return object(), None

    def fake_stop_tunnel(proc, temp_script):
        calls.append(('stop', proc, temp_script))

    def fake_run_gate(base_url, output_dir):
        calls.append(('gate', base_url, output_dir))
        if '127.0.0.1' in base_url:
            return SimpleNamespace(returncode=0, stdout='tunnel ok', stderr='')
        return SimpleNamespace(returncode=1, stdout='public failed', stderr='public err')

    monkeypatch.setattr(MODULE, 'start_tunnel', fake_start_tunnel)
    monkeypatch.setattr(MODULE, 'stop_tunnel', fake_stop_tunnel)
    monkeypatch.setattr(MODULE, 'run_gate', fake_run_gate)
    monkeypatch.setattr(MODULE, 'choose_local_port', lambda preferred_port: 58080)
    monkeypatch.setattr(
        MODULE.sys,
        'argv',
        [
            'run_phase_c_collaboration_live_gate.py',
            '--output-dir',
            str(tmp_path),
            '--probe-public-url',
            'http://47.99.217.1/manage',
        ],
    )

    rc = MODULE.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert ('start', 58080, 80, '127.0.0.1') in calls
    assert ('gate', 'http://127.0.0.1:58080/manage', tmp_path / 'tunnel') in calls
    assert ('gate', 'http://47.99.217.1/manage', tmp_path / 'public') in calls
    assert any(item[0] == 'stop' for item in calls)
    assert '[public-probe]' in out
    assert '[canonical-gate] http://127.0.0.1:58080/manage' in out


def test_choose_local_port_falls_back_when_preferred_port_is_occupied(monkeypatch):
    monkeypatch.setattr(MODULE, 'port_in_use', lambda host, port: True)

    chosen = MODULE.choose_local_port(58080)

    assert isinstance(chosen, int)
    assert chosen > 0
    assert chosen != 58080
