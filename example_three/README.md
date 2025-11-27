# Example Three

## Notice
Now let's get familiar with LlamaIndex library, this tutorial comes from the LlamaIndex official documentation [link](https://developers.llamaindex.ai/python/framework/getting_started/starter_example/). We will build an agent that helps us find our files and give us a summary for a specific file.

**Please note that adding the api key to the frontent is very dangerous. Do not use this example in real production project. In the next example, we will show how to add the key in a server environment.**

### Working Environment
- MacOS

### Preriquisites
1. Install python3
2. Create an [OpenAI API KEY](https://platform.openai.com/api-keys)
3. Export the openai api key
```
export OPENAI_API_KEY=XXXXX
```

#### Running the agent
1. Create a python environment
```
python3 -m venv env
```
2. source the environment
```
source env/bin/activate
```
3. install libraries
```bash
python3 -m pip install -r requirements.txt
```
4. running the agent
```
python3 main.py
```