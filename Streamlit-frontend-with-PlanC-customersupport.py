import streamlit as st
import os
from dotenv import load_dotenv
import sys
from typing import Dict, Any, Optional

from portia import PlanBuilderV2, StepOutput, Input, tool, ToolRegistry
from pydantic import BaseModel
from portia.cli import CLIExecutionHooks
from portia.end_user import EndUser
from portia import (
    Portia, PortiaToolRegistry, default_config, Config
)
from portia import open_source_tool_registry
from typing import Annotated, List

# Load environment variables
load_dotenv()


@st.cache_resource
def initialize_portia():
    """Initialize PortiaAI components once and cache them"""
    try:
        PORTIA_API_KEY = os.getenv("PORTIA_API_KEY")
        if not PORTIA_API_KEY:
            st.error("PORTIA_API_KEY not found in environment variables")
            return None, None, None
        
        
        @tool
        def zendeskticketsshow(ticket_id: Annotated[str, "The Zendesk ticket ID to retrieve"]) -> Dict[str, Any]:
            """Retrieves detailed information about a specific Zendesk ticket."""
            return {
                "ticket_id": ticket_id,
                "subject": "Mock: User cannot login to the system",
                "description": "User reports being unable to login using SSO authentication. Error occurs on Chrome browser.",
                "priority": "high", "status": "open", "category": "authentication",
                "created_at": "2025-08-24T04:30:00Z", "updated_at": "2025-08-24T04:45:00Z",
                "requester_id": "user_12345", "assignee_id": "agent_67890",
                "tags": ["login", "sso", "authentication"]
            }

        @tool
        def zendeskticketslistcomments(ticket_id: Annotated[str, "The Zendesk ticket ID to get comments for"]) -> List[Dict[str, Any]]:
            """Retrieves all comments for a specific Zendesk ticket."""
            return [
                {"id": "comment_1", "author": "user_12345", "author_name": "John Doe",
                 "comment": "I've been unable to login since this morning. The SSO redirect doesn't work.",
                 "created_at": "2025-08-24T04:30:00Z", "public": True},
                {"id": "comment_2", "author": "agent_67890", "author_name": "Support Agent Sarah",
                 "comment": "Thank you for reporting this. I'm looking into the SSO configuration issue.",
                 "created_at": "2025-08-24T04:35:00Z", "public": True}
            ]

        @tool
        def zendeskhelpcentersearcharticles(query: Annotated[str, "Search query to find relevant knowledge base articles"]) -> List[Dict[str, Any]]:
            """Searches the Zendesk knowledge base for relevant articles."""
            return [
                {"id": "article_1", "title": "How to Reset Your Password", 
                 "url": "https://kb.example.com/reset-password",
                 "body": "Step-by-step guide to reset your password using the self-service portal.",
                 "section": "Authentication"},
                {"id": "article_2", "title": "SSO Troubleshooting Guide",
                 "url": "https://kb.example.com/sso-troubleshooting", 
                 "body": "Common SSO issues and their solutions including browser compatibility.",
                 "section": "Authentication"}
            ]

        @tool
        def zendeskuserssearch(query: Annotated[str, "Search query to find users/agents"]) -> List[Dict[str, Any]]:
            """Searches for Zendesk users and agents based on query parameters."""
            return [
                {"user_id": "agent_67890", "name": "Support Agent Sarah", "email": "sarah@example.com",
                 "role": "agent", "category": "authentication", 
                 "skills": ["SSO", "Authentication", "Password Recovery"], "active": True}
            ]

        @tool
        def zendeskticketsupdate(ticket_id: Annotated[str, "The Zendesk ticket ID to update"],
                                update_fields: Annotated[Dict[str, Any], "Dictionary containing fields to update"],
                                comment: Annotated[Optional[str], "Optional comment to add"] = None) -> Dict[str, Any]:
            """Updates a Zendesk ticket with new field values and optionally adds a comment."""
            return {"success": True, "ticket_id": ticket_id, "updated_fields": update_fields,
                   "comment_added": bool(comment), "updated_at": "2025-08-24T05:00:00Z"}

        # Create tool registry
        my_tool_registry = ToolRegistry([
            zendeskticketsshow(), zendeskticketslistcomments(), zendeskhelpcentersearcharticles(),
            zendeskuserssearch(), zendeskticketsupdate()
        ])

        
        my_config = Config.from_default(default_model="google/gemini-2.0-flash", portia_api_key=PORTIA_API_KEY)
        portia = Portia(
            config=my_config,
            tools=(open_source_tool_registry + PortiaToolRegistry(my_config) + my_tool_registry),
            execution_hooks=CLIExecutionHooks(),
        )

        # Define data models
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

        # Build workflow
        support_plan = (
            PlanBuilderV2("Automated Customer Support Response")
            .input(name="ticket_id", description="The Zendesk ticket ID to process")
            .input(name="response_tone", description="Tone for customer response", default_value="professional")
            
            .invoke_tool_step(step_name="get_ticket", tool="zendeskticketsshow", 
                            args={"ticket_id": Input("ticket_id")})
            
            .invoke_tool_step(step_name="get_comments", tool="zendeskticketslistcomments",
                            args={"ticket_id": Input("ticket_id")})
            
            .llm_step(task="Analyze the ticket content, determine priority level, category, and customer sentiment",
                     inputs=[StepOutput("get_ticket"), StepOutput("get_comments")],
                     output_schema=TicketAnalysis, step_name="analyze_ticket")
            
            .single_tool_agent_step(step_name="search_kb", tool="zendeskhelpcentersearcharticles",
                                  task="Find relevant help articles based on the ticket issue",
                                  inputs=[StepOutput("analyze_ticket")])
            
            .if_(condition=lambda analysis: analysis.escalation_needed == True,
                args={"analysis": StepOutput("analyze_ticket")})
            
            .single_tool_agent_step(step_name="find_escalation_team", tool="zendeskuserssearch",
                                  task="find escalation team with the agent in the past ticket",
                                  inputs=[StepOutput("analyze_ticket")])
            
            .single_tool_agent_step(step_name="escalate_ticket", tool="zendeskticketsupdate",
                                  task="Escalate ticket to appropriate team and update priority",
                                  inputs=[StepOutput("analyze_ticket"), StepOutput("find_escalation_team")])
            
            .else_()
            
            .llm_step(task=f"Generate a helpful customer response in professional tone based on ticket analysis and knowledge base articles",
                     inputs=[StepOutput("analyze_ticket"), StepOutput("search_kb")],
                     output_schema=SupportResponse, step_name="generate_response")
            
            .function_step(function=lambda analysis, response: {
                "internal_note": f"Auto-analysis: Priority: {analysis.priority}, Category: {analysis.category}, Sentiment: {analysis.sentiment}",
                "customer_response": response.response_text
            }, args={"analysis": StepOutput("analyze_ticket"), "response": StepOutput("generate_response")},
            step_name="prepare_updates")
            
            .single_tool_agent_step(step_name="update_ticket", tool="zendeskticketsupdate",
                                  task="Add internal note and customer response to ticket",
                                  inputs=[StepOutput("prepare_updates"), Input("ticket_id")])
            
            .endif()
            
            .final_output(output_schema=TicketAnalysis, summarize=True)
            .build()
        )

        return portia, support_plan, TicketAnalysis
    
    except Exception as e:
        st.error(f"Failed to initialize PortiaAI: {str(e)}")
        return None, None, None

