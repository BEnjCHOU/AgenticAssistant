# Example Five

## Notice
In this example we've extended the [example four](../example_four/README.md).
- We used nextjs to create a web application
- created a database with postgreSQL to store vector index using pgvector
- Integrate docker
- the test_data/solar_system.txt file contains further explanation about dward planets, we can further use this file to test the updated Document feature.

### Working Environment
- MacOS : Important : using a chip with Apple Silicon we need to explicitly turn the
environment variable ON.
```yml 
PYTHONUNBUFFERED: "1"
```

### Preriquisites Backend
1. Install python3 for the backend
2. Create an [OpenAI API KEY](https://platform.openai.com/api-keys)
3. Export the openai api key
4. Install postgresql and define the DATABASE_URL environment variable.
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

### Preriquisites Frontend
1. Install dependencies
```bash
cd frontend/
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

### Questions to ask the agent
1. How many groups can we separate the solar system's planets into?
2. Were ancient civilizations isolated from others?
3. What is the earliest widely recognized writing system?
4. What is the key distinction from a full planet compared to a dwarf planet?
5. What is the hidden secret in the solar_system.txt file?