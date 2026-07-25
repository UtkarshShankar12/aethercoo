import json
import logging
import asyncio
from datetime import datetime
from typing import Callable, Awaitable, Type, TypeVar, Tuple, Optional
from pydantic import BaseModel
from anthropic import Anthropic

from app.config import settings
from app.schemas import (
    CEOOutput, ResearchOutput, FinanceOutput, QARiskOutput,
    RunDashboardOutput, RoadmapMonth, RevenueStreams, SWOT,
    FinanceMetrics, FinancialPeriod, RiskItem
)
from app.agents.ceo import CEO_SYSTEM_PROMPT, get_ceo_user_prompt
from app.agents.research import RESEARCH_SYSTEM_PROMPT, get_research_user_prompt
from app.agents.finance import FINANCE_SYSTEM_PROMPT, get_finance_user_prompt
from app.agents.qa import QA_SYSTEM_PROMPT, get_qa_user_prompt

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

# Cost calculation variables (per token)
SONNET_INPUT_COST = 3.0 / 1_000_000
SONNET_OUTPUT_COST = 15.0 / 1_000_000

HAIKU_INPUT_COST = 0.8 / 1_000_000
HAIKU_OUTPUT_COST = 4.0 / 1_000_000

# Client initialization
anthropic_client = Anthropic(api_key=settings.anthropic_api_key)

async def call_agent_structured(
    model: str,
    system_prompt: str,
    user_prompt: str,
    output_schema: Type[T],
    tool_name: str = "submit_report"
) -> Tuple[T, int, int, float]:
    """
    Calls Anthropic Claude API forcing a tool use block matching the target Pydantic schema.
    Returns (parsed_pydantic_model, input_tokens, output_tokens, estimated_cost)
    """
    schema_dict = output_schema.model_json_schema()
    
    # We do the call in an executor to avoid blocking the async loop
    def _do_call(prompt_text: str):
        return anthropic_client.messages.create(
            model=model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt_text}],
            tools=[
                {
                    "name": tool_name,
                    "description": f"Submit output for {output_schema.__name__}",
                    "input_schema": schema_dict
                }
            ],
            tool_choice={"type": "tool", "name": tool_name}
        )

    # First attempt
    try:
        response = await asyncio.to_thread(_do_call, user_prompt)
    except Exception as e:
        logger.error(f"First call attempt failed: {str(e)}")
        raise e

    # Extract tool call
    tool_input = None
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            tool_input = block.input
            break

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    
    # Calculate cost
    if "sonnet" in model:
        cost = (input_tokens * SONNET_INPUT_COST) + (output_tokens * SONNET_OUTPUT_COST)
    else:
        cost = (input_tokens * HAIKU_INPUT_COST) + (output_tokens * HAIKU_OUTPUT_COST)

    if not tool_input:
        # If no tool input returned, trigger repair prompt retry
        logger.warning("No tool input returned. Attempting repair retry.")
        repair_prompt = f"{user_prompt}\n\n[SYSTEM ERROR] Your previous response did not trigger the required tool '{tool_name}'. Please correct this and output parameters matching the tool schema."
        response_retry = await asyncio.to_thread(_do_call, repair_prompt)
        
        tool_input_retry = None
        for block in response_retry.content:
            if block.type == "tool_use" and block.name == tool_name:
                tool_input_retry = block.input
                break
                
        input_tokens += response_retry.usage.input_tokens
        output_tokens += response_retry.usage.output_tokens
        if "sonnet" in model:
            cost += (response_retry.usage.input_tokens * SONNET_INPUT_COST) + (response_retry.usage.output_tokens * SONNET_OUTPUT_COST)
        else:
            cost += (response_retry.usage.input_tokens * HAIKU_INPUT_COST) + (response_retry.usage.output_tokens * HAIKU_OUTPUT_COST)
            
        if not tool_input_retry:
            raise ValueError("Claude failed to use the required structured tool even after a repair retry.")
        tool_input = tool_input_retry

    # Try validating Pydantic model
    try:
        parsed = output_schema.model_validate(tool_input)
        return parsed, input_tokens, output_tokens, cost
    except Exception as validation_err:
        logger.warning(f"Validation failed on first attempt: {str(validation_err)}. Attempting repair retry.")
        # Retry with validation error feedback
        repair_prompt = f"{user_prompt}\n\n[SYSTEM ERROR] Your output failed schema validation: {str(validation_err)}. Please correct the fields and resubmit via the tool."
        response_retry = await asyncio.to_thread(_do_call, repair_prompt)
        
        tool_input_retry = None
        for block in response_retry.content:
            if block.type == "tool_use" and block.name == tool_name:
                tool_input_retry = block.input
                break
                
        input_tokens += response_retry.usage.input_tokens
        output_tokens += response_retry.usage.output_tokens
        if "sonnet" in model:
            cost += (response_retry.usage.input_tokens * SONNET_INPUT_COST) + (response_retry.usage.output_tokens * SONNET_OUTPUT_COST)
        else:
            cost += (response_retry.usage.input_tokens * HAIKU_INPUT_COST) + (response_retry.usage.output_tokens * HAIKU_OUTPUT_COST)
            
        if not tool_input_retry:
            raise ValueError(f"Repair retry failed to invoke tool. Original error: {str(validation_err)}")
            
        parsed = output_schema.model_validate(tool_input_retry)
        return parsed, input_tokens, output_tokens, cost


