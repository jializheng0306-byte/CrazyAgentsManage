"""Tests for BKN Studio fusion v2 blueprints (P0)."""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from app import app


class KnowledgeNetworksTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list_networks(self):
        resp = self.client.get('/api/v2/knowledge-networks/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])
        self.assertIn('by_kind', data)
        self.assertIn('total', data)

    def test_list_networks_no_trailing_slash(self):
        resp = self.client.get('/api/v2/knowledge-networks')
        self.assertEqual(resp.status_code, 200)

    def test_total_matches_kind_sum(self):
        resp = self.client.get('/api/v2/knowledge-networks/')
        data = json.loads(resp.data)
        self.assertEqual(data['total'], sum(data['by_kind'].values()))


class ObjectTypesTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list(self):
        resp = self.client.get('/api/v2/object-types/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])
        self.assertIsInstance(data['items'], list)

    def test_get_existing(self):
        resp = self.client.get('/api/v2/object-types/')
        items = json.loads(resp.data)['items']
        if not items:
            self.skipTest("no object DSL entries (FMD not found)")
        entry_id = items[0]['id']
        resp2 = self.client.get(f'/api/v2/object-types/{entry_id}')
        self.assertEqual(resp2.status_code, 200)
        entry = json.loads(resp2.data)
        self.assertEqual(entry['kind'], 'object')

    def test_get_nonexistent_404(self):
        resp = self.client.get('/api/v2/object-types/nonexistent-id-xyz')
        self.assertEqual(resp.status_code, 404)


class ActionTypesTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list(self):
        resp = self.client.get('/api/v2/action-types/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])
        for item in data['items']:
            self.assertIn('input', item)
            self.assertIn('output', item)
            self.assertIn('authority_profile', item)


class RelationTypesTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list(self):
        resp = self.client.get('/api/v2/relation-types/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])


class ContextLoaderTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_context_pack_graceful_when_fmd_down(self):
        resp = self.client.get('/api/v2/context-loader/pack/test-candidate')
        self.assertIn(resp.status_code, (200, 502))
        data = json.loads(resp.data)
        self.assertTrue(data.get('read_only', True))


class SkillsEnhancedTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list_graceful(self):
        resp = self.client.get('/api/v2/skills/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])
        self.assertIn('skills', data)

    def test_detail_404(self):
        resp = self.client.get('/api/v2/skills/nonexistent-skill-xyz')
        self.assertEqual(resp.status_code, 404)


class McpToolsTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_list(self):
        resp = self.client.get('/api/v2/mcp-tools/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])

    def test_instance_tools_placeholder(self):
        resp = self.client.get('/api/v2/mcp-tools/test-instance/tools')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['read_only'])


class ReadOnlyInvariantTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_post_not_allowed_on_knowledge_networks(self):
        resp = self.client.post('/api/v2/knowledge-networks/')
        self.assertIn(resp.status_code, (405, 404))

    def test_put_not_allowed_on_object_types(self):
        resp = self.client.put('/api/v2/object-types/')
        self.assertIn(resp.status_code, (405, 404))

    def test_delete_not_allowed_on_action_types(self):
        resp = self.client.delete('/api/v2/action-types/')
        self.assertIn(resp.status_code, (405, 404))


if __name__ == '__main__':
    unittest.main(verbosity=2)