def run_ticket_evaluation(ticket_id: str) -> Dict[str, Any]:
    """
    Run PortiaAI customer support workflow for ticket evaluation
    
    Args:
        ticket_id: The ticket ID to analyze
        
    Returns:
        Dictionary containing analysis results and execution details
    """
    try:
 
        portia, support_plan, TicketAnalysis = initialize_portia()
        
        if not all([portia, support_plan, TicketAnalysis]):
            return {"error": "PortiaAI initialization failed", "success": False}
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Update progress
        progress_bar.progress(20)
        status_text.text("🔍 Analyzing ticket...")
        
        # Run the workflow
        plan_run = portia.run_plan(
            support_plan, 
            plan_run_inputs={"ticket_id": ticket_id},
            end_user=EndUser(external_id="streamlit_user", name="Dashboard User")
        )
        
        progress_bar.progress(80)
        status_text.text("Processing results...")
        
        # Extract results
        final_output_value = plan_run.outputs.final_output.value
        final_output_summary = plan_run.outputs.final_output.summary
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        # Clear progress indicators after a brief pause
        import time
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "analysis": final_output_value,
            "summary": final_output_summary,
            "execution_status": "completed"
        }
        
    except Exception as e:
        return {
            "error": f"Workflow execution failed: {str(e)}",
            "success": False,
            "ticket_id": ticket_id
        }

# --- Updated Streamlit Dashboard ---
st.set_page_config(page_title="Dev-Assist Dashboard", layout="wide", page_icon="🛠️")

