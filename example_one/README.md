# Example One

## Notice
The first example we will use reactJS + vite to build a simple conversation panel connected to OpenAI LLM models.
**Please note that adding the api key to the frontent is very dangerous. Do not use this example in real production project. In the next example, we will show how to add the key in a server environment.**

### Working Environment
- MacOS

### Preriquisites
1. Create an [OpenAI API KEY](https://platform.openai.com/api-keys)
2. Create a .env file under the front project.
3. Add the following line in the .env file
```bash
VITE_OPENAI_API_KEY="THE_API_KEY_YOU_CREATED"
```
#### Install Node JS
1. install Node JS using nvm, follow this [link](https://nodejs.org/en/download) for more information
2. build the front end package
```bash
cd front
npm install
```
3. run the dev environment
```bash
npm run dev
```