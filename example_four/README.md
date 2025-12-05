# Example Four

## Notice
In this example we've extended the [example three](../example_three/README.md) with fastapi and features like adding new document to the agent, updating new documents, deleting documents and asking question based of those documents. 

We currently don't have any database to store the [document_id](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes). For this reason, to locate which document and file to be deleted we search through the docstore.json to locate the document_id. But a better approach will be to store the id when creating the document. We will be doing this in the next example using [postgreSQL pgvector](https://github.com/pgvector/pgvector).

In a real life scenario we might use a chatbot that remembers previous questions asked, let's implement that in the next example.

### Working Environment
- MacOS

### Preriquisites
1. Install python3
2. Create an [OpenAI API KEY](https://platform.openai.com/api-keys)
3. Export the openai api key
```
export OPENAI_API_KEY=XXXXX
```
4. Create a python environment
```
python3 -m venv env
```
5. source the environment
```
source env/bin/activate
```
6. install libraries
```bash
python3 -m pip install -r requirements.txt
```

### Running the agent
1. running the server
```
uvicorn main:app --reload
```

### testing the code
```
cd example_four/
pytest
```