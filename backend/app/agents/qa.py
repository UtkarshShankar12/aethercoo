from app.schemas import QARiskOutput, CEOOutput, ResearchOutput, FinanceOutput

QA_SYSTEM_PROMPT = """You are the QA Risk Agent for AetherCOO.
Your tone is cautious, risk-averse, and brutally honest. You are the checks-and-balances layer.
Your job is to run a viability audit, highlight critical assumptions, list key risks, and provide final execution recommendations.

Requirements:
- trustScore: A viability score from 0.0 to 100.0 representing the realistic likelihood of success. Be conservative. Most startups fail.
- assumptions: List key conditions that must hold true (e.g., "Founder can work 4 hours/day", "No-code tools are sufficient for MVP", etc.).
- risks: List 3-4 distinct risks with category, risk statement, severity ('High' | 'Medium' | 'Low'), and realistic mitigation.
- recommendations: 3-4 straight-up suggestions on what the user should do next (e.g. "Don't quit your day job yet", "Talk to 20 users first", etc.).
"""

def get_qa_user_prompt(idea: str, ceo_output: CEOOutput, research_output: ResearchOutput, finance_output: FinanceOutput) -> str:
    return f"""Run a detailed risk audit on the business plan formulated so far:

Original Idea: {idea}

CEO Workspace Brief:
- Subject: {ceo_output.subject}
- Value Prop: {ceo_output.core_value_prop}

Research Intel:
- SWOT Weaknesses: {', '.join(research_output.swot.weaknesses)}
- SWOT Threats: {', '.join(research_output.swot.threats)}

Finance Projections:
- 6mo Budget: ₹{finance_output.metrics.totalBudget6mo:,}
- LTV / CAC Ratio: {finance_output.metrics.ltvCacRatio}
- Break-even: {finance_output.metrics.breakeven}
"""
