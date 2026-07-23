/**
 * OntologyGraphView — simplified force-directed graph of DSL ontology entries.
 *
 * Adapted from bkn-studio's OntologyGraphView design (ADR-002: self-contained,
 * no framework-layer dependency). Nodes = DSL entries; edges = same-owner links.
 * Layout: basic force simulation (repulsion + spring).
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { SelectOutlined, ZoomInOutlined, ZoomOutOutlined, CompressOutlined } from '@ant-design/icons';
import { Button, Space, Tag, Typography } from 'antd';
import type { DslEntry, GraphNode, GraphEdge } from '../types';

const { Text } = Typography;

const KIND_COLORS: Record<string, string> = {
  object: '#2e68ff',
  action: '#7c4dff',
  constraint: '#eb5757',
  context: '#00b8a3',
  relation: '#f5a623',
  risk: '#9b51e0',
};

const NODE_RADIUS = 26;
const ZOOM_MIN = 0.4;
const ZOOM_MAX = 2.5;

interface Props {
  entries: DslEntry[];
}

export function OntologyGraphView({ entries }: Props) {
  const [view, setView] = useState({ x: 0, y: 0, zoom: 1 });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Build nodes + edges from entries
  const { nodes, edges } = useMemo(() => {
    const ns: GraphNode[] = entries.map((e, i) => {
      const angle = (i / entries.length) * 2 * Math.PI;
      const r = 200 + (i % 3) * 60;
      return {
        id: e.id,
        label: e.title || e.id,
        kind: e.kind,
        x: 400 + r * Math.cos(angle),
        y: 300 + r * Math.sin(angle),
        vx: 0,
        vy: 0,
      };
    });
    // Edges: link entries sharing same owner (cap per node to avoid clutter)
    const es: GraphEdge[] = [];
    const byOwner: Record<string, GraphNode[]> = {};
    ns.forEach(n => {
      const e = entries.find(x => x.id === n.id)!;
      const owner = e.owner || 'unknown';
      (byOwner[owner] = byOwner[owner] || []).push(n);
    });
    Object.values(byOwner).forEach(group => {
      for (let i = 0; i < group.length && i < 4; i++) {
        for (let j = i + 1; j < group.length && j < 5; j++) {
          es.push({ source: group[i].id, target: group[j].id, kind: 'same-owner' });
        }
      }
    });
    return { nodes: ns, edges: es };
  }, [entries]);

  // Simple force simulation (a few iterations on mount / entry change)
  const layoutNodes = useMemo(() => {
    const ns = nodes.map(n => ({ ...n }));
    const iterations = 60;
    const k = 80; // ideal distance
    const repulsion = 4000;
    const nodeById = new Map(ns.map(n => [n.id, n]));
    for (let iter = 0; iter < iterations; iter++) {
      // Repulsion
      for (let i = 0; i < ns.length; i++) {
        for (let j = i + 1; j < ns.length; j++) {
          const dx = ns[i].x - ns[j].x;
          const dy = ns[i].y - ns[j].y;
          const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
          const force = repulsion / (dist * dist);
          ns[i].vx += (dx / dist) * force;
          ns[i].vy += (dy / dist) * force;
          ns[j].vx -= (dx / dist) * force;
          ns[j].vy -= (dy / dist) * force;
        }
      }
      // Spring (attraction along edges)
      edges.forEach(e => {
        const s = nodeById.get(e.source)!;
        const t = nodeById.get(e.target)!;
        const dx = t.x - s.x;
        const dy = t.y - s.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const force = (dist - k) * 0.05;
        s.vx += (dx / dist) * force;
        s.vy += (dy / dist) * force;
        t.vx -= (dx / dist) * force;
        t.vy -= (dy / dist) * force;
      });
      // Apply velocity with damping
      ns.forEach(n => {
        n.x += n.vx * 0.3;
        n.y += n.vy * 0.3;
        n.vx *= 0.7;
        n.vy *= 0.7;
        n.x = Math.max(40, Math.min(760, n.x));
        n.y = Math.max(40, Math.min(560, n.y));
      });
    }
    return ns;
  }, [nodes, edges]);

  const selected = selectedId ? layoutNodes.find(n => n.id === selectedId) : null;
  const selectedEntry = selectedId ? entries.find(e => e.id === selectedId) : null;
  const neighbors = useMemo(() => {
    if (!selectedId) return new Set<string>();
    const nb = new Set<string>();
    edges.forEach(e => {
      if (e.source === selectedId) nb.add(e.target);
      if (e.target === selectedId) nb.add(e.source);
    });
    return nb;
  }, [edges, selectedId]);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setView(v => ({
      ...v,
      zoom: Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, v.zoom * delta)),
    }));
  }, []);

  const reset = () => setView({ x: 0, y: 0, zoom: 1 });

  return (
    <div style={{ display: 'flex', gap: 12, height: '100%' }}>
      <div style={{ flex: 1, position: 'relative', border: '1px solid #e8e8e8', borderRadius: 8, overflow: 'hidden' }}>
        <Space style={{ position: 'absolute', top: 8, right: 8, zIndex: 2 }}>
          <Button icon={<ZoomInOutlined />} onClick={() => setView(v => ({ ...v, zoom: Math.min(ZOOM_MAX, v.zoom * 1.2) }))} />
          <Button icon={<ZoomOutOutlined />} onClick={() => setView(v => ({ ...v, zoom: Math.max(ZOOM_MIN, v.zoom * 0.83) }))} />
          <Button icon={<CompressOutlined />} onClick={reset} />
        </Space>
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="0 0 800 600"
          onWheel={onWheel}
          style={{ background: '#fafafa', cursor: 'grab' }}
        >
          <g transform={`translate(${view.x}, ${view.y}) scale(${view.zoom})`}>
            {edges.map((e, i) => {
              const s = layoutNodes.find(n => n.id === e.source);
              const t = layoutNodes.find(n => n.id === e.target);
              if (!s || !t) return null;
              const dim = selectedId && e.source !== selectedId && e.target !== selectedId;
              return (
                <line
                  key={i}
                  x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  stroke={dim ? '#eee' : '#ccc'}
                  strokeWidth={1}
                />
              );
            })}
            {layoutNodes.map(n => {
              const color = KIND_COLORS[n.kind] || '#64748b';
              const isSel = n.id === selectedId;
              const isNb = neighbors.has(n.id);
              const dim = selectedId && !isSel && !isNb;
              return (
                <g key={n.id} transform={`translate(${n.x}, ${n.y})`} onClick={() => setSelectedId(isSel ? null : n.id)} style={{ cursor: 'pointer' }}>
                  <circle
                    r={NODE_RADIUS}
                    fill={dim ? '#f0f0f0' : color}
                    fillOpacity={dim ? 0.4 : 0.85}
                    stroke={isSel ? '#000' : '#fff'}
                    strokeWidth={isSel ? 3 : 1.5}
                  />
                  <text textAnchor="middle" dy="0.35em" fill={dim ? '#aaa' : '#fff'} fontSize="10" fontWeight={isSel ? 700 : 400}>
                    {n.label.length > 8 ? n.label.slice(0, 7) + '…' : n.label}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>
      {selectedEntry && (
        <div style={{ width: 280, padding: 12, border: '1px solid #e8e8e8', borderRadius: 8, overflowY: 'auto' }}>
          <Typography.Title level={5}>{selectedEntry.title || selectedEntry.id}</Typography.Title>
          <p><Text type="secondary">ID: </Text><Text code>{selectedEntry.id}</Text></p>
          <p><Tag color={KIND_COLORS[selectedEntry.kind]}>{selectedEntry.kind}</Tag></p>
          <p><Text type="secondary">Owner: </Text>{selectedEntry.owner}</p>
          <p><Text type="secondary">Status: </Text>{selectedEntry.status}</p>
          <p><Text type="secondary">Evidence: </Text>{selectedEntry.evidence_class}</p>
          <p style={{ marginTop: 8 }}><Text type="secondary">关联节点: {neighbors.size}</Text></p>
        </div>
      )}
    </div>
  );
}
