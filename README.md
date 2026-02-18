## Usage

This project supports multiple LLM backends. Select the appropriate client based on your desired provider.

### Prerequisites

Ensure you have [`uv`](https://github.com/astral-sh/uv) installed before proceeding.

### Running the Client

Each command launches a client paired with the MCP server (`server.py`).

**Anthropic (Claude)**
```bash
uv run python ./client.py ./server.py
```

**OpenAI**
```bash
uv run python ./client_openai.py ./server.py
```

**DeepSeek**
```bash
uv run python ./client_deepseek.py ./server.py
```

### API Keys

Before running, ensure the appropriate API key is set as an environment variable:

| Provider  | Environment Variable   |
|-----------|------------------------|
| Anthropic | `ANTHROPIC_API_KEY`    |
| OpenAI    | `OPENAI_API_KEY`       |
| DeepSeek  | `DEEPSEEK_API_KEY`     |

You can set these in a `.env` file at the project root