from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore
import os
from pathlib import Path
from sqlalchemy import make_url
from models import create_document_session, table_exists_in_db, delete_document_metadata_by_doc_id

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/vectordoc")

# Connect to PGVector
url = make_url(DB_URL)

class AgentDocument:
    def __init__(self):
        # Initialize Postgres Vector Store
        self.vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="agent_vectors",
            embed_dim=1536,  # OpenAI embedding dimension
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
                "hnsw_dist_method": "vector_cosine_ops",
            },
        )
        
        self.index = self.load_or_create_index()
        
        # Initialize Agent
        # Note: FunctionAgent keeps memory in its internal state. 
        # By using a global instance in main.py, we persist this memory.
        self.agent = FunctionAgent(
            tools=[self.multiply, self.search_content],
            llm=OpenAI(model="gpt-4o-mini"),
            system_prompt="""You are a helpful assistant that can perform calculations
            and search through uploaded documents to answer questions. 
            Always check your document knowledge base first if the question is about specific files."""
        )
    
    def get_agent(self):
        return self.agent
    
    def load_or_create_index(self) -> VectorStoreIndex:
        """
        Loads the index from Postgres if it exists, otherwise creates it 
        from the data directory.
        """
        try:
            # 0. check if table exists, if not create one
            # Note thatthe real table create will have a data_ prefix.
            if table_exists_in_db("data_agent_vectors"):
                # 1. Try to load from the existing Vector Store
                index = VectorStoreIndex.from_vector_store(self.vector_store)
                print("✅ Index loaded from Postgres/pgvector.")
                return index
            else:
                # 2. If valid index not found (or first run), load from files
                print(f"⚠️ Could not load from DB. Creating new index from 'data' folder...")
                if not os.path.exists("data"):
                    print("Data folder not found...")
                    raise FileNotFoundError("Data folder not found.")
                documents = SimpleDirectoryReader("data").load_data()
                # store document_id on a separate metadata table
                create_document_session(documents)
                storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
                index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
                print("✅ New index created and persisted to Postgres.")
                return index
            
        except Exception as e:
            print(f"Error saving metadata: {e}")

    def add_file_context_to_agent(self, filepath: Path) -> bool:
        """Process a new file and insert it into the Postgres vector store."""
        if filepath.exists():
            print(f"Processing file: {str(filepath)}")
            
            documents = SimpleDirectoryReader(input_files=[filepath]).load_data()
            # store document_id on a separate metadata table
            create_document_session(documents)
            # Insert into existing index (automatically updates PGVector)
            for doc in documents:
                self.index.insert(doc)
            print(f"✅ {str(filepath)} added to vector store.")
            return True
        else:
            print(f"{str(filepath)} does not exist. Adding new file failed.")
            return False

    def update_file_context_in_agent(self, filepath: Path, doc_id: str) -> bool:
        """Update an existing file in the Postgres vector store."""
        # check if file exists
        if filepath.exists():
            print(f"Updating file: {filepath}")
            updated_documents = SimpleDirectoryReader(input_files=[filepath]).load_data()
            # Re-insert into existing doc_id (LlamaIndex handles some deduplication)
            for i in range(len(updated_documents)):
                updated_documents[i].doc_id = doc_id  # ensure we use the same doc_id
                print(f"setting document id to : {doc_id} for updating same data.")
                # refresh the index, since we are not directly inserting text
                self.index.update_ref_doc(updated_documents[i])
            print(f"✅ {str(filepath)} updated in vector store.")
            # update DocumentMetadata table
            create_document_session(updated_documents)
            print(f"✅ {str(filepath)} updated in document metadata.")
            return True
        else:
            print(f"{str(filepath)} does not exist. Updating file failed.")
            return False
    
    def delete_file_context_in_agent(self, doc_id: str) -> bool:
        """Delete a file from the Postgres vector store using its doc_id."""
        try:
            self.index.delete_ref_doc(doc_id)
            print(f"✅ Document with doc_id: {doc_id} deleted from vector store.")
            delete_document_metadata_by_doc_id(doc_id)
            print(f"✅ Document metadata with doc_id: {doc_id} deleted from database.")
            return True
        except Exception as e:
            print(f"Error deleting document with doc_id: {doc_id}; {e}")
            return False

    def multiply(self, a: float, b: float) -> float:
        """Useful for multiplying two numbers."""
        return a * b

    async def search_content(self, query: str) -> str:
        """Useful for answering natural language questions about essays/files."""
        query_engine = self.index.as_query_engine()
        response = await query_engine.aquery(query)
        return str(response)
