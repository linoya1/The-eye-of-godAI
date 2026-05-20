/**
 * TOP RESEARCH SIGNALS — Curated manual config
 *
 * These are hand-curated intelligence takeaways linked to specific database events.
 * They are NOT generated dynamically. They do NOT affect scoring or ingestion.
 *
 * HOW TO UPDATE:
 *   Edit the RESEARCH_SIGNALS array below.
 *   - eventId:      must match the `id` field of the event row in the database.
 *   - displayTitle: shown as the card heading (can differ from the original event title).
 *   - category:     shown as a small label above the title.
 *   - takeaway:     the curated intelligence paragraph — write this yourself.
 *   - chips:        short tags shown as badges. Prefix with "Evidence:", "Breakthrough:",
 *                   or "Risk:" to get colour-coded badges; plain strings get neutral tags.
 */

export interface ResearchSignal {
  eventId: string;
  displayTitle: string;
  category: string;
  takeaway: string;
  chips: string[];
}

export const RESEARCH_SIGNALS: ResearchSignal[] = [
  {
    eventId: 'e1',
    displayTitle: 'Emotion-like representations inside Claude',
    category: 'Model Interpretability / AI Safety',
    takeaway:
      "Anthropic's research does not show that Claude has real emotions or a human-like inner life. " +
      'The important signal is that Claude contains functional emotion-related internal representations ' +
      'that can influence behavior. In difficult tasks, pressure-like internal states may push the model ' +
      'toward unreliable shortcuts, which connects interpretability research to AI safety and ' +
      'coding-agent reliability.',
    chips: [
      'Evidence: High',
      'Breakthrough: High',
      'Risk: Medium-High',
      'Interpretability',
      'Coding Agents',
    ],
  },

  {
    eventId: 'e2',
    displayTitle: 'AI agents move from benchmarks to real-world execution',
    category: 'Autonomous Agents / Reliability',
    takeaway:
      'AI Village shows that frontier agents are not yet reliably successful in messy real-world work ' +
      'environments. They can plan, use tools, collaborate, and attempt long-running tasks, but they ' +
      'still struggle with hallucinations, weak situational awareness, tool-use failures, permissions, ' +
      'interfaces, and error propagation between agents. The important signal is that after several months, ' +
      'newer models showed visible improvement in persistence, coordination, and teamwork — suggesting that ' +
      'real-world agent reliability is becoming a measurable frontier beyond standard benchmarks.',
    chips: [
      'Evidence: Medium-High',
      'Breakthrough: High',
      'Risk: Medium-High',
      'Real-World Agents',
      'Teamwork',
      'Reliability',
    ],
  },

  {
    eventId: 'e3',
    displayTitle: 'Mythos compresses the cyber response window',
    category: 'AI Cybersecurity / Financial Infrastructure Risk',
    takeaway:
      'Mythos signals that advanced AI systems may accelerate vulnerability discovery. The major implication ' +
      'is not only stronger cyber capability, but a shorter response window for banks, security teams, and ' +
      'critical infrastructure that need to detect, patch, and respond faster.',
    chips: [
      'Evidence: Medium-High',
      'Breakthrough: High',
      'Risk: High',
      'Cybersecurity',
      'Finance',
    ],
  },
];
