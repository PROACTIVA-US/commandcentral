export interface AgentExecutionConfig {
  maxMemoryMb: number;
  timeoutSeconds: number;
  outputSchema: object;
  secrets?: Record<string, string>;
  allowNetwork?: boolean;
}

export interface AgentExecutionResult {
  success: boolean;
  output?: unknown;
  error?: string;
  executionTimeMs: number;
  containerLogs?: string;
}
