export type PluginSummary = {
  tools: string[];
  models: string[];
  policies: string[];
};

export type IsolationKeys = {
  tenant_id: string;
  user_id: string;
  thread_id: string;
  run_id: string;
};

export type StepEvent = {
  step: number;
  kind: string;
  detail: Record<string, unknown>;
  ts_ms: number;
};

export type RunRecord = {
  run_id: string;
  status: string;
  final: string;
  step: number;
  tool_calls: number;
  model_name: string;
  cancel_requested: boolean;
  isolation: IsolationKeys;
  events: StepEvent[];
  demo?: string | null;
  route?: string | null;
  reply?: string;
  user_message?: string;
  budget?: {
    max_steps: number;
    max_wall_ms: number;
    max_tool_calls: number;
  };
  circuit_limit?: number;
  policy_names?: string[];
};

export type DemoInfo = {
  name: string;
  label: string;
  proves: string;
  model_name: string;
};

export type SampleChip = {
  id: string;
  label: string;
  fill: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  run?: RunRecord;
};
