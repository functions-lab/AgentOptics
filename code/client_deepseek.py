import asyncio
import sys, os
from typing import Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
import json
import time
from datetime import datetime

load_dotenv()  # load environment variables from .env


class MCPClient:
	def __init__(self):
		self.session: Optional[ClientSession] = None
		self.exit_stack = AsyncExitStack()
		self.openai = OpenAI(
			api_key=os.getenv("DEEPSEEK_API_KEY"),
			base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
		)

	async def connect_to_server(self, server_script_path: str):
		"""Connect to an MCP server (.py or .js)"""
		is_python = server_script_path.endswith(".py")
		is_js = server_script_path.endswith(".js")
		if not (is_python or is_js):
			raise ValueError("Server script must be a .py or .js file")

		command = "python" if is_python else "node"
		server_params = StdioServerParameters(
			command=command,
			args=[server_script_path],
			env=None,
		)

		stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
		self.stdio, self.write = stdio_transport
		self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

		await self.session.initialize()
		response = await self.session.list_tools()
		tools = response.tools
		# print("\nConnected to server with tools:", [tool.name for tool in tools])

	async def process_query(self, query: str, model: str) -> str:
		response = await self.session.list_tools()
		available_tools = [
			{
				"name": tool.name,
				"description": tool.description,
				"parameters": tool.inputSchema,
			}
			for tool in response.tools
		]

		response = self.openai.chat.completions.create(
			model=model,
			messages=[{"role": "user", "content": query}],
			tools=[
				{
					"type": "function",
					"function": t,
				}
				for t in available_tools
			],
		)

		message = response.choices[0].message
		final_text = []

		if message.content:
			final_text.append(message.content)

		if message.tool_calls:
			# print(message.tool_calls)
			for tool_call in message.tool_calls:
				tool_name = tool_call.function.name
				raw_args = tool_call.function.arguments
				tool_args = json.loads(raw_args) if isinstance(raw_args, str) and raw_args.strip() else {}

				result = await self.session.call_tool(tool_name, tool_args)
				res_text = str(result.content)
				final_text.append(f"[Called tool {tool_name} with {tool_args}]")

				# Feed result back into OpenAI for final reasoning
				followup = self.openai.chat.completions.create(
					model=model,
					# messages=[
					#     {"role": "user", "content": query},
					#     {"role": "assistant", "tool_calls": [tool_call]},
					#     {"role": "tool", "content": str(result.content), "name": tool_name},
					# ],
					messages=[
						{"role": "user", "content": query},
						{
							"role": "assistant",
							"content": "", 
							"tool_calls": [{
								"id": tool_call.id,
								"type": "function",
								"function": {
									"name": tool_name,
									"arguments": raw_args,
								},
							}],
						},
						{
							"role": "tool",
							"tool_call_id": tool_call.id,
							"content": res_text,
						},
					],
				)
				final_text.append(followup.choices[0].message.content)
		return "\n".join(filter(None, final_text))

	async def chat_loop(self, model: str = "deepseek-chat"):
		"""Run an interactive chat loop"""
		print("\nMCP Client Started!")
		print("Type your queries or 'quit' to exit.")

		log_file = "mcp_client.jsonl"

		while True:
			try:
				query = input("\nQuery: ").strip()
				if query.lower() == "quit":
					break

				start_time = time.time()
				try:
					final_chunks, usage = await self.process_query_new(query, model)
					print("\n" + "".join(final_chunks))
					print(f"Token Usage: {{'prompt_tokens': {usage['prompt_tokens']}, 'completion_tokens': {usage['completion_tokens']}, 'total_tokens': {usage['total_tokens']}}}")

					log_entry = {
						"timestamp": datetime.now().isoformat(),
						"query": query,
						"provider": "DeepSeek",
						"model": model,
						"response": "".join(final_chunks),
						"usage": usage,
						"duration_ms": (time.time() - start_time) * 1000,
						"success": True
					}
				except Exception as e:
					print(f"\nError is: {str(e)}")
					log_entry = {
						"timestamp": datetime.now().isoformat(),
						"query": query,
						"provider": "DeepSeek",
						"model": model,
						"error": str(e),
						"duration_ms": (time.time() - start_time) * 1000,
						"success": False
					}
				with open(log_file, 'a') as f:
					f.write(json.dumps(log_entry) + '\n')
			except Exception as e:
				print(f"\nError is: {str(e)}")

	async def cleanup(self):
		"""Clean up resources"""
		await self.exit_stack.aclose()

	async def process_query_new(self, query: str, model: str) -> tuple[list[str], dict]:
		resp = await self.session.list_tools()
		available_tools = [
			{"name": t.name, "description": t.description, "parameters": t.inputSchema}
			for t in resp.tools
		]
		tool_schema = [{"type": "function", "function": t} for t in available_tools]

		messages = [{"role": "user", "content": query}]
		final_chunks: list[str] = []
		usage_stats = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "tool_calls": []}

		while True:
			r = self.openai.chat.completions.create(
				model=model,
				messages=messages,
				tools=tool_schema,
				tool_choice="auto",
			)
			msg = r.choices[0].message
			if r.usage:
				usage_stats["prompt_tokens"] += r.usage.prompt_tokens
				usage_stats["completion_tokens"] += r.usage.completion_tokens
				usage_stats["total_tokens"] += r.usage.total_tokens

			if msg.content:
				final_chunks.append(msg.content)

			if not msg.tool_calls:
				break

			assistant_tool_calls = []
			tool_result_msgs = []
			tool_details = []
			for tc in msg.tool_calls:
				tool_name = tc.function.name
				raw_args = tc.function.arguments
				args = json.loads(raw_args) if isinstance(raw_args, str) and raw_args.strip() else {}

				tool_start = time.time()
				result = await self.session.call_tool(tool_name, args)
				tool_duration = (time.time() - tool_start) * 1000
				res_text = str(result.content)

				final_chunks.append(f"[Called tool {tool_name} with {args}]")
				final_chunks.append(res_text)
				
				tool_details.append({
					"tool_name": tool_name,
					"arguments": args,
					"result": res_text[:500],
					"duration_ms": tool_duration,
					"success": not getattr(result, 'isError', False)
				})

				assistant_tool_calls.append({
					"id": tc.id,
					"type": "function",
					"function": {"name": tool_name, "arguments": raw_args},
				})
				tool_result_msgs.append({
					"role": "tool",
					"tool_call_id": tc.id,
					"content": res_text,
				})

			messages.append({"role": "assistant", "content": "", "tool_calls": assistant_tool_calls})
			messages.extend(tool_result_msgs)
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
		await client.chat_loop(model="deepseek-chat")
	finally:
		await client.cleanup()


if __name__ == "__main__":
	asyncio.run(main())
