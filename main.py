from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_response import InterviewResponse
from tools import search_tool

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")

parser = PydanticOutputParser(pydantic_object=InterviewResponse)
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a job interviewer. Please become an interviewer of a coding job\n{format_instructions}.
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("user", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions)

tools = [search_tool]
agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=[])

agent_executor = AgentExecutor(agent=agent, tools=[], verbose=True)
query = input("What can i help you?")
raw_response = agent_executor.invoke({"query": query})
print("raw response...\n", raw_response)

try:
    structured_response = parser.parse(raw_response.get("output"))
    print(structured_response)
except Exception as e:
    print("error while parsing response", e)
