/** CAM API client — fetches v2 blueprint endpoints (same-origin, cookie auth). */

import type { KnowledgeNetworksResponse } from '../types';

const BASE = (import.meta as any).env?.BASE_URL ?? '/';

export async function fetchKnowledgeNetworks(): Promise<KnowledgeNetworksResponse> {
  const resp = await fetch(`${BASE}api/v2/knowledge-networks/`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
