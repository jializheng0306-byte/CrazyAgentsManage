"""
Sprint 1-5 route registration patch for api/routes.py.

This file documents the new routes that need to be added to
api/routes.py's handle_get() and handle_post() functions.

To apply: copy the route blocks into the appropriate sections
of api/routes.py.
"""

# ── Add to handle_get() in api/routes.py ────────────────────────────────────

GET_ROUTES = """
    # ── Sprint 1: Overview API ────────────────────────────────────────────────
    elif path == '/api/overview/stats':
        from api.overview_api import handle_overview_stats
        handle_overview_stats(handler, params)
    elif path == '/api/overview/teams':
        from api.overview_api import handle_overview_teams
        handle_overview_teams(handler, params)
    elif path == '/api/overview/memories':
        from api.overview_api import handle_overview_memories
        handle_overview_memories(handler, params)

    # ── Sprint 2: Dashboard API ───────────────────────────────────────────────
    elif path == '/api/dashboard/stats':
        from api.dashboard_api import handle_dashboard_stats
        handle_dashboard_stats(handler, params)
    elif path == '/api/dashboard/sessions':
        from api.dashboard_api import handle_dashboard_sessions
        handle_dashboard_sessions(handler, params)
    elif path == '/api/dashboard/gateway-status':
        from api.dashboard_api import handle_dashboard_gateway_status
        handle_dashboard_gateway_status(handler, params)
    elif path.startswith('/api/dashboard/session/'):
        session_id = path.split('/')[-1]
        from api.dashboard_api import handle_dashboard_session_detail
        handle_dashboard_session_detail(handler, session_id, params)

    # ── Sprint 2: Sessions API ────────────────────────────────────────────────
    elif path == '/api/sessions/list':
        from api.sessions_api import handle_sessions_list
        handle_sessions_list(handler, params)
    elif path == '/api/sessions/search':
        from api.sessions_api import handle_sessions_search
        handle_sessions_search(handler, params)
    elif path == '/api/sessions/stats':
        from api.sessions_api import handle_sessions_stats
        handle_sessions_stats(handler, params)
    elif path.startswith('/api/sessions/detail/'):
        session_id = path.split('/')[-1]
        from api.sessions_api import handle_sessions_detail
        handle_sessions_detail(handler, session_id, params)
    elif path.startswith('/api/sessions/tree/'):
        session_id = path.split('/')[-1]
        from api.sessions_api import handle_sessions_tree
        handle_sessions_tree(handler, session_id, params)

    # ── Sprint 3: Token API ───────────────────────────────────────────────────
    elif path == '/api/tokens/stats':
        from api.tokens_api import handle_tokens_stats
        handle_tokens_stats(handler, params)
    elif path == '/api/tokens/by-provider':
        from api.tokens_api import handle_tokens_by_provider
        handle_tokens_by_provider(handler, params)
    elif path == '/api/tokens/by-model':
        from api.tokens_api import handle_tokens_by_model
        handle_tokens_by_model(handler, params)
    elif path == '/api/tokens/trend':
        from api.tokens_api import handle_tokens_trend
        handle_tokens_trend(handler, params)
    elif path == '/api/tokens/recent':
        from api.tokens_api import handle_tokens_recent
        handle_tokens_recent(handler, params)

    # ── Sprint 4: Alerts API ──────────────────────────────────────────────────
    elif path == '/api/alerts/list':
        from api.alerts_api import handle_alerts_list
        handle_alerts_list(handler, params)
    elif path == '/api/alerts/platform-status':
        from api.alerts_api import handle_alerts_platform_status
        handle_alerts_platform_status(handler, params)
    elif path == '/api/alerts/process-check':
        from api.alerts_api import handle_alerts_process_check
        handle_alerts_process_check(handler, params)

    # ── Sprint 3: Memory API ──────────────────────────────────────────────────
    elif path == '/api/memory/teams':
        from api.memory_api import handle_memory_teams
        handle_memory_teams(handler, params)
    elif path == '/api/memory/search':
        from api.memory_api import handle_memory_search
        handle_memory_search(handler, params)
    elif path.startswith('/api/memory/team/'):
        team_name = path.split('/')[-1]
        from api.memory_api import handle_memory_team
        handle_memory_team(handler, team_name, params)
    elif path.startswith('/api/memory/role/'):
        role_name = path.split('/')[-1]
        from api.memory_api import handle_memory_role
        handle_memory_role(handler, role_name, params)
"""

# ── Add to handle_post() in api/routes.py ───────────────────────────────────

POST_ROUTES = """
    # ── Sprint 3: Memory API ──────────────────────────────────────────────────
    elif path == '/api/memory/update':
        from api.memory_api import handle_memory_update
        handle_memory_update(handler, params)
"""
