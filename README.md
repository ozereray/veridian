# Veridian Guard 🌿

Robust retry and fallback decorators for unpredictable AI agents, LLM calls, and flaky network requests.

When your AI agent crashes, the API rate-limits you, or a network request fails, **Veridian Guard** gracefully catches the errors, retries the execution with custom delays, and provides safe fallbacks to prevent production crashes.

## 🚀 Installation

```bash
pip install veridian-guard
```

## 💡 Quick Start (Sync)

Wrap any flaky function (like an LLM API call) with the @guard decorator.

from veridian.guard import guard
import random

# Example: An unpredictable LLM function

@guard(max_retries=3, delay=1.0, fallback="Default safe response")
def call_llm_agent(): # Simulating a random API failure
if random.random() < 0.7:
raise ConnectionError("LLM API Timeout!")

    return "Agent succeeded! Here is your generated text."

result = call_llm_agent()
print(result)

## ⚡ Async/Await Support Built-in

Veridian Guard automatically detects whether your function is synchronous or asynchronous. It works flawlessly with asyncio, making it perfect for modern AI agents like LangChain or CrewAI.

import asyncio
from veridian.guard import guard

@guard(max_retries=3, delay=2.0, fallback={"status": "failed"})
async def fetch_data_from_llm(): # Simulating a heavy async API call
await asyncio.sleep(1)
raise TimeoutError("API is too busy!")

async def main():
result = await fetch_data_from_llm()
print(result) # Will print the fallback: {'status': 'failed'}

asyncio.run(main())

## ✨ Why Veridian Guard?

Zero Dependencies: Pure Python. Extremely lightweight.

Smart Logging Built-in: Automatically logs failed attempts and warnings so you can monitor your agent's behavior in the terminal.

Fail-Safe Fallbacks: Never let an unhandled exception crash your main application loop again.

Universal: Seamlessly handles both def and async def functions out of the box.

## 🛠️ Advanced Usage

Catching specific exceptions instead of all errors:

from veridian.guard import guard

@guard(max_retries=5, delay=2.0, exceptions=(TimeoutError, ConnectionError))
def fetch_data(): # Will only retry on TimeoutError or ConnectionError. # Other exceptions (like ValueError) will be raised immediately.
pass
