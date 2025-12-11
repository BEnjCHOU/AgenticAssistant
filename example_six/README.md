# Example Six

In this example we are going to augment our agent capability with existing MCP servers, fine-tune our prompt for dedicated tasks, and evaluate our context.

## Features

This example extends [example five](../example_five/README.md) with the following enhancements:

### 1. MCP (Model Context Protocol) Server Integration
- **File System Tools**: Read files from the data directory
- **Web Search Tools**: Real web search using DuckDuckGo (no API key required)
- **Calculator Tools**: Perform mathematical calculations
- **Extensible Architecture**: Easy to add new MCP tools

### 2. Fine-Tuned Prompts for Dedicated Tasks
The agent supports multiple task-specific prompts:
- **default**: General purpose assistant
- **document_analysis**: Specialized for analyzing documents
- **research**: Optimized for research tasks with multiple sources
- **calculation**: Focused on mathematical calculations
- **general**: General purpose with all tools available

### 3. Context Evaluation
- **Relevance Scoring**: Evaluates how relevant the context is to the query
- **Completeness Scoring**: Assesses if the context fully answers the query
- **Quality Metrics**: Overall quality score with recommendations
- **Detailed Feedback**: Provides explanations and identifies missing aspects

## Notice
This example extends [example five](../example_five/README.md) with:
- MCP server integration for enhanced tool capabilities
- Task-specific prompt fine-tuning
- Context quality evaluation system
- Enhanced API endpoints for evaluation and task type management

### Working Environment
- MacOS : Important : using a chip with Apple Silicon we need to explicitly turn the
environment variable ON.
```yml 
PYTHONUNBUFFERED: "1"
```

### Prerequisites Backend
1. Install python3 for the backend
2. Create an [OpenAI API KEY](https://platform.openai.com/api-keys)
3. Export the openai api key
4. Install postgresql and define the DATABASE_URL environment variable.
```
export OPENAI_API_KEY=XXXXX
```
5. Create a python environment
```
python3 -m venv env
```
6. source the environment
```
source env/bin/activate
```
7. install libraries
```bash
python3 -m pip install -r requirements.txt
```

**Note:** The web search feature uses DuckDuckGo via the `ddgs` package (included in requirements.txt). No API keys are required - web search works out of the box!

### Prerequisites Frontend
1. Install dependencies
```bash
cd frontend/my-app/
npm install
```

### Running the backend
```bash
cd backend/
uvicorn main:app --reload
```

### Running the frontend
```
cd frontend/my-app/
pnpm run dev
```

### Running with Docker Compose
```bash
docker-compose up --build
```
Open your browser to `http://localhost:3000`.

## API Endpoints

### Standard Endpoints (from example_five)
- `POST /ask/` - Ask a question to the agent
- `POST /upload/` - Upload a file
- `PUT /update/` - Update an existing file
- `DELETE /delete/{filename}` - Delete a file
- `GET /files/` - List all uploaded files

### New Endpoints

#### `POST /ask-with-evaluation/`
Ask a question and get context evaluation metrics.

**Request:**
```json
{
  "message": "What is the solar system?",
  "task_type": "document_analysis",
  "evaluate_context": true
}
```

**Response:**
```json
{
  "response": "...",
  "evaluation": {
    "overall_quality_score": 0.85,
    "relevance": {
      "relevance_score": 0.9,
      "explanation": "...",
      "key_points": [...]
    },
    "completeness": {
      "completeness_score": 0.8,
      "explanation": "...",
      "missing_aspects": [...]
    },
    "recommendation": "High quality context - suitable for use"
  },
  "status": "success"
}
```

#### `POST /set-task-type/`
Change the agent's task type for fine-tuned prompts.

**Request:**
```json
{
  "task_type": "document_analysis"
}
```

**Valid task types:**
- `default`
- `document_analysis`
- `research`
- `calculation`
- `general`

#### `GET /mcp-tools/`
List all available MCP tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read the contents of a file from the data directory",
      "inputSchema": {...}
    },
    ...
  ],
  "status": "success"
}
```

#### Enhanced `POST /ask/`
The standard ask endpoint now supports optional parameters:

**Request:**
```json
{
  "message": "What is the solar system?",
  "task_type": "document_analysis",
  "evaluate_context": false
}
```

## Usage Examples

### Using Task-Specific Prompts

```python
# Set task type for document analysis
POST /set-task-type/
{
  "task_type": "document_analysis"
}

# Ask a question - agent will use document_analysis prompt
POST /ask/
{
  "message": "Summarize the key points from the uploaded documents"
}
```

### Evaluating Context Quality

```python
# Ask with evaluation
POST /ask-with-evaluation/
{
  "message": "What are the main characteristics of dwarf planets?",
  "task_type": "document_analysis"
}
```

### Using MCP Tools

The agent automatically has access to MCP tools. You can:
- Read files using the `read_file` tool
- Perform calculations using the `calculate` tool
- Search the web using the `web_search` tool (powered by DuckDuckGo, returns up to 5 results with titles, URLs, and snippets)

The agent will automatically select and use appropriate tools based on the query.

**Example web search usage:**
The agent can automatically search the web when you ask questions like:
- "What's the current weather in San Francisco?"
- "Find recent news about AI developments"
- "Search for information about Python async programming"

## Questions to ask the agent
1. How many groups can we separate the solar system's planets into?
2. Were ancient civilizations isolated from others?
3. What is the earliest widely recognized writing system?
4. What is the key distinction from a full planet compared to a dwarf planet?
5. What is the hidden secret in the solar_system.txt file?

## Architecture

### MCP Tools (`mcp_tools.py`)
- `MCPTool`: Base class for MCP tools
- `FileSystemMCPTool`: File reading capabilities
- `WebSearchMCPTool`: Real web search using DuckDuckGo (returns up to 5 results with titles, URLs, and snippets)
- `CalculatorMCPTool`: Mathematical calculations
- `MCPToolRegistry`: Registry for managing tools

### Context Evaluator (`context_evaluator.py`)
- `ContextEvaluator`: Evaluates context quality
  - `evaluate_relevance()`: Relevance scoring
  - `evaluate_completeness()`: Completeness scoring
  - `evaluate_quality()`: Comprehensive evaluation

### Enhanced Agent (`agent.py`)
- Task-specific prompts
- MCP tool integration
- Context evaluation capabilities
- All features from example_five

## Extending MCP Tools

To add a new MCP tool:

1. Create a new tool class inheriting from `MCPTool`:
```python
class MyCustomTool(MCPTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Description of my tool"
        )
    
    def get_input_schema(self):
        return {...}
    
    async def execute(self, **kwargs):
        # Implementation
        return result
```

2. Register it in `mcp_tools.py`:
```python
mcp_registry.register_tool(MyCustomTool())
```

The tool will automatically be available to the agent!