# CSS Styles (keeping your original styles)
st.markdown("""
<style>
body { background-color: #0E1117; color: #FFFFFF; }
h1, h2 { color: #4B8BBE; text-align: center; font-weight: 700; }
.card-button {
    background-color: #1E1E2F; color: white; border-radius: 12px; padding: 30px;
    text-align: center; font-size: 20px; font-weight: bold; border: none;
    width: 100%; height: 150px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    transition: all 0.2s ease-in-out;
}
.card-button:hover { background-color: #2A2A3C; transform: scale(1.02); }
.stTextInput>div>div>input {
    background-color: #2A2A3C; color: white; border-radius: 6px;
    padding: 0.6rem; border: 1px solid #3A3A4C;
}
.stButton>button {
    background-color: #4B8BBE; color: white; border-radius: 6px;
    padding: 0.5rem 1.2rem; font-weight: 600;
}
.stButton>button:hover { background-color: #3A7BAA; }
</style>
""", unsafe_allow_html=True)

# Dashboard Title
st.markdown("<h1>🛠️ Dev-Assist Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Session State Initialization
for key in ["checkcode_expanded", "deepsearch_expanded", "ticketeval_expanded", "docsearch_expanded"]:
    if key not in st.session_state:
        st.session_state[key] = False

def toggle_card(key):
    st.session_state[key] = not st.session_state[key]

def card_button(label, key, icon):
    return st.button(f"{icon}  {label}", key=key, use_container_width=True)

# Dummy functions for other features
def checkcode(reponame, owner):
    return f"Checked code for repo: '{reponame}', owner: '{owner}'"

def deep_search(query):
    return f"Deep search results for: '{query}'"

def internaldocsrwfwrence(search):
    return f"Internal documentation result for: '{search}'"

# 4 Card Layout
col1, col2, col3, col4 = st.columns(4)

with col1:
    if card_button("Code Check", "card1", ""):
        toggle_card("checkcode_expanded")
    if st.session_state.checkcode_expanded:
        reponame = st.text_input("Repo Name", key="reponame")
        owner = st.text_input("Owner", key="owner")
        if st.button("Run", key="go_checkcode"):
            st.success(checkcode(reponame, owner))

with col2:
    if card_button("Deep Search", "card2", ""):
        toggle_card("deepsearch_expanded")
    if st.session_state.deepsearch_expanded:
        query = st.text_input("Search Query", key="query")
        if st.button("Run", key="go_deepsearch"):
            st.success(deep_search(query))

with col3:
    if card_button("Ticket Eval", "card3", ""):
        toggle_card("ticketeval_expanded")
    if st.session_state.ticketeval_expanded:
        ticketid = st.text_input("Ticket ID", key="ticketid", placeholder="Enter ticket ID (e.g., 123)")
        if st.button("Run Analysis", key="go_ticketeval"):
            if ticketid:
                with st.spinner("Running AI-powered ticket analysis..."):
                    result = run_ticket_evaluation(ticketid)
                    
                if result["success"]:
                    st.success("Ticket analysis completed successfully!")
                    
                    # Display results in expandable sections
                    with st.expander("Analysis Results", expanded=True):
                        if result["analysis"]:
                            st.json({
                                "Priority": result["analysis"].priority,
                                "Category": result["analysis"].category, 
                                "Sentiment": result["analysis"].sentiment,
                                "Escalation Needed": result["analysis"].escalation_needed
                            })
                    
                    with st.expander("AI Summary"):
                        if result["summary"]:
                            st.write(result["summary"])
                        else:
                            st.info("No summary available")
                    
                    with st.expander("Technical Details"):
                        st.json({
                            "Ticket ID": result["ticket_id"],
                            "Execution Status": result["execution_status"],
                            "Workflow": "Automated Customer Support Response"
                        })
                        
                else:
                    st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please enter a ticket ID")

with col4:
    if card_button("Docs Ref", "card4", ""):
        toggle_card("docsearch_expanded")
    if st.session_state.docsearch_expanded:
        term = st.text_input("Search Term", key="docsearch")
        if st.button("Run", key="go_docsearch"):
            st.success(internaldocsrwfwrence(term))

# Universal Search
st.markdown("<hr><h2>🔎 Universal Search</h2>", unsafe_allow_html=True)
search_input = st.text_input("Enter search term", key="global_search", 
                           placeholder="Search across repos, tickets, and docs...")

if st.button("Search", key="global_search_button"):
    st.success(internaldocsrwfwrence(search_input))