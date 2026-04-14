import React from 'react';
import { Agent, AgentRole } from '../types';
import { cn } from '../lib/utils';
import { UserCog, Palette, Code, ShieldCheck, Loader2, CheckCircle2 } from 'lucide-react';

interface AgentStatusProps {
  agents: Record<AgentRole, Agent>;
}

const ROLE_ICONS: Record<AgentRole, React.ReactNode> = {
  manager: <UserCog className="w-5 h-5" />,
  designer: <Palette className="w-5 h-5" />,
  developer: <Code className="w-5 h-5" />,
  qa: <ShieldCheck className="w-5 h-5" />,
};

export function AgentStatus({ agents }: AgentStatusProps) {
  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xs font-mono uppercase tracking-widest text-nexus-muted mb-6">Swarm Status</h2>
      {(Object.entries(agents) as [AgentRole, Agent][]).map(([role, agent]) => (
        <div 
          key={role}
          className={cn(
            "flex items-center gap-4 p-3 rounded-lg border transition-all duration-500",
            agent.status === 'working' ? "border-nexus-accent bg-nexus-accent/5" : "border-nexus-border",
            agent.status === 'completed' ? "border-nexus-accent/50" : ""
          )}
        >
          <div className={cn(
            "p-2 rounded-md",
            agent.status === 'working' ? "text-nexus-accent" : "text-nexus-muted"
          )}>
            {ROLE_ICONS[role]}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-sm font-bold capitalize">{agent.name}</span>
              {agent.status === 'working' && <Loader2 className="w-4 h-4 animate-spin text-nexus-accent" />}
              {agent.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-nexus-accent" />}
            </div>
            <p className="text-xs text-nexus-muted truncate">{agent.goal}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
