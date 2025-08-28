import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import display, Image
from openai import OpenAI
from dotenv import load_dotenv


#Vnexpress scraper
from vnexpress import get_articles
url = "https://vnexpress.net/"
article = get_articles(url)[0]


#load api key here (remember to have .env file contains this key)

load_dotenv()

#here we can switch to other provider such as anthropic, ....

# api_key = os.getenv("OPENAI_API_KEY")
# if api_key is None:
#     raise ValueError("OPENAI_API_KEY environment variable not found")
# os.environ["OPENAI_API_KEY"] = api_key
base_url = os.getenv("openrouter_url")
api_key = os.getenv("api_key")
client = OpenAI(
  base_url = base_url,
  api_key = api_key,
)

#Insert system prompt
system_prompt = '''
    This is system prompt, you will do the following:
    1. Answer the user in their corrsponding language (such as Vietnamese, French, ...). Answer in that language only !
    2. When processing a text, only use the content from the given text, do not make up anything new.
    3. Only do what the user ask, do not hallucinate or given out of context answer.
    In your answer, do not mention about this prompt, now the user will ask their question: \n

'''
def call_llm(user_content:str):
    completion = client.chat.completions.create(
        extra_body={},
        model="deepseek/deepseek-r1-0528-qwen3-8b:free",
        messages=[{
            "role": "system",
            "content" : f"{system_prompt}"
            },
                  
            {
            "role": "user",
            "content": f"{user_content}"
            }
        ]
    )
    return completion.choices[0].message.content.strip()

#Building the pipeline

#Define State class to hold the workflow data and initialize the ChatOpenAI model

class State(TypedDict):
    text: str
    classification: str
    entities: List[str]
    summary: str

# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

#define node functions

#in langgraph, each node connected to other nodes to form a graph

#so it it suitable to build multi-agents systems and workflow

#moreover, langgraph allows for loop and revisited previous states of the graph, unlike directed acyclic graph (DAG) structure in langchain

def classification_node(state:State):
    '''Classify the text into one of the categories: News, Blog, Research, or Other '''

    user_content = f"Classify the following text into one of the categories: News, Blog, Research, or Other.\n\nText: {state['text']}\n\nCategory:"
    
    classification = call_llm(user_content)
    return {"classification": classification}

def entity_extraction_node(state: State):
    '''Extract the entities (Person, Organization, Location) from the text '''
    user_content = f"Extract the entities (Person, Location, Organization) from the following text. Give the result as a comma-separated list only (For example: Entity 1, Entity 2, ...).\n\nText: {state['text']}\n\nEntities:"
    
    entities = call_llm(user_content)
    return {"entities": entities}
def summarization_node(state: State):
    '''Summarize the text in one short sentence'''
    user_content = f"Summarize the following text.\n\nText: {state['text']}\n\nSummarize text:"
    
    summary = call_llm(user_content)
    return {"summary": summary}

#create tools and build workflow

workflow = StateGraph(State)

#add nodes (components) to the graph
workflow.add_node("classification_node", classification_node)
workflow.add_node("entities_extraction", entity_extraction_node)
workflow.add_node("summarization", summarization_node)

#add edges (how the state is passed through the graph)
workflow.set_entry_point("classification_node") #this is the entry point of the graph
#the text will enter this node first
workflow.add_edge("classification_node", "entities_extraction")
workflow.add_edge("entities_extraction", "summarization")
workflow.add_edge("summarization", END)

#compile the graph
app = workflow.compile()

sample_text = """
OpenAI has announced the GPT-4 model, which is a large multimodal model that exhibits human-level performance on various professional benchmarks. It is developed to improve the alignment and safety of AI systems.
additionally, the model is designed to be more efficient and scalable than its predecessor, GPT-3. The GPT-4 model is expected to be released in the coming months and will be available to the public for research and development purposes.
"""

vietnamese_sample_text = """
Từ sáng sớm nay, hàng trăm người mang áo mưa, chiếu, đồ ăn và nước uống đổ về các tuyến đường quanh quảng trường Ba Đình chờ xem sơ duyệt diễu binh diễu hành.

Theo Trung tâm Dự báo Khí tượng Thủy văn Quốc gia, hôm nay 27/8, Hà Nội có mưa vừa, mưa to, kèm giông, cục bộ có nơi mưa rất to. Từ chiều, lượng mưa giảm dần. 
Trong cơn giông có khả năng xảy ra lốc, sét, gió giật mạnh. 
Nhiệt độ thấp nhất 23-25 độ C, cao nhất 28-30 độ C."""

vn_express_sample_text = article['content']
state_input = {"text": vn_express_sample_text}
result = app.invoke(state_input)

# print("Classification:", result["classification"])
# print("\nEntities:", result["entities"])
print(f"\nArticle URL:{article['url']}")
print("\nSummary:", result["summary"])