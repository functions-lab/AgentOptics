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

| Provider  | Environment Variable |
| --------- | -------------------- |
| Anthropic | `ANTHROPIC_API_KEY`  |
| OpenAI    | `OPENAI_API_KEY`     |
| DeepSeek  | `DEEPSEEK_API_KEY`   |

You can set these in a `.env` file at the project root.

### Device-Specific Files

For files related to **Lumentum ROADM**, **Lumentum 400 GbE CFP2-DCO**, **Calient switch**, or **DiCon switch**, please email us to request access.

## License

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

If you have any questions or suggestions, feel free to open an issue on GitHub.