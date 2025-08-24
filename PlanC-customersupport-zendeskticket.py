# Customer Support Automation Workflow
from portia import PlanBuilderV2, StepOutput, Input
from pydantic import BaseModel


from portia.cli import CLIExecutionHooks
from portia import tool,ToolRegistry
from portia import PlanBuilderV2, StepOutput, Input
from pydantic import BaseModel
from portia.end_user import EndUser

from typing import Tuple

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
from typing import Annotated

load_dotenv()
PORTIA_API_KEY = os.getenv("PORTIA_API_KEY")

from pathlib import Path
from typing import Annotated, Dict, List, Any, Optional
from portia import tool

@tool
def zendeskticketsshow(
    ticket_id: Annotated[str, "The Zendesk ticket ID to retrieve"]
) -> Dict[str, Any]:
    """Retrieves detailed information about a specific Zendesk ticket."""
    return {
        "ticket_id": ticket_id,
        "subject": "Mock: User cannot login to the system",
        "description": "User reports being unable to login using SSO authentication. Error occurs on Chrome browser.",
        "priority": "high",
        "status": "open",
        "category": "authentication",
        "created_at": "2025-08-24T04:30:00Z",
        "updated_at": "2025-08-24T04:45:00Z",
        "requester_id": "user_12345",
        "assignee_id": "agent_67890",
        "tags": ["login", "sso", "authentication"]
    }

@tool
def zendeskticketslistcomments(
    ticket_id: Annotated[str, "The Zendesk ticket ID to get comments for"]
) -> List[Dict[str, Any]]:
    """Retrieves all comments for a specific Zendesk ticket."""
    return [
        {
            "id": "comment_1",
            "author": "user_12345",
            "author_name": "John Doe",
            "comment": "I've been unable to login since this morning. The SSO redirect doesn't work.",
            "created_at": "2025-08-24T04:30:00Z",
            "public": True
        },
        {
            "id": "comment_2", 
            "author": "agent_67890",
            "author_name": "Support Agent Sarah",
            "comment": "Thank you for reporting this. I'm looking into the SSO configuration issue.",
            "created_at": "2025-08-24T04:35:00Z",
            "public": True
        },
        {
            "id": "comment_3",
            "author": "agent_67890",
            "author_name": "Support Agent Sarah", 
            "comment": "Internal note: Checking with IT team about recent SSO changes.",
            "created_at": "2025-08-24T04:40:00Z",
            "public": False
        }
    ]

@tool
def zendeskhelpcentersearcharticles(
    query: Annotated[str, "Search query to find relevant knowledge base articles"]
) -> List[Dict[str, Any]]:
    """Searches the Zendesk knowledge base for relevant articles."""
    return [
        {
            "id": "article_1",
            "title": "How to Reset Your Password",
            "url": "https://kb.example.com/reset-password",
            "body": "Step-by-step guide to reset your password using the self-service portal.",
            "section": "Authentication",
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-08-01T14:30:00Z"
        },
        {
            "id": "article_2",
            "title": "SSO Troubleshooting Guide", 
            "url": "https://kb.example.com/sso-troubleshooting",
            "body": "Common SSO issues and their solutions including browser compatibility.",
            "section": "Authentication",
            "created_at": "2025-02-20T09:00:00Z",
            "updated_at": "2025-07-15T11:20:00Z"
        },
        {
            "id": "article_3",
            "title": "Browser Compatibility Requirements",
            "url": "https://kb.example.com/browser-compatibility", 
            "body": "Supported browsers and configuration requirements for optimal experience.",
            "section": "Technical Requirements",
            "created_at": "2025-03-10T13:00:00Z",
            "updated_at": "2025-06-30T16:45:00Z"
        }
    ]

