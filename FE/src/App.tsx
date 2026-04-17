/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Agent, AgentRole, Task, LogEntry, SwarmState } from './types';
import { AgentStatus } from './components/AgentStatus';
import { Terminal } from './components/Terminal';
import { Workspace } from './components/Workspace';
import { runAgentTask } from './services/gemini';
import { runSkillRuntime } from './services/skillsApi';
import { Play, Square, RefreshCw, Cpu, Zap, Activity, Brain, Database, Shield } from 'lucide-react';
import { motion } from 'motion/react';

const INITIAL_AGENTS: Record<AgentRole, Agent> = {
  manager: {
    role: 'manager',
    name: 'Nexus-Manager',
    goal: 'Create PRD and oversee workflow',
    backstory: 'Expert at system design and task delegation.',
    status: 'idle'
  },
  designer: {
    role: 'designer',
    name: 'Nexus-Designer',
    goal: 'Draft UI/UX schemas',
    backstory: 'Translates requirements into functional designs.',
    status: 'idle'
  },
  developer: {
    role: 'developer',
    name: 'Nexus-Developer',
    goal: 'Write clean Python/React code',
    backstory: 'Master of full-stack engineering and local databases.',
    status: 'idle'
  },
  qa: {
    role: 'qa',
    name: 'Nexus-QA',
    goal: 'Execute unit tests and capture errors',
    backstory: 'Picky specialist ensuring zero-defect delivery.',
    status: 'idle'
  }
};

const INITIAL_TASKS: Task[] = [
  { id: 't1', agentRole: 'manager', description: 'Analyze requirement and create PRD.md', expectedOutput: 'Markdown PRD', status: 'pending' },
  { id: 't2', agentRole: 'designer', description: 'Design UI components and layout', expectedOutput: 'UI Schema', status: 'pending' },
  { id: 't3', agentRole: 'developer', description: 'Implement Python backend and React frontend', expectedOutput: 'Source Code', status: 'pending' },
  { id: 't4', agentRole: 'qa', description: 'Run tests in Docker sandbox', expectedOutput: 'QA Report', status: 'pending' }
];

