from portia import PlanBuilderV2, StepOutput, Input
from pydantic import BaseModel
from portia.end_user import EndUser
from typing import Tuple, List, Dict, Any, Optional
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
from portia.cli import CLIExecutionHooks

load_dotenv()
PORTIA_API_KEY = os.getenv("PORTIA_API_KEY")

my_config = Config.from_default(default_model="google/gemini-2.0-flash", portia_api_key=PORTIA_API_KEY)
portia = Portia(
    config=my_config,
    tools=(open_source_tool_registry + PortiaToolRegistry(my_config)),
    execution_hooks=CLIExecutionHooks(),
)

# Data Models
class CommitSha(BaseModel):
    sha: str
    message: str

class FileInfo(BaseModel):
    path: str
    content: str
    sha: str
    name: str

class CodeAnalysisResult(BaseModel):
    issues_found: int
    code_smells: List[str]
    dead_code_files: List[str]
    refactor_suggestions: List[str]
    complexity_score: float
    maintainability_rating: str
    analyzed_files: List[str]

class FileFix(BaseModel):
    file_path: str
    original_content: str
    fixed_content: str
    file_sha: str
    changes_made: List[str]

class CodeQualityReport(BaseModel):
    summary: str
    critical_issues: List[str]
    recommendations: List[str]
    fixed_issues: List[str]
    files_analyzed: int
    files_fixed: int

class ListWrapper(BaseModel):
    file_paths: List[str]

class FileInfoList(BaseModel):
    files: List[FileInfo]

class BranchInfo(BaseModel):
    branch_name: str
    created: bool

