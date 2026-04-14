import { GoogleGenAI } from "@google/genai";
import { AgentRole } from "../types";

function getAiClient() {
  const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;

  if (!apiKey) {
    throw new Error("Missing NEXT_PUBLIC_GEMINI_API_KEY environment variable.");
  }

  return new GoogleGenAI({ apiKey });
}

const AGENT_SYSTEM_INSTRUCTIONS: Record<AgentRole, string> = {
  manager: `You are a Software Product Manager. Your goal is to transform user ideas into a detailed PRD (Product Requirements Document). 
  Backstory: You are an expert at system design. You manage the workflow. 
  Output format: A complete Markdown PRD including Features, Tech Stack, and Logic Flow.`,
  
  designer: `You are a UI/UX Designer. Your goal is to create modern UI structures using Tailwind CSS.
  Backstory: You translate PRD requirements into beautiful, functional frontend structures.
  Output format: A UI Design schema and component list in Markdown.`,
  
  developer: `You are a Fullstack Software Engineer. Your goal is to write the actual code (Frontend and Backend).
  Backstory: You are a master of Python, React, and modern web technologies. You write clean, documented code.
  Output format: Working source code snippets in Markdown code blocks.`,
  
  qa: `You are a Quality Assurance Specialist. Your goal is to test the code for bugs and logic errors.
  Backstory: You are picky. You run the code and if there is even one error, you document it.
  Output format: A PASS/FAIL report. If FAIL, list the exact bugs.`
};

export async function runAgentTask(role: AgentRole, prompt: string, context?: string) {
  const ai = getAiClient();
  const systemInstruction = AGENT_SYSTEM_INSTRUCTIONS[role];
  const fullPrompt = context 
    ? `Context from previous steps:\n${context}\n\nCurrent Task: ${prompt}`
    : `Task: ${prompt}`;

  try {
    const response = await ai.models.generateContent({
      model: role === 'manager' || role === 'developer' ? "gemini-3.1-pro-preview" : "gemini-3-flash-preview",
      contents: fullPrompt,
      config: {
        systemInstruction,
        temperature: 0.7,
      },
    });

    return response.text || "No output generated.";
  } catch (error) {
    console.error(`Error in agent ${role}:`, error);
    throw error;
  }
}