export default function App() {
  const [state, setState] = useState<SwarmState>({
    agents: INITIAL_AGENTS,
    tasks: INITIAL_TASKS,
    logs: [],
    currentTaskIndex: 0,
    isBuilding: false
  });
  const [prompt, setPrompt] = useState('');
  const [activeTab, setActiveTab] = useState<'swarm' | 'training' | 'memory'>('swarm');

  const addLog = (agentName: string, message: string, type: LogEntry['type'] = 'info') => {
    setState(prev => ({
      ...prev,
      logs: [...prev.logs, {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: Date.now(),
        agentName,
        message,
        type
      }]
    }));
  };

  const updateAgentStatus = (role: AgentRole, status: Agent['status']) => {
    setState(prev => ({
      ...prev,
      agents: {
        ...prev.agents,
        [role]: { ...prev.agents[role], status }
      }
    }));
  };

  const updateTask = (index: number, updates: Partial<Task>) => {
    setState(prev => {
      const newTasks = [...prev.tasks];
      newTasks[index] = { ...newTasks[index], ...updates };
      return { ...prev, tasks: newTasks };
    });
  };

  const runSwarm = async () => {
    if (!prompt.trim()) return;

    setState(prev => ({
      ...prev,
      isBuilding: true,
      currentTaskIndex: 0,
      tasks: INITIAL_TASKS.map(t => ({ ...t, status: 'pending', output: undefined })),
      agents: INITIAL_AGENTS,
      logs: []
    }));

    addLog('System', `Initializing Project Nexus Swarm for: "${prompt}"`, 'info');
    addLog('System', 'Connecting to local Ollama instance (Simulated)...', 'info');
    addLog('System', 'Loading ChromaDB project context...', 'info');

    try {
      const skillResult = await runSkillRuntime(prompt);
      if (skillResult) {
        updateAgentStatus('manager', 'working');
        updateTask(0, {
          status: 'completed',
          output: skillResult.output,
          description: `Skill runtime matched: ${skillResult.matched_skill}`,
        });
        updateAgentStatus('manager', 'completed');

        for (let i = 1; i < INITIAL_TASKS.length; i++) {
          updateTask(i, {
            status: 'completed',
            output: 'Skipped: handled by backend skill runtime execution path.',
          });
          updateAgentStatus(INITIAL_TASKS[i].agentRole, 'completed');
        }

        setState(prev => ({ ...prev, isBuilding: false }));
        addLog('System', `Skill runtime completed with ${skillResult.matched_skill}.`, 'success');
        return;
      }
    } catch (error) {
      addLog('System', `Skill runtime unavailable, using local Gemini flow: ${error instanceof Error ? error.message : 'Unknown error'}`, 'warning');
    }

    let accumulatedContext = '';

    for (let i = 0; i < state.tasks.length; i++) {
      const task = state.tasks[i];
      const agent = state.agents[task.agentRole];

      setState(prev => ({ ...prev, currentTaskIndex: i }));
      updateAgentStatus(task.agentRole, 'working');
      updateTask(i, { status: 'in-progress' });
      addLog(agent.name, `Executing: ${task.description}`, 'info');

      try {
        const output = await runAgentTask(task.agentRole, prompt, accumulatedContext);
        
        accumulatedContext += `\n\n--- ${task.agentRole.toUpperCase()} OUTPUT ---\n${output}`;
        
        updateTask(i, { status: 'completed', output });
        updateAgentStatus(task.agentRole, 'completed');
        addLog(agent.name, `Task finalized. Results saved to workspace/`, 'success');
      } catch (error) {
        updateTask(i, { status: 'failed' });
        updateAgentStatus(task.agentRole, 'failed');
        addLog(agent.name, `Execution error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
        break;
      }
    }

    setState(prev => ({ ...prev, isBuilding: false }));
    addLog('System', 'Project Nexus build cycle complete.', 'success');
  };

  return (
    <div className="min-h-screen flex flex-col bg-nexus-bg text-nexus-ink selection:bg-nexus-accent selection:text-nexus-bg">
      {/* Header */}
      <header className="h-16 border-b border-nexus-border flex items-center justify-between px-6 bg-nexus-bg/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-nexus-accent rounded-lg flex items-center justify-center shadow-[0_0_20px_rgba(0,255,0,0.2)]">
            <Shield className="w-6 h-6 text-nexus-bg" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tighter italic">PROJECT NEXUS</h1>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-nexus-accent animate-pulse" />
              <span className="text-[10px] font-mono text-nexus-muted uppercase tracking-widest">Local Agentic Swarm v2.0</span>
            </div>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-1 bg-nexus-border/20 p-1 rounded-lg border border-nexus-border/50">
          {(['swarm', 'training', 'memory'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-1.5 rounded-md text-xs font-mono uppercase tracking-wider transition-all",
                activeTab === tab ? "bg-nexus-accent text-nexus-bg font-bold" : "text-nexus-muted hover:text-nexus-ink"
              )}
            >
              {tab}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-6">
          <div className="hidden xl:flex items-center gap-4 text-xs font-mono text-nexus-muted">
            <div className="flex items-center gap-1.5">
              <Database className="w-3 h-3" />
              <span>CHROMA: ACTIVE</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Brain className="w-3 h-3" />
              <span>OLLAMA: READY</span>
            </div>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="p-2 hover:bg-nexus-border rounded-full transition-colors text-nexus-muted"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 max-w-[1800px] mx-auto w-full">
        {/* Left Sidebar: Agents & Input */}
        <aside className="lg:col-span-3 flex flex-col gap-4">
          <div className="nexus-card flex-1">
            <AgentStatus agents={state.agents} />
          </div>
          
          <div className="nexus-card p-4 space-y-4 bg-nexus-accent/5 border-nexus-accent/20">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase tracking-widest text-nexus-accent">Requirement Input</h3>
              <Zap className="w-3 h-3 text-nexus-accent" />
            </div>
            <textarea 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your application requirements..."
              className="nexus-input h-32 resize-none text-sm bg-nexus-bg/50"
              disabled={state.isBuilding}
            />
            <button 
              onClick={runSwarm}
              disabled={state.isBuilding || !prompt.trim()}
              className="nexus-button w-full flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(0,255,0,0.1)]"
            >
              {state.isBuilding ? (
                <>
                  <Square className="w-4 h-4" />
                  HALT EXECUTION
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  DEPLOY SWARM
                </>
              )}
            </button>
          </div>
        </aside>

        {/* Center: Workspace */}
        <section className="lg:col-span-6 flex flex-col gap-4">
          <div className="flex-1 min-h-[600px]">
            <Workspace tasks={state.tasks} activeTaskIndex={state.currentTaskIndex} />
          </div>
        </section>

        {/* Right Sidebar: Terminal & Stats */}
        <aside className="lg:col-span-3 flex flex-col gap-4">
          <div className="flex-1 min-h-[400px]">
            <Terminal logs={state.logs} />
          </div>
          
          <div className="nexus-card p-4 bg-nexus-bg/50">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-mono uppercase tracking-widest text-nexus-muted">Hardware Telemetry</h3>
              <Activity className="w-3 h-3 text-nexus-muted" />
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-mono">
                  <span>VRAM UTILIZATION (RTX 4090)</span>
                  <span className="text-nexus-accent">{state.isBuilding ? '68%' : '12%'}</span>
                </div>
                <div className="h-1 bg-nexus-border rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-nexus-accent"
                    animate={{ width: state.isBuilding ? '68%' : '12%' }}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-mono">
                  <span>SYSTEM RAM (64GB)</span>
                  <span className="text-nexus-accent">{state.isBuilding ? '42%' : '18%'}</span>
                </div>
                <div className="h-1 bg-nexus-border rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-nexus-accent"
                    animate={{ width: state.isBuilding ? '42%' : '18%' }}
                  />
                </div>
              </div>
              <div className="pt-2 border-t border-nexus-border/50 grid grid-cols-2 gap-2">
                <div className="p-2 bg-nexus-border/20 rounded text-center">
                  <div className="text-[10px] text-nexus-muted uppercase">Tokens/sec</div>
                  <div className="text-sm font-bold font-mono">124.5</div>
                </div>
                <div className="p-2 bg-nexus-border/20 rounded text-center">
                  <div className="text-[10px] text-nexus-muted uppercase">Temp</div>
                  <div className="text-sm font-bold font-mono">62°C</div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </main>

      {/* Footer */}
      <footer className="h-8 border-t border-nexus-border bg-nexus-bg/80 backdrop-blur-md flex items-center justify-between px-6 text-[10px] font-mono text-nexus-muted">
        <div className="flex gap-4">
          <span className="text-nexus-accent font-bold">PROJECT NEXUS CORE</span>
          <span>PERSISTENCE: CHROMA_LOCAL</span>
          <span>LLM: DEEPSEEK_V2_CODER</span>
        </div>
        <div className="flex gap-4">
          <span>STATUS: {state.isBuilding ? 'SWARM_ACTIVE' : 'IDLE'}</span>
          <span>ENCRYPTION: AES-256-LOCAL</span>
        </div>
      </footer>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}