#classes
code_quality_plan = (
    PlanBuilderV2("Automated Code Quality Analysis and Maintenance")
    .input(
        name="repository_name",
        description="GitHub repository to analyze for code quality",
        default_value="securityexample"
    )
    .input(
        name="repository_owner",
        description="Repository owner (username or org)",
        default_value="adityajha2007"
    )
    .input(
        name="branch_name",
        description="Branch to analyze",
        default_value="main"
    )
    .input(
        name="language",
        description="Primary programming language (python, javascript, java, etc.)",
        default_value="python"
    )
    
    # Step 1: Get recent commits for change analysis
    .single_tool_agent_step(
        step_name="get_recent_commits",
        task="Fetch the latest commit from the repository",
        tool="portia:mcp:api.githubcopilot.com:list_commits",
        inputs=[Input("repository_owner"), Input("repository_name"), Input("branch_name")]
    )
    
    # Step 2: Extract latest commit SHA
    .llm_step(
        step_name="get_latest_commit",
        task="Extract SHA of the latest commit",
        inputs=[StepOutput("get_recent_commits")],
        output_schema=CommitSha
    )
    
    # Step 3: Get repository file tree to find all files
    .single_tool_agent_step(
        step_name="get_repo_tree",
        task="Get repository file tree to find all source code files",
        tool="portia:mcp:api.githubcopilot.com:search_code",
        inputs=[Input("repository_owner"), Input("repository_name"), Input("language")]
    )
    
    # Step 4: Extract file paths from repo tree
    .llm_step(
        step_name="extract_file_paths",
        task="Extract file paths for source code files that need analysis",
        inputs=[StepOutput("get_repo_tree")],
        output_schema=ListWrapper
    )
    
    # Step 5: Get file contents with SHA information
    .single_tool_agent_step(
        step_name="get_file_contents_with_sha",
        task="Fetch file contents along with SHA information for each file",
        tool="portia:mcp:api.githubcopilot.com:get_file_contents", 
        inputs=[
            Input("repository_owner"), 
            Input("repository_name"), 
            Input("branch_name"), 
            StepOutput("extract_file_paths")
        ]
    )
    
    # Step 6: Structure file information
    .llm_step(
        step_name="structure_file_info",
        task="Structure file information including path, content, and SHA for each file",
        inputs=[StepOutput("get_file_contents_with_sha"), StepOutput("extract_file_paths")],
        output_schema=FileInfoList
    )
    
    # Step 7: Analyze code quality
    .llm_step(
        step_name="analyze_code_quality", 
        task="Perform comprehensive code quality analysis including: dead code detection, code smells, complexity analysis, maintainability assessment, and refactoring opportunities",
        inputs=[StepOutput("structure_file_info")],
        output_schema=CodeAnalysisResult
    )
    
    # Step 8: Check if critical issues found
    .if_(
        condition=lambda analysis: analysis.issues_found > 10 or analysis.complexity_score > 7.0,
        args={"analysis": StepOutput("analyze_code_quality")}
    )
    
    # Step 8a: Create high-priority issue for critical problems
    .single_tool_agent_step(
        step_name="create_critical_issue",
        tool="portia:mcp:api.githubcopilot.com:create_issue",
        task="Create GitHub issue for critical code quality problems requiring immediate attention. Be descriptive about the issues found.",
        inputs=[
            StepOutput("analyze_code_quality"), 
            Input("repository_owner"), 
            Input("repository_name")
        ]
    )
    
    .endif()
    
    # Step 9: Generate automated fixes for each file
    .llm_step(
        step_name="generate_file_fixes",
        task="Generate specific code fixes for each file, mapping fixes to file paths with their SHA information",
        inputs=[StepOutput("analyze_code_quality"), StepOutput("structure_file_info")],
        output_schema=FileInfoList
    )
    
    # Step 10: Create branch for automated fixes
    .single_tool_agent_step(
        step_name="create_fix_branch",
        tool="portia:mcp:api.githubcopilot.com:create_branch",
        task="Create new branch for automated code quality fixes",
        inputs=[Input("repository_owner"), Input("repository_name"), Input("branch_name")]
    )
    
    # Step 11: Get fresh file contents from the new branch (CRITICAL FIX)
    .single_tool_agent_step(
        step_name="get_fresh_file_contents",
        task="Get fresh file contents and SHAs from the newly created branch to ensure correct SHA values for updates",
        tool="portia:mcp:api.githubcopilot.com:get_file_contents",
        inputs=[
            Input("repository_owner"),
            Input("repository_name"),
            StepOutput("create_fix_branch"),  # Use the new branch name
            StepOutput("extract_file_paths")
        ]
    )
    
    # Step 12: Structure fresh file information with correct SHAs
    .llm_step(
        step_name="structure_fresh_file_info",
        task="Structure fresh file information with correct SHAs from the new branch and merge with the fixed content from generate_file_fixes",
        inputs=[
            StepOutput("get_fresh_file_contents"), 
            StepOutput("generate_file_fixes"),
            StepOutput("extract_file_paths")
        ],
        output_schema=FileInfoList
    )
    
    # Step 13: Update files with fixes using fresh SHAs
    .single_tool_agent_step(
        step_name="update_files_with_fixes",
        tool="portia:mcp:api.githubcopilot.com:create_or_update_file",
        task="Update each file in the new branch with the improved code and fixes using the fresh SHA values from the new branch",
        inputs=[
            StepOutput("create_fix_branch"),
            StepOutput("generate_file_fixes"),
            StepOutput("structure_fresh_file_info"), 
            Input("repository_owner"),
            Input("repository_name"),
            StepOutput("analyze_code_quality")
        ]
    )
    
    # Step 14: Create pull request for fixes
    .single_tool_agent_step(
        step_name="create_quality_pr",
        tool="portia:mcp:api.githubcopilot.com:create_pull_request",
        task="Create a pull request from the fixes branch to the main branch with detailed description of changes made",
        inputs=[
            StepOutput("create_fix_branch"),
            Input("repository_owner"),
            Input("repository_name"),
            Input("branch_name"),
            StepOutput("structure_fresh_file_info")
        ]
    )
    
    # Step 15: Request review for the pull request
    .single_tool_agent_step(
        step_name="create_pr_review_request",
        tool="portia:mcp:api.githubcopilot.com:create_pending_pull_request_review",
        task="Request the repository owner to review the pull request with automated code quality fixes",
        inputs=[
            StepOutput("create_quality_pr"),
            Input("repository_owner"),
            Input("repository_name")
        ]
    )
    
    # Step 16: Generate comprehensive quality report
    .llm_step(
        step_name="generate_quality_report",
        task="Create detailed code quality report with metrics, issues found, fixes applied, and recommendations",
        inputs=[
            StepOutput("analyze_code_quality"), 
            StepOutput("structure_fresh_file_info"),
            StepOutput("create_quality_pr")
        ],
        output_schema=CodeQualityReport
    )
    .single_tool_agent_step(
        step_name="notify_team",
        tool="portia:slack:bot:send_message",
        task="Send summary report to channel #debug or #support ",
        inputs=[StepOutput("generate_quality_report"),Input('repository_name')]
    )
    
    # Step 17: Save report to file
    .invoke_tool_step(
        step_name="save_quality_report",
        tool="file_writer_tool",
        args={
            "filename": f"code_quality_report_{Input('repository_name')}.md",
            "content": str(StepOutput("generate_quality_report"))
        }
    )
    
    .final_output(
        output_schema=CodeQualityReport,
        summarize=True
    )
    .build()
)

# Execute the plan
plan_run = portia.run_plan(
    code_quality_plan, 
    plan_run_inputs={
        "repository_name": "securityexample",
        "repository_owner": "adityajha2007"
    },
    end_user=EndUser(external_id="adityajha", name="Aditya Jha")
)

final_output_value = plan_run.outputs.final_output.value
final_output_summary = plan_run.outputs.final_output.summary

print("Final Output Summary:")
print(final_output_summary)
print("\nFinal Output Value:")
print(final_output_value)