@tool
def zendeskuserssearch(
    query: Annotated[str, "Search query to find users/agents (e.g., 'role:agent category:authentication')"]
) -> List[Dict[str, Any]]:
    """Searches for Zendesk users and agents based on query parameters."""
    return [
        {
            "user_id": "agent_67890",
            "name": "Support Agent Sarah",
            "email": "sarah@example.com", 
            "role": "agent",
            "category": "authentication",
            "skills": ["SSO", "Authentication", "Password Recovery"],
            "active": True,
            "created_at": "2024-01-15T08:00:00Z"
        },
        {
            "user_id": "agent_11111",
            "name": "Senior Agent Mike",
            "email": "mike@example.com",
            "role": "agent", 
            "category": "authentication",
            "skills": ["Advanced SSO", "LDAP", "Security"],
            "active": True,
            "created_at": "2023-06-20T10:30:00Z"
        },
        {
            "user_id": "lead_22222",
            "name": "Team Lead Jessica",
            "email": "jessica@example.com",
            "role": "team_lead",
            "category": "authentication", 
            "skills": ["Team Management", "Escalation", "Complex Issues"],
            "active": True,
            "created_at": "2022-03-01T12:00:00Z"
        }
    ]

@tool
def zendeskticketsupdate(
    ticket_id: Annotated[str, "The Zendesk ticket ID to update"],
    update_fields: Annotated[Dict[str, Any], "Dictionary containing fields to update (status, priority, assignee_id, etc.)"],
    comment: Annotated[Optional[str], "Optional comment to add to the ticket"] = None
) -> Dict[str, Any]:
    """Updates a Zendesk ticket with new field values and optionally adds a comment."""
    print(f"Updating ticket {ticket_id} with fields: {update_fields}")
    if comment:
        print(f"Adding comment to ticket {ticket_id}: {comment}")
    
    return {
        "success": True,
        "ticket_id": ticket_id,
        "updated_fields": update_fields,
        "comment_added": bool(comment),
        "updated_at": "2025-08-24T05:00:00Z"
    }

@tool  
def zendeskticketscreate(
    subject: Annotated[str, "The subject line for the new ticket"],
    description: Annotated[str, "The detailed description of the issue"],
    priority: Annotated[str, "Ticket priority (low, normal, high, urgent)"] = "normal",
    category: Annotated[str, "Ticket category"] = "general",
    requester_email: Annotated[str, "Email of the person requesting support"] = "user@example.com"
) -> Dict[str, Any]:
    """Creates a new Zendesk support ticket."""
    new_ticket_id = f"ticket_{hash(subject + description) % 10000}"
    
    return {
        "ticket_id": new_ticket_id,
        "subject": subject,
        "description": description,
        "priority": priority,
        "category": category,
        "status": "new",
        "requester_email": requester_email,
        "created_at": "2025-08-24T05:00:00Z",
        "url": f"https://example.zendesk.com/tickets/{new_ticket_id}"
    }

@tool
def zendeskticketscount(
    status: Annotated[str, "Filter tickets by status (open, pending, solved, closed, all)"] = "all",
    priority: Annotated[Optional[str], "Filter tickets by priority (low, normal, high, urgent)"] = None,
    assignee_id: Annotated[Optional[str], "Filter tickets by assigned agent ID"] = None
) -> Dict[str, Any]:
    """Returns count of tickets matching the specified filters."""
    # Mock data based on filters
    base_count = 127
    if status != "all":
        base_count = base_count // 3
    if priority:
        base_count = base_count // 2
    if assignee_id:
        base_count = base_count // 4
        
    return {
        "total_count": base_count,
        "filters_applied": {
            "status": status,
            "priority": priority, 
            "assignee_id": assignee_id
        },
        "last_updated": "2025-08-24T05:00:00Z"
    }

@tool
def zendeskticketsshowmetrics(
    ticket_id: Annotated[str, "The Zendesk ticket ID to get metrics for"]
) -> Dict[str, Any]:
    """Returns performance metrics for a specific ticket."""
    return {
        "ticket_id": ticket_id,
        "first_response_time": "2 hours 15 minutes",
        "full_resolution_time": "1 day 4 hours", 
        "customer_satisfaction_score": 4.2,
        "reopened_count": 0,
        "agent_work_time": "45 minutes",
        "reply_count": 3,
        "created_at": "2025-08-23T10:30:00Z",  
        "resolved_at": "2025-08-24T14:30:00Z"
    }
     

my_tool_registry = ToolRegistry([
    zendeskticketsshow(),
    zendeskticketscreate(),
    zendeskticketsupdate(),
    zendeskticketslistcomments(),
    zendeskhelpcentersearcharticles(),
    zendeskuserssearch(),
])


my_config = Config.from_default(default_model="google/gemini-2.0-flash", portia_api_key=PORTIA_API_KEY)
portia = Portia(
    config=my_config,
    tools=(open_source_tool_registry +PortiaToolRegistry(my_config)+my_tool_registry),
    execution_hooks=CLIExecutionHooks(),
)



