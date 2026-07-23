"""Skills Enhanced API — projects Hermes skills/ directory.

Extends existing /api/operations/integrations with per-skill detail + file tree.
Read-only projection.
"""

import json
import os
from pathlib import Path
from flask import Blueprint, jsonify

bp = Blueprint('skills_enhanced', __name__, url_prefix='/api/v2/skills')


def _get_hermes_home():
    return Path(os.environ.get('HERMES_HOME', os.path.expanduser('~/.hermes')))


def _scan_skill_file(skill_dir):
    """Read SKILL.md frontmatter from a skill directory."""
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        return None
    try:
        content = skill_md.read_text(encoding='utf-8')
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                fm = yaml.safe_load(parts[1]) or {}
                return {
                    'id': fm.get('name', skill_dir.name),
                    'name': fm.get('name', skill_dir.name),
                    'description': fm.get('description', ''),
                    'allowed_tools': fm.get('allowed-tools', fm.get('allowed_tools', [])),
                    'dir_name': skill_dir.name,
                    'path': str(skill_dir),
                }
    except Exception:
        pass
    return {'id': skill_dir.name, 'name': skill_dir.name, 'description': '', 'dir_name': skill_dir.name}


def _list_skill_files(skill_dir):
    """List files in a skill directory (max depth 2)."""
    files = []
    for f in sorted(skill_dir.rglob('*')):
        if f.is_file():
            rel = f.relative_to(skill_dir)
            if len(rel.parts) <= 3:
                files.append({
                    'path': str(rel),
                    'size': f.stat().st_size,
                })
    return files


@bp.route('')
@bp.route('/')
def list_skills():
    home = _get_hermes_home()
    skills_dir = home / 'skills'
    if not skills_dir.exists():
        return jsonify({'skills': [], 'total': 0, 'read_only': True,
                        'note': f'skills dir not found at {skills_dir}'})
    skills = []
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and not d.name.startswith('.'):
            info = _scan_skill_file(d)
            if info:
                skills.append(info)
    return jsonify({'skills': skills, 'total': len(skills), 'read_only': True})


@bp.route('/<skill_id>')
def get_skill_detail(skill_id):
    home = _get_hermes_home()
    skill_dir = home / 'skills' / skill_id
    if not skill_dir.exists():
        return jsonify({'error': 'skill not found', 'skill_id': skill_id}), 404
    info = _scan_skill_file(skill_dir) or {'id': skill_id, 'name': skill_id}
    info['files'] = _list_skill_files(skill_dir)
    info['read_only'] = True
    return jsonify(info)