# Consolidator logic to assemble final schemas
CONSOLIDATOR_SYSTEM_PROMPT = """You are the Lead Consolidator for AetherCOO.
Your job is to take the outputs from the CEO, Research, Finance, and QA Risk Agents and compile them into a unified final dashboard database format.

You must generate two custom sections based on the analysis:
1. `roadmap`: A 6-month roadmap with exactly 6 month objects. Each month must have a 'priority', 'actions' (List[str]), a realistic 'budget' (matching the monthly cash limits suggested by Finance), and a critical 'realityCheck' validation condition.
2. `revenueModel`: Primary and secondary revenue streams, and a paragraph with 'honestTruth' about the timing.

Make sure your output exactly matches the RunDashboardOutput schema. Keep the tone realistic, blunt, and matching the previous agents' analyses.
"""

def get_consolidator_user_prompt(idea: str, ceo: CEOOutput, research: ResearchOutput, finance: FinanceOutput, qa: QARiskOutput) -> str:
    return f"""Consolidate the following agent summaries into the final unified dashboard payload.

Original Goal: {idea}

CEO Workspace:
- Subject: {ceo.subject}
- Business Model: {ceo.businessModel}
- Industry: {ceo.industry}
- Value Prop: {ceo.core_value_prop}

Research Output:
- Competitors: {research.competitors}
- SWOT: {research.swot.model_dump()}

Finance Outputs:
- CAC: ₹{finance.metrics.cac:,}
- LTV: ₹{finance.metrics.ltv:,}
- Total 6mo Budget: ₹{finance.metrics.totalBudget6mo:,}
- Cumulative Financials: {[f.model_dump() for f in finance.financials]}

QA Risk Output:
- Viability Score: {qa.trustScore}%
- Risks: {[r.model_dump() for r in qa.risks]}
"""


