import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv
import json
import time
from datetime import datetime

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        # print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str, model: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model=model,
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        final_text = []

        # print(response.content)
        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                if hasattr(content, 'text') and content.text:
                    messages.append({
                      "role": "assistant",
                      "content": content.text
                    })
                messages.append({
                    "role": "user", 
                    "content": result.content
                })

                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model=model,
                    max_tokens=1000,
                    messages=messages,
                )

                final_text.append(response.content[0].text)

        return "\n".join(final_text)

    async def chat_loop(self, model: str = "claude-3-haiku-20240307"):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print(f"Using model: {model}")
        print("Type your queries or 'quit' to exit.")
        
        log_file = "mcp_client.jsonl"

        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                
                start_time = time.time()
                
                try:
                    final_chunks, usage = await self.process_query_new(query, model)
                    print("\n" + "".join(final_chunks))
                    print(f"Token Usage: {{'prompt_tokens': {usage['prompt_tokens']}, 'completion_tokens': {usage['completion_tokens']}, 'total_tokens': {usage['total_tokens']}}}")
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "query": query,
                        "provider": "Anthropic",
                        "model": model,
                        "response": "".join(final_chunks),
                        "usage": usage,
                        "duration_ms": (time.time() - start_time) * 1000,
                        "success": True
                    }
                except Exception as e:
                    print(f"\nError: {str(e)}")
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "query": query,
                        "provider": "Anthropic",
                        "model": model,
                        "error": str(e),
                        "duration_ms": (time.time() - start_time) * 1000,
                        "success": False
                    }
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

    async def process_query_new(self, query: str, model: str) -> list[str]:
        messages = [{"role": "user", "content": query}]

        resp = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in resp.tools]

        final_chunks: list[str] = []
        usage_stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "tool_calls": []}

        while True:
            response = self.anthropic.messages.create(
                model=model,
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )

            if hasattr(response, 'usage'):
                usage_stats["prompt_tokens"] += response.usage.input_tokens
                usage_stats["completion_tokens"] += response.usage.output_tokens
                usage_stats["total_tokens"] += (response.usage.input_tokens + response.usage.output_tokens)

            tool_uses = [c for c in response.content if getattr(c, "type", None) == "tool_use"]

            if not tool_uses:
                for c in response.content:
                    if getattr(c, "type", None) == "text" and getattr(c, "text", None):
                        final_chunks.append(c.text)
                break

            tool_results_blocks = []
            tool_details = []

            for tu in tool_uses:
                tool_name = tu.name
                tool_args = tu.input
                tool_use_id = tu.id

                tool_start = time.time()
                result = await self.session.call_tool(tool_name, tool_args)
                tool_duration = (time.time() - tool_start) * 1000

                result_text = getattr(result, "content", "")
                if not isinstance(result_text, str):
                    result_text = str(result_text)

                final_chunks.append(f"[Called tool {tool_name} with args {json.dumps(tool_args, ensure_ascii=False)}]")
                final_chunks.append(result_text)

                tool_details.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": result_text[:500],
                    "duration_ms": tool_duration,
                    "success": not getattr(result, 'isError', False)
                })

                tool_results_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result_text,
                })

            messages.extend([
                {
                    "role": "assistant",
                    "content": response.content
                },
                {
                    "role": "user",
                    "content": tool_results_blocks
                }
            ])

            if tool_details:
                usage_stats["tool_calls"] = tool_details
        return final_chunks, usage_stats

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop(model="claude-3-haiku-20240307")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
