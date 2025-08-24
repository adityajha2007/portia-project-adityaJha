from portia import PlanBuilderV2, StepOutput, Input
from pydantic import BaseModel
from portia.end_user import EndUser

from typing import Tuple
from portia.cli import CLIExecutionHooks
from dotenv import load_dotenv
from portia import (
    ActionClarification,
    InputClarification,
    MultipleChoiceClarification,
    PlanRunState,
    Portia,
    PortiaToolRegistry,
    default_config,
    Config
)
from portia import open_source_tool_registry
import os


from portia import PlanBuilderV2, StepOutput, Input
from pydantic import BaseModel

load_dotenv()
PORTIA_API_KEY = os.getenv("PORTIA_API_KEY")

my_config = Config.from_default(default_model="google/gemini-2.0-flash", portia_api_key=PORTIA_API_KEY)
portia = Portia(
    config=my_config,
    tools=(open_source_tool_registry +PortiaToolRegistry(my_config)),
    execution_hooks=CLIExecutionHooks(),
)

class RagLinearInsight(BaseModel):
    rag_search_results: list
    linear_issues: list
    matched_issues: list
    recommendations: list
    new_tasks_created: int
    project_summary: str

rag_linear_plan = (
    PlanBuilderV2("Cloudflare AutoRAG and Linear Integrated Knowledge & Issue Management")
    .input(name="search_query", description="Semantic search query to find knowledge and related issues")
    .input(name="linear_project_id", description="Linear project ID to filter issues")
    
    # Step 1: List existing AutoRAG knowledge collections
    .invoke_tool_step(
        step_name="list_rags",
        tool="portia:mcp:autorag.mcp.cloudflare.com:list_rags",
        args={}
    )
    
    # Step 2: Perform semantic AI search on AutoRAG knowledge base
    .invoke_tool_step(
        step_name="autorag_ai_search",
        tool="portia:mcp:autorag.mcp.cloudflare.com:ai_search",
        args={"query": Input("search_query")}
    )
    
    # Step 3: List issues from Linear filtered by project ID
    .invoke_tool_step(
        step_name="list_linear_issues",
        tool="portia:mcp:mcp.linear.app:list_issues",
        args={"projectId": Input("linear_project_id"), "filter": "state:unstarted;state:started"}
    )
    
    # Step 4: LLM step to match AutoRAG search results to Linear issues semantically
    .llm_step(
        task="Match AutoRAG knowledge search results with Linear issues by semantic similarity and content relevance",
        inputs=[StepOutput("autorag_ai_search"), StepOutput("list_linear_issues")],
        output_schema=RagLinearInsight,
        step_name="match_rag_to_linear"
    )
    
    # Step 5: Create new Linear issues for unmatched/important AutoRAG insights
    .single_tool_agent_step(
        step_name="create_linear_tasks_for_new_insights",
        tool="portia:mcp:mcp.linear.app:create_issue",
        task="Create Linear issues for AutoRAG search results not covered by existing issues",
        inputs=[StepOutput("match_rag_to_linear")]
    )
    
    # Step 6: Generate summary report of findings and recommendations
    .llm_step(
        task="Generate categorized summary report of knowledge base insights, matching Linear issues, and new tasks created with prioritized recommendations for the team",
        inputs=[StepOutput("match_rag_to_linear")],
        output_schema=RagLinearInsight,
        step_name="generate_summary_report"
    )
    
    # Step 7: Final output returning summary and task creation count
    .final_output(output_schema=RagLinearInsight, summarize=True)
    
    .build()
)

plan_run=portia.run_plan(rag_linear_plan, 
                plan_run_inputs={"search_query": "connec your tools","linear_project_id":"portiatest"},
                end_user=EndUser(external_id="my_user_id_123", name="Aditya Jha"))


final_output_value = plan_run.outputs.final_output.value
print(final_output_value)

final_output_summary = plan_run.outputs.final_output.summary
print(final_output_value)