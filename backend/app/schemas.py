from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Input Models ---
class RunCreate(BaseModel):
    idea: str
    user_id: str

# --- CEO Agent Output Models ---
class CEOOutput(BaseModel):
    subject: str = Field(description="The core subject/offering of the business, clean name (e.g. 'premium organic Matcha tea subscription box').")
    businessModel: str = Field(description="The type of business model (e.g. 'Subscription / Recurring Delivery', 'Software Tool (SaaS)').")
    modelType: str = Field(description="Code-friendly business model type: 'saas' | 'subscription' | 'marketplace' | 'app' | 'logistics' | 'local' | 'education'.")
    industry: str = Field(description="The industry category (e.g. 'Food & Beverage', 'Health & Wellness', 'Legal & Compliance').")
    industryType: str = Field(description="Code-friendly industry type: 'food' | 'wellness' | 'compliance' | 'ai' | 'edtech' | 'fintech' | 'tech'.")
    location: str = Field(description="Geographic scope or launch city (e.g. 'Austin, TX', 'Online / Remote').")
    audience: str = Field(description="Target audience demographics (e.g. 'young remote workers').")
    core_value_prop: str = Field(description="Single sentence describing what makes the business unique.")

# --- Research Agent Output Models ---
class SWOT(BaseModel):
    strengths: List[str] = Field(description="List of internal advantages/strengths, written bluntly.")
    weaknesses: List[str] = Field(description="List of internal weaknesses/constraints, written bluntly.")
    opportunities: List[str] = Field(description="List of external opportunities, written bluntly.")
    threats: List[str] = Field(description="List of external threats/market forces, written bluntly.")

class ResearchOutput(BaseModel):
    competitors: List[str] = Field(description="List of 3-4 top competitors, direct or indirect.")
    swot: SWOT = Field(description="SWOT analysis containing strengths, weaknesses, opportunities, threats.")
    marketAnalysis: str = Field(description="A blunt, no-fluff summary of the market dynamics and the competitive landscape.")

# --- Finance Agent Output Models ---
class FinancialPeriod(BaseModel):
    year: str = Field(description="Period label, e.g. 'Month 1-2', 'Month 3-4', 'Month 5-6', 'Month 7-9', 'Month 10-12'.")
    revenue: int = Field(description="Estimated cumulative revenue for this period (in INR/₹).")
    expenses: int = Field(description="Estimated cumulative expenses for this period (in INR/₹).")
    profit: int = Field(description="Estimated cumulative profit/loss for this period (revenue - expenses) (in INR/₹).")

class FinanceMetrics(BaseModel):
    pricing: int = Field(description="Estimated initial product price (in INR/₹).")
    marginPct: int = Field(description="Gross profit margin percentage (integer, e.g., 70 for 70%).")
    cac: int = Field(description="Estimated Customer Acquisition Cost (in INR/₹).")
    ltv: int = Field(description="Estimated Customer Lifetime Value (in INR/₹).")
    ltvCacRatio: str = Field(description="LTV to CAC ratio as a string, e.g., '3.5'.")
    payback: int = Field(description="Payback period in months.")
    breakeven: str = Field(description="Estimated breakeven timeline phrase, e.g., 'Month 8-10'.")
    currency: str = Field(default="₹", description="Currency symbol, defaults to ₹.")
    totalBudget6mo: int = Field(description="Total estimated budget needed to survive for 6 months (in INR/₹).")

class FinanceOutput(BaseModel):
    metrics: FinanceMetrics = Field(description="High level metrics for the business model.")
    financials: List[FinancialPeriod] = Field(description="5 periods representing cash flow projection details.")

# --- QA Risk Agent Output Models ---
class RiskItem(BaseModel):
    category: str = Field(description="Category of the risk, e.g. 'Nobody wants it', 'Regulatory compliance', 'Team split'.")
    risk: str = Field(description="Blunt description of the specific risk event.")
    severity: str = Field(description="Risk severity level: 'High' | 'Medium' | 'Low'.")
    mitigation: str = Field(description="Actionable mitigation plan.")

class QARiskOutput(BaseModel):
    trustScore: float = Field(description="A viability rating score between 0.0 and 100.0.")
    assumptions: List[str] = Field(description="Key constraints and assumptions that must hold true.")
    risks: List[RiskItem] = Field(description="Detailed risk matrix representing critical issues.")
    recommendations: List[str] = Field(description="Straight-up actionable next steps for the founder.")

# --- Consolidation / Roadmap & Revenue Models ---
class RoadmapMonth(BaseModel):
    month: int = Field(description="Month number (1 to 6).")
    priority: str = Field(description="The primary objective/priority of the month.")
    actions: List[str] = Field(description="Specific actionable tasks for this month.")
    budget: int = Field(description="Allotted budget for this month (in INR/₹).")
    realityCheck: str = Field(description="Condition or threshold representing the validation requirement.")

class RevenueStreams(BaseModel):
    primary: str = Field(description="Primary revenue generation mechanism.")
    secondary: str = Field(description="Secondary monetization model (e.g. premium features).")
    honestTruth: str = Field(description="The brutal honesty about timing and cash flow expectations.")

# --- Consolidated Dashboard Schema ---
class RunDashboardOutput(BaseModel):
    id: str = Field(description="The run ID.")
    timestamp: int = Field(description="Epoch millisecond timestamp.")
    goal: str = Field(description="The original user goal.")
    
    # CEO properties
    subject: str
    businessModel: str
    modelType: str
    industry: str
    industryType: str
    location: str
    audience: str
    core_value_prop: str
    
    # Research properties
    competitors: List[str]
    swot: SWOT
    marketAnalysis: str
    
    # Finance properties
    financials: List[FinancialPeriod]
    metrics: FinanceMetrics
    
    # QA properties
    trustScore: float
    assumptions: List[str]
    risks: List[RiskItem]
    recommendations: List[str]
    
    # Generated structures
    roadmap: List[RoadmapMonth]
    revenueModel: RevenueStreams

# --- Chat Advisor Models ---
class ChatMessage(BaseModel):
    sender: str  # "You" | "Advisor"
    text: str
    time: str

class AdvisorRequest(BaseModel):
    messages: List[ChatMessage]
    new_message: str
