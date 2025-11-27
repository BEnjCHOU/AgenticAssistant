from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
import asyncio
import os

# Create a RAG tool using LlamaIndex

def load_index() -> VectorStoreIndex:
    if os.path.exists("storage"):
        from llama_index.core import StorageContext, load_index_from_storage
        # load the index from disk
        print("loading index from storage folder")
        storage_context = StorageContext.from_defaults(persist_dir="storage")
        index = load_index_from_storage(storage_context)
        return index
    else:
        print("data folder used to load documents and create index")
        documents = SimpleDirectoryReader("data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        save_index_to_disk(index, persist_dir="storage")
        return index

def save_index_to_disk(index, persist_dir="storage"):
    """Saves the index to disk for persistence."""
    index.storage_context.persist(persist_dir)

def multiply(a: float, b: float) -> float:
    """Useful for multiplying two numbers."""
    return a * b


async def search_documents(query: str) -> str:
    """Useful for answering natural language questions about essays"""
    index = load_index()
    query_engine = index.as_query_engine()
    response = await query_engine.aquery(query)
    return str(response)


# Create an enhanced workflow with both tools
agent = FunctionAgent(
    tools=[multiply, search_documents],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="""You are a helpful assistant that can perform calculations
    and search through documents to answer questions.""",
)


# Now we can ask questions about the documents or do calculations
async def main():
    response = await agent.run(
        "What planet is closest to the sun? Also, what's 7 * 8?"
    )
    print(response)


# Run the agent
if __name__ == "__main__":
    asyncio.run(main())