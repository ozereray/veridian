# Veridian Guard 🛡️

![PyPI](https://img.shields.io/pypi/v/veridian-guard)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)

> **Built for production AI agents where reliability = security.**  
> Unhandled LLM failures silently break agent logic — Veridian Guard makes failure explicit, logged, and recoverable.

Robust retry and fallback decorators for unpredictable AI agents, LLM API calls, and flaky network requests.

When your AI agent crashes, the API rate-limits you, or a network request fails — Veridian Guard gracefully catches the error, retries with configurable delays, and returns a safe fallback to prevent production crashes.

---

## Table of Contents

- [Why Veridian Guard?](#-why-veridian-guard)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Async Support](#-asyncawait-support)
- [Advanced Usage](#-advanced-usage)
- [Parameters](#-parameters)
- [Real-World Use Cases](#-real-world-use-cases)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Why Veridian Guard?

| Feature | Description |
|---|---|
| 🪶 **Zero Dependencies** | Pure Python — nothing to install beyond the package itself |
| 🔁 **Smart Retry Logic** | Configurable retries with delay between attempts |
| 🔒 **Fail-Safe Fallbacks** | Never let an unhandled exception crash your agent loop |
| 🔍 **Built-in Logging** | Every failed attempt is automatically logged for debugging |
| ⚡ **Async-Native** | Auto-detects `async def` functions — no extra config needed |
| 🎯 **Selective Catching** | Target specific exception types, ignore the rest |

---

## 🚀 Installation

```bash
pip install veridian-guard
```

---

## ⚡ Quick Start

Wrap any flaky function — like an LLM API call — with the `@guard` decorator:

```python
from veridian_guard import guard
import random

@guard(max_retries=3, delay=1.5, fallback="Default safe response")
def call_llm_agent():
    if random.random() < 0.7:
        raise ConnectionError("LLM API Timeout!")
    return "Agent succeeded! Here is your generated text."

result = call_llm_agent()
print(result)
```

**Output on failure:**
```
[Veridian] Attempt 1 failed: LLM API Timeout! Retrying in 1.5s...
[Veridian] Attempt 2 failed: LLM API Timeout! Retrying in 1.5s...
[Veridian] Attempt 3 failed: LLM API Timeout! Retrying in 1.5s...
[Veridian] All retries exhausted. Returning fallback.
Default safe response
```

---

## 🔄 Async/Await Support

Veridian Guard automatically detects whether your function is synchronous or asynchronous — no extra flags needed:

```python
import asyncio
from veridian_guard import guard

@guard(max_retries=3, delay=2.0, fallback="Service unavailable")
async def fetch_data_from_llm():
    await asyncio.sleep(1)
    raise TimeoutError("API is too busy")

async def main():
    result = await fetch_data_from_llm()
    print(result)  # "Service unavailable"

asyncio.run(main())
```

---

## 🔧 Advanced Usage

### Catch only specific exceptions

```python
from veridian_guard import guard

@guard(
    max_retries=5,
    delay=2.5,
    exceptions=(TimeoutError, ConnectionError)
)
def call_data():
    # Only retries on TimeoutError or ConnectionError
    # A ValueError will be raised immediately — as expected
    pass
```

### Combine with any LLM provider

```python
from veridian_guard import guard
import anthropic

client = anthropic.Anthropic()

@guard(max_retries=4, delay=2.0, fallback="Claude is currently unavailable.")
def ask_claude(prompt: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

response = ask_claude("Summarize the key risks of this contract.")
print(response)
```

---

## 📦 Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_retries` | `int` | `3` | Maximum number of retry attempts |
| `delay` | `float` | `1.0` | Seconds to wait between retries |
| `fallback` | `any` | `None` | Value returned if all retries are exhausted |
| `exceptions` | `tuple` | `(Exception,)` | Exception types to catch and retry on |

---

## 📝 Real-World Use Cases

### 1. LLM API Calls (OpenAI, Anthropic, Gemini)

```python
@guard(max_retries=5, delay=2.0, fallback="Sorry, AI is currently unavailable.")
def ask_gpt(prompt):
    return openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
```

### 2. Database Connections

```python
@guard(max_retries=3, delay=1.0, exceptions=(ConnectionError, OperationalError))
def connect_to_db():
    return psycopg2.connect(DATABASE_URL)
```

### 3. Web Scraping & External APIs

```python
@guard(max_retries=4, delay=3.0, fallback=[])
def scrape_website(url: str):
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()
```

### 4. AI Agent Chains (LangChain, CrewAI)

```python
@guard(max_retries=3, delay=1.5, fallback={"status": "fallback", "result": None})
async def run_agent_step(input_data: dict):
    agent = build_agent()
    return await agent.ainvoke(input_data)
```

---

## 🤝 Contributing

Contributions are welcome! If you have an idea, found a bug, or want to improve the docs:

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push and open a Pull Request

---

## 📄 License

MIT License — free to use in personal and commercial projects.

---

<div align="center">
  <strong>Made with 💚 for the AI Agent community</strong><br/>
  <a href="https://github.com/ozereray">github.com/ozereray</a>
</div>
