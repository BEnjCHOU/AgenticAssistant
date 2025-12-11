from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore
import os
from pathlib import Path
from sqlalchemy import make_url
from models import create_document_session, table_exists_in_db, delete_document_metadata_by_doc_id
from mcp_tools import mcp_registry, create_llamaindex_tool_from_mcp
from context_evaluator import ContextEvaluator

DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/vectordoc")

# Connect to PGVector
url = make_url(DB_URL)

# Fine-tuned system prompts for different task types
TASK_PROMPTS = {
    "default": """You are a helpful assistant that can perform calculations
    and search through uploaded documents to answer questions. 
    Always check your document knowledge base first if the question is about specific files.
    Use available MCP tools when appropriate to enhance your capabilities.""",
    
    "document_analysis": """You are a specialized document analysis assistant. Your primary role is to:
    1. Thoroughly analyze uploaded documents
    2. Extract key information, themes, and insights
    3. Provide detailed summaries and comparisons
    4. Answer questions with specific references to document content
    5. Use MCP tools to access file contents when needed
    
    Always prioritize accuracy and cite specific sections when possible.""",
    
    "research": """You are a research assistant with access to multiple information sources. Your capabilities include:
    1. Searching through your document knowledge base
    2. Using web search tools for current information
    3. Synthesizing information from multiple sources
    4. Providing well-structured, cited responses
    
    Always verify information and indicate your confidence level.""",
    
    "calculation": """You are a calculation assistant. Your role is to:
    1. Perform accurate mathematical calculations
    2. Use the calculator tool for complex expressions
    3. Explain your calculation steps
    4. Verify results when appropriate
    
    Always show your work and double-check calculations.""",
    
    "general": """You are an intelligent assistant with access to:
    - A document knowledge base (vector store)
    - File system operations (via MCP tools)
    - Web search capabilities
    - Mathematical calculation tools
    
    Use the most appropriate tools for each task. Always provide clear, accurate, and helpful responses."""
}


class AgentDocument:
    def __init__(self, task_type: str = "default"):
        """
        Initialize the agent with MCP tools and fine-tuned prompts.
        
        Args:
            task_type: Type of task to optimize for. Options:
                - "default": General purpose
                - "document_analysis": Focus on document analysis
                - "research": Focus on research tasks
                - "calculation": Focus on calculations
                - "general": General purpose with all tools
        """
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
        
        # Initialize context evaluator
        self.context_evaluator = ContextEvaluator()
        
        # Get fine-tuned system prompt
        system_prompt = TASK_PROMPTS.get(task_type, TASK_PROMPTS["default"])
        
        # Build tools list: base tools + MCP tools
        tools = [self.multiply, self.search_content]
        
        # Add MCP tools
        for mcp_tool_name in mcp_registry.tools.keys():
            mcp_tool = mcp_registry.get_tool(mcp_tool_name)
            llamaindex_tool = create_llamaindex_tool_from_mcp(mcp_tool)
            tools.append(llamaindex_tool)
        
        # Initialize Agent with fine-tuned prompt and MCP tools
        self.agent = FunctionAgent(
            tools=tools,
            llm=OpenAI(model="gpt-4o-mini"),
            system_prompt=system_prompt
        )
        
        self.task_type = task_type
        print(f"✅ Agent initialized with task type: {task_type}")
        print(f"✅ MCP tools registered: {list(mcp_registry.tools.keys())}")
    
    def get_agent(self):
        return self.agent
    
    def load_or_create_index(self) -> VectorStoreIndex:
        """
        Loads the index from Postgres if it exists, otherwise creates it 
        from the data directory.
        """
        try:
            # 0. check if table exists, if not create one
            # Note that the real table create will have a data_ prefix.
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

    async def get_response_with_evaluation(self, query: str) -> dict:
        """
        Get agent response and evaluate the context quality.
        Returns both the response and evaluation metrics.
        """
        # Get response from agent
        response = await self.agent.run(query)
        response_str = str(response)
        
        # Evaluate context quality
        evaluation = await self.context_evaluator.evaluate_quality(query, response_str)
        
        return {
            "response": response_str,
            "evaluation": evaluation
        }

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

