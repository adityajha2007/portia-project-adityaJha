from portia import PlanBuilderV2, StepOutput, Input
from pydantic import BaseModel
from portia.end_user import EndUser
from portia.open_source_tools.registry import open_source_tool_registry
from typing import Tuple
from portia.open_source_tools.browser_tool import BrowserTool
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

load_dotenv()
PORTIA_API_KEY = os.getenv("PORTIA_API_KEY")

my_config = Config.from_default(default_model="google/gemini-2.0-flash", portia_api_key=PORTIA_API_KEY)
portia = Portia(
    config=my_config,
    tools=(open_source_tool_registry +PortiaToolRegistry(my_config)+BrowserTool())
)

class ResearchResult(BaseModel):
    summary: str
    key_findings: list[str]
    sources: list[str]

class DocumentContent(BaseModel):
    title: str
    content: str
    formatted_document: str

# Research and Documentation Workflow
research_plan = (
    PlanBuilderV2("Comprehensive Research and Documentation")
    .input(
        name="research_topic", 
        description="The topic to research thoroughly"
    )
    .input(
        name="output_format",
        description="Format for the final document (report, presentation, etc.)",
        default_value="report"
    )
    
    # Step 1: Web search for initial information
    .invoke_tool_step(
        step_name="web_search",
        tool="search_tool",
        args={
            "search_query": f"comprehensive information about {Input('research_topic')}"
        }
    )
    
    # Step 2: Deep dive with browser tool for specific sources
    .single_tool_agent_step(
        step_name="deep_research",
        tool="browser_tool",
        task="Visit top sources from search results and extract detailed information",
        inputs=[StepOutput("web_search")]
    )
    
    # Step 3: Analyze and synthesize findings
    .llm_step(
        task="Analyze all research data and create comprehensive findings summary",
        inputs=[StepOutput("web_search"), StepOutput("deep_research")],
        output_schema=ResearchResult,
        step_name="analyze_research"
    )
    
    # Step 4: Create structured document
    .llm_step(
        task=f"Create a well-structured {Input('output_format')} document based on research findings",
        inputs=[StepOutput("analyze_research"), Input("research_topic")],
        output_schema=DocumentContent,
        step_name="create_document"
    )
    # .llm_step(
    #     task=f"Create a well-structured {Input('output_format')} document based on research findings",
    #     inputs=[StepOutput("analyze_research"), Input("research_topic")],
    #     output_schema=DocumentContent,
    #     step_name="create_document"
    # )
    
    # Step 5: Save document to file
    .invoke_tool_step(
        step_name="save_document",
        tool="file_writer_tool",
        args={
            "filename": f"research_{Input('research_topic')}.md",
            "content": str(StepOutput("create_document"))
        }
    )
    
  #  Step 6: Upload to Google Drive
    .single_tool_agent_step(
        step_name="upload_to_drive",
        tool="portia:google:drive:search",
        task="Upload the research document to Google Drive in appropriate folder",
        inputs=[StepOutput("save_document")]
    )
    
    .final_output(
        output_schema=DocumentContent,
        summarize=True
    )
    .build()
)

plan_run=portia.run_plan(research_plan, 
                plan_run_inputs={"research_topic": "portiaAI"},
                end_user=EndUser(external_id="my_user_id_123", name="Aditya Jha"))


final_output_value = plan_run.outputs.final_output.value
print(final_output_value)
final_output_summary = plan_run.outputs.final_output.summary
print(final_output_value)