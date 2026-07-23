import { useEffect, useState } from 'react';
import { Alert, Card, List, Tag, Typography, Spin, Empty } from 'antd';
import type { DslEntry } from './types';

const { Title, Text } = Typography;

interface AgentEntry { id: string; title: string; owner: string; status: string; evidence_class: string; }

export function AgentApp() {
  const [actions, setActions] = useState<AgentEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v2/action-types/')
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d => { setActions(d.items || []); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: 16, height: '100vh', boxSizing: 'border-box', overflowY: 'auto' }}>
      <Title level={4}>Agent 调试台 — 动作类型清单</Title>
      <Card size="small">
        {loading ? <Spin /> :
         error ? <Alert type="error" message={`加载失败: ${error}`} /> :
         actions.length === 0 ? <Empty description="暂无动作类型 DSL 条目" /> :
         <List
           dataSource={actions}
           renderItem={(a: AgentEntry) => (
             <List.Item>
               <List.Item.Meta
                 title={<Text strong>{a.title || a.id}</Text>}
                 description={
                   <span>
                     <Tag>{a.id}</Tag>
                     <Tag color={a.status === 'active' ? 'green' : 'default'}>{a.status}</Tag>
                     <Tag color="purple">{a.evidence_class}</Tag>
                     <Text type="secondary"> owner: {a.owner}</Text>
                   </span>
                 }
               />
             </List.Item>
           )}
         />}
      </Card>
      <Alert
        type="info"
        style={{ marginTop: 16 }}
        message="Agent 对话调试（ai SDK 流式）为 P1 骨架，待集成 FlowMindDeploy mcp-server 的对话 bridge surface"
      />
    </div>
  );
}
