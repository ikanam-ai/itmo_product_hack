import os
import time
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_community.chat_models.ollama import ChatOllama

import os

load_dotenv()

MONGO_USERNAME = os.getenv('MONGO_INITDB_ROOT_USERNAME')
MONGO_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PORT = os.getenv('MONGO_INITDB_ROOT_PORT')

mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
client = MongoClient(mongo_uri)
db = client['llm_database']
collection = db['dataset_ai']


# Настройки модели
llm_name = "qwen2:72b-instruct-q4_0"
num_ctx = 8192

llm = ChatOllama(
    model=llm_name,
    temperature=0,
    num_ctx=num_ctx,
).with_retry(
    retry_if_exception_type=(ValueError, TimeoutError),
    wait_exponential_jitter=True,
    stop_after_attempt=3,
)
class DataExtractionSchema(BaseModel):
    response_class: str = Field()
    date: str = Field()
    contacts: str = Field()
    need_more_info: str = Field()
    need_image: str = Field()
    model_response: str = Field()

class OutputSchema(BaseModel):
    response_class: str
    date: str
    contacts: str
    need_more_info: str
    need_image: str
    model_response: str

def read_system_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    return system_prompt

# Чтение файла
system_message = read_system_prompt("system_ptompt.txt")

# Шаблон для запроса к модели
template = """\
Документ:
{input}\
"""

final_prompt_template = PromptTemplate.from_template(template)
chat_prompt_template = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=system_message),
        HumanMessagePromptTemplate(prompt=final_prompt_template),
    ]
)

# Создаем цепочку
chain = chat_prompt_template | llm | JsonOutputParser()


def generate_response(prompt, model):
    try:
        response = chain.invoke(prompt)
        return response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def process_tasks():
    while True:
        task = collection.find_one_and_update(
            {"status": "pending"},
            {"$set": {"status": "processing"}}
        )
        if task:
            print(f"Processing task with id: {task['_id']}")
            prompt = task['prompt']
            model = task['model']
            try:
                response = generate_response(prompt, model)
                if response:
                    collection.update_one(
                        {"_id": task['_id']},
                        {"$set": {"status": "completed", "response": response}}
                    )
                    print(f"Completed task with id: {task['_id']}")
                else:
                    raise Exception("Failed to get a valid response from the API")
            except Exception as e:
                collection.update_one(
                    {"_id": task['_id']},
                    {"$set": {"status": "failed", "error": str(e)}}
                )
                print(f"Failed task with id: {task['_id']} - Error: {e}")
        else:
            print("No pending tasks. Waiting for new tasks...")
            time.sleep(5)

if __name__ == "__main__":
    process_tasks()
