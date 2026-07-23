"""BKN Studio fusion blueprints — v2 API namespace.

Each blueprint provides read-only projection of OpenBKN capabilities
absorbed into CrazyAgentsManage. See ADR-003 in
04-bkn-studio-frontend-and-cam-fusion.md.
"""

from .knowledge_networks import bp as knowledge_networks_bp
from .object_types import bp as object_types_bp
from .relation_types import bp as relation_types_bp
from .action_types import bp as action_types_bp
from .context_loader import bp as context_loader_bp
from .skills_enhanced import bp as skills_enhanced_bp
from .mcp_tools import bp as mcp_tools_bp

ALL_BLUEPRINTS = [
    knowledge_networks_bp,
    object_types_bp,
    relation_types_bp,
    action_types_bp,
    context_loader_bp,
    skills_enhanced_bp,
    mcp_tools_bp,
]
