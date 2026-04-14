export type AgentRole = 'manager' | 'designer' | 'developer' | 'qa';

export interface Agent {
  role: AgentRole;
  name: string;
  goal: string;
  backstory: string;
  status: 'idle' | 'working' | 'completed' | 'failed';
}

export interface Task {
  id: string;
  agentRole: AgentRole;
  description: string;
  expectedOutput: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  output?: string;
}

export interface LogEntry {
  id: string;
  timestamp: number;
  agentName: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export interface SwarmState {
  agents: Record<AgentRole, Agent>;
  tasks: Task[];
  logs: LogEntry[];
  currentTaskIndex: number;
  isBuilding: boolean;
}
