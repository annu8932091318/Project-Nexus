from __future__ import annotations

import re
from pathlib import Path
from typing import Dict


def generate_project_artifacts(prompt: str, workspace_root: Path) -> Dict[str, str]:
    text = prompt.lower()
    if "portfolio" in text and "html" in text:
        return _generate_single_file_portfolio(workspace_root)
    return _generate_generic_project_notes(prompt, workspace_root)


def _generate_single_file_portfolio(workspace_root: Path) -> Dict[str, str]:
    artifact_dir = workspace_root / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    html_path = artifact_dir / "developer-portfolio.html"

    html_content = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Developer Portfolio</title>
  <style>
    :root {
      --bg-0: #06131f;
      --bg-1: #0b1f33;
      --card: rgba(255, 255, 255, 0.08);
      --line: rgba(255, 255, 255, 0.16);
      --text: #eaf4ff;
      --muted: #b8d2eb;
      --accent: #37d5ff;
      --accent-2: #5effb0;
      --shadow: 0 22px 44px rgba(2, 10, 20, 0.45);
      --radius: 18px;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Trebuchet MS", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 8% 10%, #163c5f 0%, transparent 38%),
        radial-gradient(circle at 86% 6%, #225a85 0%, transparent 35%),
        linear-gradient(170deg, var(--bg-0), var(--bg-1));
      min-height: 100vh;
      overflow-x: hidden;
    }

    body::before,
    body::after {
      content: "";
      position: fixed;
      inset: auto;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      filter: blur(8px);
      opacity: 0.24;
      z-index: 0;
      pointer-events: none;
    }

    body::before {
      background: var(--accent);
      left: -30px;
      top: 25%;
      animation: floatOrb 10s ease-in-out infinite;
    }

    body::after {
      background: var(--accent-2);
      right: -20px;
      top: 60%;
      animation: floatOrb 13s ease-in-out infinite reverse;
    }

    @keyframes floatOrb {
      0%, 100% { transform: translateY(0) scale(1); }
      50% { transform: translateY(-22px) scale(1.08); }
    }

    .container {
      width: min(1100px, 92%);
      margin: 28px auto 56px;
      position: relative;
      z-index: 1;
    }

    .hero {
      border: 1px solid var(--line);
      background: linear-gradient(145deg, rgba(255, 255, 255, 0.13), rgba(255, 255, 255, 0.03));
      border-radius: 24px;
      box-shadow: var(--shadow);
      padding: 26px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
      animation: slideUp .75s ease both;
    }

    .hero h1 { margin: 0; font-size: clamp(1.8rem, 4.4vw, 3rem); }
    .hero p { margin: 14px 0 0; color: var(--muted); line-height: 1.55; }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(55, 213, 255, 0.45);
      background: rgba(55, 213, 255, 0.15);
      font-size: 0.88rem;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }

    .stat {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--card);
      padding: 12px;
      min-height: 88px;
      transform: translateY(18px);
      opacity: 0;
      animation: slideUp .65s ease forwards;
    }

    .stat:nth-child(2) { animation-delay: .08s; }
    .stat:nth-child(3) { animation-delay: .16s; }
    .stat:nth-child(4) { animation-delay: .24s; }

    .stat .num { font-size: 1.35rem; font-weight: 700; }
    .stat .lbl { color: var(--muted); font-size: .9rem; }

    .grid {
      margin-top: 16px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 18px;
      background: var(--card);
      box-shadow: var(--shadow);
      transform: translateY(18px);
      opacity: 0;
      animation: slideUp .65s ease forwards;
    }

    .card:nth-child(2) { animation-delay: .1s; }
    .card:nth-child(3) { animation-delay: .18s; }
    .card:nth-child(4) { animation-delay: .26s; }

    .card h2 { margin: 0 0 12px; font-size: 1.2rem; }

    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      border: 1px solid rgba(94, 255, 176, 0.45);
      background: rgba(94, 255, 176, 0.14);
      color: #d9fff0;
      padding: 7px 10px;
      border-radius: 999px;
      font-size: .84rem;
    }

    .project {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 11px;
      margin-bottom: 10px;
      background: rgba(255, 255, 255, 0.04);
      transition: transform .25s ease, border-color .25s ease, background .25s ease;
    }

    .project:hover {
      transform: translateY(-3px);
      border-color: rgba(55, 213, 255, 0.6);
      background: rgba(55, 213, 255, 0.09);
    }

    .project h3 { margin: 0 0 6px; font-size: 1rem; }
    .project p { margin: 0; color: var(--muted); font-size: .92rem; }

    .timeline-item {
      border-left: 2px solid rgba(55, 213, 255, 0.5);
      margin: 0 0 11px 8px;
      padding: 0 0 0 12px;
      position: relative;
    }

    .timeline-item::before {
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent);
      position: absolute;
      left: -6px;
      top: 6px;
      box-shadow: 0 0 0 4px rgba(55, 213, 255, 0.18);
    }

    .timeline-item h3 { margin: 0; font-size: .95rem; }
    .timeline-item p { margin: 4px 0 0; color: var(--muted); font-size: .9rem; }

    .footer {
      text-align: center;
      margin-top: 16px;
      color: var(--muted);
      font-size: .9rem;
    }

    @keyframes slideUp {
      from { opacity: 0; transform: translateY(18px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 860px) {
      .hero { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      .stats { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    }

    @media (max-width: 560px) {
      .stats { grid-template-columns: repeat(2, 1fr); }
      .hero { padding: 18px; }
      .card { padding: 14px; }
    }
  </style>
</head>
<body>
  <main class="container">
    <section class="hero" id="hero"></section>
    <section class="grid">
      <article class="card">
        <h2>Skills</h2>
        <div class="chips" id="skills"></div>
      </article>
      <article class="card">
        <h2>Projects</h2>
        <div id="projects"></div>
      </article>
      <article class="card">
        <h2>Experience</h2>
        <div id="experience"></div>
      </article>
      <article class="card">
        <h2>Contact</h2>
        <div id="contact"></div>
      </article>
    </section>
    <p class="footer">Replace portfolioData values with your own details.</p>
  </main>

  <script>
    // Replace this JSON object with your own data later.
    const portfolioData = {
      name: "Aarav Sharma",
      role: "Software Developer",
      tagline: "Building fast, elegant, and reliable web products.",
      summary: "Full-stack developer with a strong focus on frontend quality, clean architecture, and product-minded engineering.",
      stats: [
        { label: "Years Experience", value: "5+" },
        { label: "Projects Shipped", value: "32" },
        { label: "Tech Stack", value: "12" },
        { label: "Client Satisfaction", value: "98%" }
      ],
      skills: ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js", "Python", "REST APIs"],
      projects: [
        {
          title: "Realtime Analytics Dashboard",
          description: "Built a low-latency dashboard with live metrics and alerting workflows.",
          stack: "React, Node.js, WebSocket"
        },
        {
          title: "AI Content Ops Platform",
          description: "Developed a collaborative workspace for AI-assisted content generation and review.",
          stack: "TypeScript, Python, FastAPI"
        },
        {
          title: "E-commerce Performance Revamp",
          description: "Reduced time-to-interactive and improved conversion with frontend optimization.",
          stack: "React, Vite, CDN"
        }
      ],
      experience: [
        {
          title: "Senior Software Developer",
          detail: "Nexus Labs (2023-Present) - Leading frontend architecture and delivery quality."
        },
        {
          title: "Software Engineer",
          detail: "BlueOrbit Tech (2020-2023) - Built scalable web platforms for SaaS clients."
        }
      ],
      contact: {
        email: "you@example.com",
        location: "Bengaluru, India",
        github: "github.com/your-handle",
        linkedin: "linkedin.com/in/your-handle"
      }
    };

    const hero = document.getElementById("hero");
    hero.innerHTML = `
      <div>
        <h1>${portfolioData.name}</h1>
        <p><strong>${portfolioData.role}</strong> - ${portfolioData.tagline}</p>
        <p>${portfolioData.summary}</p>
        <span class="badge">Open for impactful engineering roles</span>
      </div>
      <div class="stats">
        ${portfolioData.stats.map(item => `
          <div class="stat">
            <div class="num">${item.value}</div>
            <div class="lbl">${item.label}</div>
          </div>
        `).join("")}
      </div>
    `;

    document.getElementById("skills").innerHTML = portfolioData.skills
      .map(skill => `<span class="chip">${skill}</span>`)
      .join("");

    document.getElementById("projects").innerHTML = portfolioData.projects
      .map(project => `
        <div class="project">
          <h3>${project.title}</h3>
          <p>${project.description}</p>
          <p><strong>Stack:</strong> ${project.stack}</p>
        </div>
      `)
      .join("");

    document.getElementById("experience").innerHTML = portfolioData.experience
      .map(item => `
        <div class="timeline-item">
          <h3>${item.title}</h3>
          <p>${item.detail}</p>
        </div>
      `)
      .join("");

    const c = portfolioData.contact;
    document.getElementById("contact").innerHTML = `
      <p><strong>Email:</strong> ${c.email}</p>
      <p><strong>Location:</strong> ${c.location}</p>
      <p><strong>GitHub:</strong> ${c.github}</p>
      <p><strong>LinkedIn:</strong> ${c.linkedin}</p>
    `;
  </script>
</body>
</html>
"""

    html_path.write_text(html_content, encoding="utf-8")
    return {
      "project_html": str(html_path),
      "project_type": "single_file_portfolio",
    }


def _generate_generic_project_notes(prompt: str, workspace_root: Path) -> Dict[str, str]:
    artifact_dir = workspace_root / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    readme_path = artifact_dir / "project-implementation-notes.md"
    title = _slug_title(prompt)
    readme_path.write_text(
        "\n".join(
            [
                f"# Implementation Draft: {title}",
                "",
                "No specialized generator matched this prompt yet.",
                "Create domain-specific generator logic in src/project_builder.py for this project type.",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "project_notes": str(readme_path),
        "project_type": "generic_notes",
    }


def _slug_title(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return "Untitled"
    return cleaned[:80]
