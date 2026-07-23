import { useEffect, useState } from 'react';
import { Alert, Card, Spin, Typography, Tag, Row, Col, Statistic } from 'antd';
import { OntologyGraphView } from './components/OntologyGraphView';
import { fetchKnowledgeNetworks } from './api/client';
import type { DslEntry, KnowledgeNetworksResponse } from './types';

const { Title } = Typography;

export function GraphApp() {
  const [data, setData] = useState<KnowledgeNetworksResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKnowledgeNetworks()
      .then(d => { setData(d); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin tip="加载知识网络..." style={{ padding: 80 }} />;
  if (error) return <Alert type="error" message={`加载失败: ${error}`} style={{ margin: 24 }} />;
  if (!data) return null;

  const entries: DslEntry[] = Object.values(data.by_owner).flat();

  return (
    <div style={{ padding: 16, height: '100vh', boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
      <Title level={4}>知识网络图谱 — OpenBKN 能力吸收</Title>
      <Row gutter={16} style={{ marginBottom: 12 }}>
        <Col span={4}><Statistic title="DSL 条目" value={data.total} /></Col>
        <Col span={4}><Statistic title="OKF 投影" value={data.okf_projections} /></Col>
        {Object.entries(data.by_kind).map(([k, v]) => (
          <Col key={k} span={2}><Statistic title={k} value={v} /></Col>
        ))}
      </Row>
      <Card size="small" style={{ flex: 1, overflow: 'hidden' }}>
        {entries.length > 0 ? (
          <OntologyGraphView entries={entries} />
        ) : (
          <Alert type="info" message="暂无 DSL 条目（FlowMindDeploy ontology 未找到）" />
        )}
      </Card>
      <div style={{ marginTop: 8 }}>
        <Tag color="blue">只读投影</Tag>
        <span style={{ color: '#999', fontSize: 12 }}>数据源: FlowMindDeploy ontology DSL（文件直读）</span>
      </div>
    </div>
  );
}
