import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import EXASearchTool, ScrapeWebsiteTool
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

# ---------- Agentcore imports --------------------
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
#------------------------------------------------

# Get the API key from environment variables
exa_api_key = os.getenv('EXA_API_KEY')  # Use the exact variable name you set in AgentCore

# Initialize with explicit parameters to avoid interactive prompts
exa_search_tool = EXASearchTool(
    api_key=exa_api_key,
    # Add any other required parameters to prevent prompts
)
# Create the ScrapeWebsiteTool instance
scrape_website_tool = ScrapeWebsiteTool()

@CrewBase
class DeepResearch():
    """DeepResearch crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    # @agent
    # def researcher(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['researcher'], # type: ignore[index]
    #         verbose=True
    #     )

    # @agent
    # def reporting_analyst(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['reporting_analyst'], # type: ignore[index]
    #         verbose=True
    #     )

    @agent
    def research_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['research_planner'], # type: ignore[index]
            verbose=True,
            max_rpm= 150,
            max_iter= 15
        )

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            tools=[exa_search_tool, scrape_website_tool],
            verbose=True,
            max_rpm=150,
            max_iter=15
        )
    
    @agent
    def fact_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['fact_checker'], # type: ignore[index]
            tools=[exa_search_tool, scrape_website_tool],
            verbose=True,
            max_rpm= 150,
            max_iter= 15
        )

    @agent
    def report_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['report_writer'], # type: ignore[index]
            verbose=True,
            max_rpm= 150,
            max_iter= 15
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    # @task
    # def research_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['research_task'], # type: ignore[index]
    #     )

    # @task
    # def reporting_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['reporting_task'], # type: ignore[index]
    #         output_file='report.md'
    #     )
    
    @task
    def create_research_plan_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_research_plan_task'], # type: ignore[index]
        )

    @task
    def gather_research_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['gather_research_data_task'], # type: ignore[index]
            output_file='report.md'
        )
    
    @task
    def verify_information_quality_task(self) -> Task:
        return Task(
            config=self.tasks_config['verify_information_quality_task'], # type: ignore[index]
        )

    @task
    def write_final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['write_final_report_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DeepResearch crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
    
# Integration with Bedrock AgentCore
@app.entrypoint
def agent_invocation(payload, context):
    """Handler for agent invocation"""
    print(f'Payload: {payload}')
    try: 
        # Extract user message from payload with default
        user_message = payload.get("topic", "Artificial Intelligence in Healthcare")
        print(f"Processing user query: {user_message}")
        
        # Create crew instance and run synchronously
        crew_instance = DeepResearch()
        crew = crew_instance.crew()
        
        # Use synchronous kickoff instead of async - this avoids all event loop issues
        result = crew.kickoff(inputs={'user_query': user_message})

        print("Context:\n-------\n", context)
        print("Result Raw:\n*******\n", result.raw)
        
        # Safely access json_dict if it exists
        if hasattr(result, 'json_dict'):
            print("Result JSON:\n*******\n", result.json_dict)
        
        return {"result": result.raw}
        
    except Exception as e:
        print(f'Exception occurred: {e}')
        return {"error": f"An error occurred: {str(e)}"}

if __name__ == "__main__":
    app.run() 
