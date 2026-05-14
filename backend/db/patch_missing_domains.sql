-- Safely insert missing MVP domains into the database
INSERT INTO domains (id, name, slug, description, icon) 
VALUES
('d5', 'AI Research Breakthroughs & Real-World Impact', 'ai-research-impact', 'Medical AI, robotics, scientific discovery, drug discovery, and climate applications.', '🔬'),
('d8', 'AI Infrastructure & Hardware', 'ai-infrastructure', 'GPUs, AI chips, inference optimization, data centers, and hardware impact.', '⚙️')
ON CONFLICT (id) DO NOTHING;
