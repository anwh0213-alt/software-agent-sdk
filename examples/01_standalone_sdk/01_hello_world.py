import os

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool


llm = LLM(
    # model=os.getenv("LLM_MODEL", "openhands/claude-sonnet-4-5-20250929"),
    model=os.getenv("LLM_MODEL", "litellm_proxy/deepseek-chat"),
    api_key=os.getenv("LLM_API_KEY", "abc"),
    base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:4000"),
)

agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

cwd = os.getcwd()
conversation = Conversation(agent=agent, workspace=cwd)

conversation.send_message("Write 3 facts about the current project into FACTS.txt.")
conversation.run()
print("All done!")
