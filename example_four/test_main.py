import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from main import app

client = TestClient(app)

# --- Fixtures to mock the heavy AgentDocument class ---

@pytest.fixture
def mock_agent_document():
    """
    Patches 'main.AgentDocument' so we don't actually load LlamaIndex
    or call OpenAI during unit tests.
    """
    with patch("main.AgentDocument") as MockClass:
        # Create a mock instance
        mock_instance = MockClass.return_value
        
        # Create a mock for the internal agent (FunctionAgent)
        mock_function_agent = MagicMock()
        
        # IMPORTANT: Since main.py uses 'await agent.run(...)', 
        # we must make .run() an AsyncMock.
        mock_function_agent.run = AsyncMock()
        
        # Connect the chain: AgentDocument().get_agent() -> mock_function_agent
        mock_instance.get_agent.return_value = mock_function_agent
        
        yield MockClass, mock_function_agent

# --- Tests ---

def test_ask_question_success(mock_agent_document):
    """Test the /ask/ endpoint with a mocked LLM response."""
    MockAgentDoc, mock_agent = mock_agent_document
    
    # 1. Define what the "LLM" should return
    mock_agent.run.return_value = "Mars is the fourth planet."
    
    # 2. Make the request
    payload = {"message": "Which planet is Mars?"}
    response = client.post("/ask/", json=payload)
    
    # 3. Assertions
    assert response.status_code == 200
    assert response.json() == {"response": "Mars is the fourth planet."}
    
    # Verify the code actually called the agent
    mock_agent.run.assert_called_once_with("Which planet is Mars?")

def test_ask_question_failure(mock_agent_document):
    """Test error handling in /ask/."""
    MockAgentDoc, mock_agent = mock_agent_document
    
    # Simulate an error from the agent (e.g., OpenAI down)
    mock_agent.run.side_effect = Exception("OpenAI API Error")
    
    payload = {"message": "Hello"}
    response = client.post("/ask/", json=payload)
    
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert "OpenAI API Error" in response.json()["error"]

@patch("main.shutil") # Mock file operations so we don't write to disk
@patch("main.Path")   # Mock Path so we don't create directories
def test_upload_file(mock_path, mock_shutil, mock_agent_document):
    """Test the /upload/ endpoint."""
    
    # Setup file upload
    filename = "test_doc.txt"
    file_content = b"This is a test document."
    
    # Mock the file saving logic
    mock_upload_path = MagicMock()
    mock_path.return_value = mock_upload_path
    mock_upload_path.mkdir.return_value = None
    mock_upload_path.__truediv__.return_value = MagicMock() # Mock the / operator for path

    # Make request
    response = client.post(
        "/upload/", 
        files={"file": (filename, file_content, "text/plain")}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == filename
    assert response.json()["message"] == "File saved successfully"

    # Verify AgentDocument().add_file_context_to_agent was called
    MockAgentDoc, _ = mock_agent_document
    MockAgentDoc.return_value.add_file_context_to_agent.assert_called_with(filename)

### Part 2: How to test the "Actual" LLM Response?
'''
Testing if the LLM response is "correct" is different from unit testing. 
You cannot check `assert response == "exact string"` 
because LLMs generate slightly different text every time.

Here are the three ways to test LLM Output:
'''
#### 1. Keyword Assertion (Simple)
'''
If you expect a specific fact, check if keywords exist.
'''
'''python
def test_llm_content_basic():
    # This runs against the REAL Agent (Integration Test)
    # WARNING: This costs money and requires setting up real OpenAI keys
    
    payload = {"message": "What is 2 + 2?"}
    response = client.post("/ask/", json=payload)
    
    answer = response.json()["response"]
    
    # We don't know if it will say "The answer is 4" or "It is 4", 
    # but it MUST contain "4".
    assert "4" in answer
'''
#### 2. LLM-as-a-Judge (Advanced - Recommended)
'''
Use a library like `deepeval` or `pytest-llm`. This uses a cheaper LLM (like GPT-3.5 or a local model) to grade the response of your main LLM.
**Example logic:**
'''

'''python
# Pseudo-code for LLM evaluation
def test_rag_accuracy():
    response = client.post("/ask/", json={"message": "Summarize the uploaded PDF."})
    actual_output = response.json()["response"]
    
    # Use another LLM to grade it
    grader_prompt = f"""
    Question: Summarize the uploaded PDF.
    Actual Answer: {actual_output}
    
    Does the Actual Answer make sense and seem like a summary? reply YES or NO.
    """
    grade = call_openai_gpt3(grader_prompt)
    assert "YES" in grade
'''

#### 3. Deterministic Assertions (For Tools)
'''
Since you are using `FunctionAgent` (tools), 
you should test that the *Tools* are called correctly, 
rather than just checking the text output.

You can modify the mock in `test_main.py` to ensure the tool logic works:
'''

'''python
def test_multiply_tool_logic():
    from agent import AgentDocument
    agent_doc = AgentDocument()
    
    # Directly test the multiply function
    result = agent_doc.multiply(7, 8)
    assert result == 56
'''