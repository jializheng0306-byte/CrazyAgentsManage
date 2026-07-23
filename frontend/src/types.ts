/** CAM Studio frontend types (simplified, independent of bkn-studio). */

export interface DslEntry {
  id: string;
  kind: string;
  title: string;
  owner: string;
  status: string;
  evidence_class: string;
}

export interface KnowledgeNetworksResponse {
  total: number;
  by_kind: Record<string, number>;
  okf_projections: number;
  domains: Record<string, { primary_consumer: string }>;
  by_owner: Record<string, DslEntry[]>;
  read_only: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  kind: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  kind: 'same-owner' | 'same-kind';
}
