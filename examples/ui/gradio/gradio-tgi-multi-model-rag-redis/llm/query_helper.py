from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
import os
from langchain.vectorstores.redis import Redis
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain.schema.retriever import BaseRetriever
from typing import List
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_community.vectorstores.faiss import FAISS


REDIS_URL = os.getenv('REDIS_URL')
REDIS_INDEX = os.getenv('REDIS_INDEX')

############################
# LLM chain implementation #
############################

# Document store: Redis vector store
embeddings = HuggingFaceEmbeddings()
rds = None
retriever = None

# prompt_template3 = """<s>[INST] <<SYS>>
# Instructions:
# - You are a helpful assistant in writing a project proposal for products owned by Red Hat for the company name provided in the question below.
# - Your job is to look at the  question and create the project proposal addressed to the company mentioned in question.
# - Base your answer on the provided context and question and not on prior knowledge.
# - The proposal should contain headings and sub-headings and each heading and sub-heading should be in bold.
# - Generate the project proposal in markdown language.
# - Each section in the proposal should contain only three items.
# - Proposal should be minimum of 500 lines.
# <</SYS>>

# Question: {question}
# Context: {context}

# [/INST]
# """

prompt_template = """
### [INST]
Instructions:
- You are a helpful assistant in writing a project proposal for products owned by Red Hat for the company name provided in the question below.
- Your job is to look at the  question and create the project proposal addressed to the company mentioned in question.
- Base your answer on the provided context and question and not on prior knowledge.
- The proposal should contain headings and sub-headings and each heading and sub-heading should be in bold.
- Generate the project proposal in markdown language.
- Each section in the proposal should contain only three items.
- Proposal should be minimum of 500 lines.

Here is context to help:
{context}

### QUESTION:
Question: {question}

[/INST]
"""

QA_CHAIN_PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"])

def get_qa_chain(llm):
    global rds
    global retriever
    if rds is None:
        try:
            rds = Redis.from_existing_index(
                embeddings,
                redis_url=REDIS_URL,
                index_name=REDIS_INDEX,
                schema="redis_schema.yaml"
            )
            retriever = rds.as_retriever(
                            search_type="similarity",
                            search_kwargs={"k": 4, "distance_threshold": 0.5})
        except Exception as e:
            print(e)
            print(
                "Redis server is unavailable. Project proposal will be generated without RAG content."
            )
            #TODO
            db = FAISS.from_texts(["dummy"], embeddings)
            retriever = db.as_retriever()

    return RetrievalQA.from_chain_type(
        llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        return_source_documents=True
    )