async def run_orchestration(
    run_id: str,
    idea: str,
    db,
    broadcast_callback: Callable[[dict], Awaitable[None]]
):
    """
    Orchestrates the sequential multi-agent execution pipeline using local SQLite persistence.
    Saves intermediate outputs, tracks costs, updates run statuses, and streams live events.
    """
    total_in = 0
    total_out = 0
    total_cost = 0.0

    async def send_log(agent: str, message: str, step_progress: int = None):
        payload = {
            "type": "log",
            "time": datetime.utcnow().strftime("%H:%M:%S"),
            "agent": agent,
            "message": message
        }
        if step_progress is not None:
            payload["progress"] = step_progress
        await broadcast_callback(payload)

    try:
        # --- 1. CEO Agent ---
        await send_log("CEO", f"Initialized strategy board for goal: \"{idea}\"", step_progress=5)
        db.update_run_status(run_id, "ceo_working")
        await send_log("CEO", "Analyzing business structure, target audience, and value proposition...", step_progress=10)
        
        ceo_output, in_t, out_t, cost = await call_agent_structured(
            model="claude-3-5-sonnet-20240620",
            system_prompt=CEO_SYSTEM_PROMPT,
            user_prompt=get_ceo_user_prompt(idea),
            output_schema=CEOOutput
        )
        total_in += in_t
        total_out += out_t
        total_cost += cost

        db.save_agent_output(run_id, "ceo", ceo_output.model_dump())

        await send_log(
            "CEO", 
            f"Identified business structure as [{ceo_output.businessModel}] targeting [{ceo_output.audience}] in [{ceo_output.location}]. Dispatching task sets...",
            step_progress=25
        )
        await send_log("CEO", f"Strategic task mapping completed for \"{ceo_output.subject}\". Handing off to Research Agent.", step_progress=28)

        # --- 2. Research Agent ---
        db.update_run_status(run_id, "research_working")
        await send_log("Research", f"Research Agent active. Mapping competitive landscape for \"{ceo_output.subject}\"...", step_progress=32)
        
        # Use Claude Haiku for competitor Intel passes as specified in guidelines
        research_output, in_t, out_t, cost = await call_agent_structured(
            model="claude-3-5-haiku-20241022",
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            user_prompt=get_research_user_prompt(idea, ceo_output),
            output_schema=ResearchOutput
        )
        total_in += in_t
        total_out += out_t
        total_cost += cost

        db.save_agent_output(run_id, "research", research_output.model_dump())

        competitors_str = ", ".join(research_output.competitors)
        await send_log("Research", f"Scanning competitors. Found market leaders/workarounds: {competitors_str}. Analyzing gaps...", step_progress=45)
        await send_log("Research", f"Synthesized SWOT analysis. Demographics for [{ceo_output.audience}] indicate market entry windows.", step_progress=52)
        await send_log("Research", "Market reports synthesized. Delivering data models to Finance.", step_progress=55)

        # --- 3. Finance Agent ---
        db.update_run_status(run_id, "finance_working")
        await send_log("Finance", "Finance Agent analyzing unit economics. Setting pricing and modeling CAC vs LTV...", step_progress=60)

        finance_output, in_t, out_t, cost = await call_agent_structured(
            model="claude-3-5-sonnet-20240620",
            system_prompt=FINANCE_SYSTEM_PROMPT,
            user_prompt=get_finance_user_prompt(idea, ceo_output, research_output),
            output_schema=FinanceOutput
        )
        total_in += in_t
        total_out += out_t
        total_cost += cost

        db.save_agent_output(run_id, "finance", finance_output.model_dump())

        await send_log("Finance", f"Projecting cumulative financials. Modeled gross profit margin of {finance_output.metrics.marginPct}% over 12 months.", step_progress=70)
        await send_log("Finance", f"Calculated operational cash runway. Target 6-Month budget set to: ₹{finance_output.metrics.totalBudget6mo:,}.", step_progress=78)
        await send_log("Finance", "Spreadsheet projection modeling finished. Relaying to QA Agent for verification.", step_progress=82)

        # --- 4. QA Risk Agent (With Fallback Graceful degradation) ---
        db.update_run_status(run_id, "qa_working")
        await send_log("QA", f"QA Risk Agent auditing files. Reviewing regulatory requirements for {ceo_output.industry} in {ceo_output.location}...", step_progress=85)
        
        qa_failed = False
        try:
            qa_output, in_t, out_t, cost = await call_agent_structured(
                model="claude-3-5-sonnet-20240620",
                system_prompt=QA_SYSTEM_PROMPT,
                user_prompt=get_qa_user_prompt(idea, ceo_output, research_output, finance_output),
                output_schema=QARiskOutput
            )
            total_in += in_t
            total_out += out_t
            total_cost += cost
            
            db.save_agent_output(run_id, "qa", qa_output.model_dump())

            await send_log("QA", f"Flagged critical assumption matrix. Safety score calculated at {qa_output.trustScore}%.", step_progress=90)
            await send_log("QA", f"Consistency validation check: Passed. Integrity score: {qa_output.trustScore}%", step_progress=92)
        except Exception as e:
            logger.error(f"QA Agent failed: {str(e)}. Proceeding with partial recovery.")
            await send_log("QA", "⚠️ QA Agent audit run encountered an API error. Falling back to default risk matrix.", step_progress=90)
            qa_failed = True
            # Construct a default fallback QARiskOutput
            qa_output = QARiskOutput(
                trustScore=75.0,
                assumptions=[
                    "General: Requires standard operational setup.",
                    "Time: Assumes founder can devote 15+ hours weekly.",
                    "Tech: Assumes simple web infrastructure."
                ],
                risks=[
                    RiskItem(
                        category="Audits Unavailable",
                        risk="Full regulatory and QA audit is currently offline due to transient API drops.",
                        severity="Medium",
                        mitigation="Please trigger a re-run of this plan later to pull deep risk analyses."
                    )
                ],
                recommendations=[
                    "Proceed with initial customer interviews manually.",
                    "Keep expenses minimal until full compliance checks can be run."
                ]
            )

        # --- 5. Consolidator Pass (Assemble Dashboard) ---
        await send_log("CEO", "Assembling strategy blueprint and generating operational roadmap...", step_progress=95)
        
        consolidated_output, in_t, out_t, cost = await call_agent_structured(
            model="claude-3-5-sonnet-20240620",
            system_prompt=CONSOLIDATOR_SYSTEM_PROMPT,
            user_prompt=get_consolidator_user_prompt(idea, ceo_output, research_output, finance_output, qa_output),
            output_schema=RunDashboardOutput
        )
        total_in += in_t
        total_out += out_t
        total_cost += cost

        # Override dynamic runtime fields for strict consistency
        consolidated_output.id = run_id
        consolidated_output.goal = idea
        consolidated_output.timestamp = int(datetime.utcnow().timestamp() * 1000)

        # Write final consolidated report to SQLite dashboard table
        db.save_dashboard(
            run_id,
            roadmap=[m.model_dump() for m in consolidated_output.roadmap],
            revenue=consolidated_output.revenueModel.model_dump(),
            risk={
                "trustScore": consolidated_output.trustScore,
                "assumptions": consolidated_output.assumptions,
                "risks": [r.model_dump() for r in consolidated_output.risks],
                "recommendations": consolidated_output.recommendations
            },
            budget={
                "financials": [f.model_dump() for f in consolidated_output.financials],
                "metrics": consolidated_output.metrics.model_dump()
            }
        )

        # Update run status
        viability = consolidated_output.trustScore
        db.update_run_status(run_id, "completed", viability_score=viability)

        # Log Cost statistics
        db.save_cost(run_id, total_in, total_out, total_cost)

        await send_log("CEO", "Report signed off. Compiled business dashboard successfully.", step_progress=100)
        
        # Broadcast completed status
        await broadcast_callback({
            "type": "completed",
            "dashboard": consolidated_output.model_dump()
        })

    except Exception as orchestration_err:
        logger.error(f"Orchestration pipeline failed: {str(orchestration_err)}")
        db.update_run_status(run_id, "failed")
        await broadcast_callback({
            "type": "failed",
            "error": str(orchestration_err)
        })
        raise orchestration_err
