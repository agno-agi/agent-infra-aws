"""AgentOS Demo"""

import asyncio
from pathlib import Path

from agno.os import AgentOS

from agents.agno_assist import agno_assist
from agents.web_agent import web_agent
from teams.multilingual_team import multilingual_team
from teams.reasoning_finance_team import reasoning_research_team
from workflows.investment_workflow import investment_workflow
from workflows.research_workflow import research_workflow

os_config_path = str(Path(__file__).parent.joinpath("config.yaml"))

# Create the AgentOS
agent_os = AgentOS(
    os_id="agentos-demo",
    agents=[web_agent, agno_assist],
    teams=[multilingual_team, reasoning_research_team],
    workflows=[investment_workflow, research_workflow],
    # Configuration for the AgentOS
    config=os_config_path,
)
app = agent_os.get_app()

if __name__ == "__main__":
    # Add knowledge to Agno Assist agent
    asyncio.run(
        agno_assist.knowledge.add_content_async(  # type: ignore
            name="Agno Docs",
            url="https://docs.agno.com/llms-full.txt",
        )
    )
    # Simple run to generate and record a session
    agent_os.serve(app="main:app", reload=True)
