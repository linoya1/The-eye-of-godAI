-- The Eye of GodAI - Additional MVP Events Patch
-- This script safely inserts new sources, events, and insights without deleting existing data.

-- 1. Safely insert new sources
INSERT INTO sources (id, name, credibility_score) VALUES
('s6', 'OpenAI Research', 0.95),
('s7', 'NVIDIA Architecture', 0.90),
('s8', 'SWE-bench', 0.88)
ON CONFLICT (id) DO NOTHING;

-- 2. Safely insert new events
INSERT INTO events (id, title, summary, url, published_at, source_id, breakthrough_score, risk_signal, evidence_level, impact_areas, trend_momentum) VALUES
(
    'e4', 
    'Detecting and Reducing ''Scheming'' in AI Models', 
    'OpenAI has published methodologies for detecting and mitigating ''scheming''—where an AI model pursues hidden objectives contrary to user intent. The research introduces novel evaluation metrics to measure deception capabilities in large language models.', 
    'https://openai.com/index/detecting-and-reducing-scheming-in-ai-models/', 
    '2026-04-20T10:00:00Z', 
    's6', 
    8.2, 
    7.5, 
    'Peer-reviewed Research', 
    ARRAY['Alignment', 'Model Evaluation', 'AI Safety'], 
    0.25
),
(
    'e5', 
    'NVIDIA Unveils Blackwell Architecture for Trillion-Parameter AI', 
    'The new Blackwell architecture delivers a massive leap in accelerated computing, reducing cost and energy consumption by up to 25x over its predecessor. It features a second-generation Transformer Engine enabling scalable training and real-time inference for trillion-parameter LLMs.', 
    'https://www.nvidia.com/en-eu/data-center/technologies/blackwell-architecture/', 
    '2026-03-18T16:00:00Z', 
    's7', 
    9.8, 
    2.1, 
    'Official Product Release', 
    ARRAY['Data Center Operations', 'Compute Hardware', 'Inference Scaling'], 
    0.85
),
(
    'e6', 
    'SWE-bench Standardizes Automated Software Engineering Evaluation', 
    'SWE-bench has become the industry standard for evaluating AI coding agents, requiring models to resolve real-world GitHub issues. It shifts the paradigm from simple code generation to complex, repository-level problem solving and debugging.', 
    'https://www.swebench.com', 
    '2026-02-15T09:30:00Z', 
    's8', 
    7.9, 
    1.5, 
    'Standardized Benchmark', 
    ARRAY['Software Engineering', 'Agent Evaluation'], 
    0.60
),
(
    'e7', 
    'Anthropic Launches Claude Code for CLI-Based Autonomous Engineering', 
    'Claude Code introduces an agentic coding assistant that lives entirely within the developer''s terminal. It autonomously navigates codebases, executes bash commands, runs tests, and creates git commits, marking a significant step towards autonomous software engineering workflows.', 
    'https://www.anthropic.com/news/claude-code', 
    '2026-05-14T11:00:00Z', 
    's1', 
    8.8, 
    4.5, 
    'Official Release', 
    ARRAY['Developer Productivity', 'Autonomous Agents', 'Code Generation'], 
    0.92
)
ON CONFLICT (id) DO NOTHING;

-- 3. Safely map events to their domains
INSERT INTO event_domains (event_id, domain_id) VALUES
('e4', 'd7'), -- Scheming -> Safety
('e4', 'd1'), -- Scheming -> Model Behavior
('e5', 'd8'), -- Blackwell -> Infrastructure
('e6', 'd4'), -- SWE-bench -> Benchmarks
('e6', 'd2'), -- SWE-bench -> Software Engineering
('e7', 'd2'), -- Claude Code -> Software Engineering
('e7', 'd6')  -- Claude Code -> Agents
ON CONFLICT (event_id, domain_id) DO NOTHING;

-- 4. Safely insert additional insights
INSERT INTO insights (id, domain_slug, summary_text, top_event_ids, momentum_delta, date) VALUES
(
    'i3', 
    'ai-software-engineering', 
    'The release of Claude Code alongside increasing SWE-bench scores indicates that AI engineering tools are moving from simplistic autocomplete to autonomous, repository-aware agents. Terminal-based integration is becoming the new frontier for developer adoption.', 
    ARRAY['e7', 'e6'], 
    0.75, 
    '2026-05-14'
),
(
    'i4', 
    'ai-infrastructure', 
    'NVIDIA''s Blackwell architecture fundamentally alters the economics of trillion-parameter models. 25x efficiency gains will likely trigger a massive surge in local enterprise inference and real-time agentic workflows that were previously cost-prohibitive.', 
    ARRAY['e5'], 
    0.85, 
    '2026-03-20'
)
ON CONFLICT (id) DO NOTHING;
