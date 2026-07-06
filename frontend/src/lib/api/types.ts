// RouteIQ API Types

export type ProviderStatus = {
  name: string;
  available: boolean;
  latency_ms: number | null;
  detail: string;
};

export type StatusResponse = {
  service: string;
  version: string;
  environment: string;
  status: string;
  checked_at: string;
  providers: ProviderStatus[];
};

export type MetricsResponse = {
  total_requests: number;
  local_requests: number;
  cloud_requests: number;
  hybrid_requests: number;
  fallback_count: number;
  avg_latency_ms: number;
  estimated_cloud_tokens_avoided: number;
  estimated_token_savings_usd: number;
  provider_split_percent: {
    local: number;
    cloud: number;
    hybrid: number;
  };
  recent_decisions: Array<{
    request_id: string;
    target: string;
    provider: string;
    latency_ms: number;
    fallback_used: boolean;
    confidence: number;
    summary: string;
  }>;
};

export type RouteDecision = {
  target: string;
  primary_provider: string;
  backup_providers: string[];
  confidence: number;
  fallback_mode: string;
  reason_codes: string[];
  decision_summary: string;
};

export type RouteResponse = {
  request_id: string;
  created_at: string;
  decision: RouteDecision;
  classification: {
    privacy_score: number;
    complexity_score: number;
    latency_score: number;
    cost_score: number;
    estimated_input_tokens: number;
    risk_flags: string[];
    explanation: string[];
  };
  provider_response: {
    provider: string;
    model: string;
    text: string;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    total_tokens: number;
  };
  audit_id: string;
  token_savings_estimate_usd: number;
  latency_ms: number;
  fallback_used: boolean;
  audit_timeline: Array<{
    stage: string;
    message: string;
    created_at: string;
  }>;
};

export type Simulation = {
  id: string;
  task_type: string;
  privacy_level: string;
  force_route: string | null;
  prompt_preview: string;
};

export type RouteRequestParams = {
  prompt: string;
  task_type: string;
  privacy_level: string;
  max_latency_ms?: number;
  prefer_local?: boolean;
};