class TicketAnalysis(BaseModel):
    priority: str
    category: str
    sentiment: str
    suggested_response: str
    escalation_needed: bool

class SupportResponse(BaseModel):
    response_text: str
    follow_up_needed: bool
    knowledge_base_articles: list[str]

# Customer Support Workflow
support_plan = (
    PlanBuilderV2("Automated Customer Support Response")
    .input(
        name="ticket_id",
        description="The Zendesk ticket ID to process"
    )
    .input(
        name="response_tone",
        description="Tone for customer response (professional, friendly, empathetic)",
        default_value="professional"
    )
    
  # Step 1: Retrieve ticket details
    .invoke_tool_step(
        step_name="get_ticket",
        tool="zendeskticketsshow",
        args={
            "ticket_id": Input("ticket_id")
        }
    )
    
    # Step 2: Get ticket comments/conversation history  
    .invoke_tool_step(
        step_name="get_comments",
        tool="zendeskticketslistcomments",
        args={
            "ticket_id": Input("ticket_id")
        }
    )
    
    # Step 3: Analyze ticket content and priority
    .llm_step(
        task="Analyze the ticket content, determine priority level, category, and customer sentiment",
        inputs=[StepOutput("get_ticket"), StepOutput("get_comments")],
        output_schema=TicketAnalysis,
        step_name="analyze_ticket"
    )
    
    # Step 4: Search knowledge base for relevant articles
    .single_tool_agent_step(
        step_name="search_kb",
        tool="zendeskhelpcentersearcharticles",
        task="Find relevant help articles based on the ticket issue",
        inputs=[StepOutput("analyze_ticket")]
    )
    
    # Step 5: Check if escalation is needed
    .if_(
        condition=lambda analysis: analysis.escalation_needed == True,
        args={"analysis": StepOutput("analyze_ticket")}
    )
    
    # Step 5a: Search for appropriate team members if escalation needed
    .single_tool_agent_step(
        step_name="find_escalation_team",
        tool="zendeskuserssearch",
        task="find escalation team with the agent in the past ticket",
        inputs=[StepOutput("analyze_ticket")]
    )
    
    # Step 5b: Update ticket with escalation
    .single_tool_agent_step(
        step_name="escalate_ticket",
        tool="zendeskticketsupdate",
        task="Escalate ticket to appropriate team and update priority",
        inputs=[StepOutput("analyze_ticket"), StepOutput("find_escalation_team")]
    )
    
    .else_()
    
    # Step 6: Generate response if no escalation needed
    .llm_step(
        task=f"Generate a helpful customer response in {Input('response_tone')} tone based on ticket analysis and knowledge base articles",
        inputs=[StepOutput("analyze_ticket"), StepOutput("search_kb")],
        output_schema=SupportResponse,
        step_name="generate_response"
    )
    
    # Step 7: Create internal comment with analysis
    .function_step(
        function=lambda analysis, response: {
            "internal_note": f"Auto-analysis: Priority: {analysis.priority}, Category: {analysis.category}, Sentiment: {analysis.sentiment}",
            "customer_response": response.response_text
        },
        args={
            "analysis": StepOutput("analyze_ticket"),
            "response": StepOutput("generate_response")
        },
        step_name="prepare_updates"
    )
    
    # Step 8: Update ticket with response
    .single_tool_agent_step(
        step_name="update_ticket",
        tool="zendeskticketsupdate", 
        task="Add internal note and customer response to ticket",
        inputs=[StepOutput("prepare_updates"), Input("ticket_id")]
    )
    
    .endif()
    

    .single_tool_agent_step(
        step_name="notify_team",
        tool="portia:slack:bot:send_message",
        task="Send summary notification to support team channel named as debug",
        inputs=[StepOutput("analyze_ticket"), Input("ticket_id")]
    )
    
    .final_output(
        output_schema=TicketAnalysis,
        summarize=True
    )
    .build()
)


plan_run=portia.run_plan(support_plan, 
                plan_run_inputs={"ticket_id":"123"},
                end_user=EndUser(external_id="my_user_id_123", name="Aditya Jha"))


final_output_value = plan_run.outputs.final_output.value


final_output_summary = plan_run.outputs.final_output.summary