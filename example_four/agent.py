from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
import asyncio
import os
from pathlib import Path

# Create a RAG tool using LlamaIndex

class AgentDocument:
    def __init__(self):
        self.agent = FunctionAgent(
            tools=[self.multiply, self.search_content],
            llm=OpenAI(model="gpt-4o-mini"),
            system_prompt="""You are a helpful assistant that can perform calculations
            and search through documents to answer questions.""",
        )
        self.index = self.load_index()
    
    def get_agent(self):
        return self.agent

    def load_index(self) -> VectorStoreIndex:
        if os.path.exists("storage"):
            from llama_index.core import StorageContext, load_index_from_storage
            # load the index from disk
            print("loading index from storage folder")
            storage_context = StorageContext.from_defaults(persist_dir="storage")
            index = load_index_from_storage(storage_context)
            return index
        else:
            # will run this block only once to create the index
            print("data folder used to load documents and create index")
            documents = SimpleDirectoryReader("data").load_data()
            index = VectorStoreIndex.from_documents(documents)
            self.save_index_to_disk(index, persist_dir="storage")
            return index

    def add_file_context_to_agent(self, filename: str):
        filepath = Path("data") / filename
        document = SimpleDirectoryReader(filepath).load_data()
        index = VectorStoreIndex.from_documents(document)
        self.save_index_to_disk(index, persist_dir="storage")

    def save_index_to_disk(self, index, persist_dir="storage"):
        """Saves the index to disk for persistence."""
        index.storage_context.persist(persist_dir)

    def multiply(self, a: float, b: float) -> float:
        """Useful for multiplying two numbers."""
        return a * b

    async def search_content(self, query: str) -> str:
        """Useful for answering natural language questions about essays"""
        query_engine = self.index.as_query_engine()
        response = await query_engine.aquery(query)
        return str(response)
    
    # access index metadata
    def get_index_metadata(self):
        return self.index.ref_doc_info
    
    # get document id based on filename
    def get_document_id(self, filename: str):
        metadatalist = self.get_index_metadata()
        for doc_id in metadatalist["docstore/metadata"]:
            if metadatalist["docstore/ref_doc_info"][doc_id]["metadata"]["file_name"] == filename:
                return doc_id
        return None
    
    # delete file from data directory
    def delete_file(self, filename: str):
        filepath = Path("data") / filename
        if filepath.exists():
            os.remove(filepath)
        else:
            print("The file does not exist.")

    # delete document in vector
    def delete_document(self, filename: str):
        doc_id = self.get_document_id(filename)
        if doc_id == None:
            print("Document not found in index.")
            return
        self.index.delete_ref_doc(doc_id, delete_from_docstore=True)
        # delete file
        self.delete_file(filename)

    # update document in vector
    def update_document(self, filepath: str):
        # first update the document in data directory
        # this will be done on upload_function()
        # since LlamaIndex provides an update function that handles the complex 
        # process of removing old data and replacing it with new, chunked data. 
        # This is typically done when the content of an original source file has changed.
        
        # load the data
        # 1. Load the updated document from the source file path
        updated_documents = SimpleDirectoryReader(
            input_files=[filepath]
        ).load_data()

        # 2. Insert the updated document into the index
        # LlamaIndex handles the 'update' logic automatically
        # by comparing the new and old document hashes.
        print("Updating the document and its associated nodes...")
        self.index.insert(updated_documents[0])



# Now we can ask questions about the documents or do calculations
async def main():
    agentdoc = AgentDocument()
    agent = agentdoc.get_agent()
    response = await agent.run(
        "What planet is closest to the sun? Also, what's 7 * 8?"
    )
    print(response)


# Run the agent
if __name__ == "__main__":
    asyncio.run(main())