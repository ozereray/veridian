# Veridian Guard 🛡️

Robust retry and fallback decorators for unpredictable AI agents, LLM calls, and flaky network requests.

When your AI agents crashes, the API rate limits you, or a network request fails, Veridian Guard gracefully catches the errors, retries the execution with custom delays, and provides safe fallbacks to prevent production crashes.

---

## 🚀 Installation

```bash
pip install veridian-guard
```

---

## ⚡ Quick Start (Sync)

Wrap any flaky function like an LLM API call with the `@guard` decorator:

```python
from veridian_guard import guard
import random

@guard(max_retries=3, delay=1.5, fallback="Default safe response")
def call_llm_agent():
    # Simulating a random API failure
    if random.random() < 0.7:
        raise ConnectionError("LLM API Timeout!")
    return "Agent succeeded! Here is your generated text."

result = call_llm_agent()
print(result)
```

---

## 🔄 Async/Await Support Built-in

Veridian Guard automatically detects whether your function is synchronous or asynchronous. It works flawlessly with async/await, making it perfect for modern AI agent chains or Crew AI.

```python
import asyncio
from veridian_guard import guard

@guard(max_retries=3, delay=2.0, fallback="Failed", async_def_fetch_data_from_llm=True)
async def fetch_data_from_llm():
    # Simulating a heavy async API call
    await asyncio.sleep(1)
    raise TimeoutError("API is too busy")

async def main():
    result = await fetch_data_from_llm()
    print(result)  # Will print the fallback: "Failed"

asyncio.run(main())
```

---

## ✨ Why Veridian Guard?

✅ **Zero Dependencies** - Pure Python, Extremely lightweight.

✅ **Smart Logging Built-in** - Automatically logs failed attempts and warnings so you can monitor your agent's behavior in the terminal.

✅ **Fail-Safe Fallbacks** - Never let an unhandled exception crash your main application loop again.

✅ **Universal** - Seamlessly handles both def and async def functions out of the box.

---

## 🔧 Advanced Usage

### Catching specific exceptions instead of all errors:

```python
from veridian_guard import guard

@guard(
    max_retries=5,
    delay=2.5,
    exceptions=(TimeoutError, ConnectionError)
)
def call_data():
    # Will only retry on TimeoutError or ConnectionError
    # Other exceptions like ValueError will be raised immediately
    pass
```

---

## 📦 Parameters

| Parameter     | Type  | Default      | Description                            |
| ------------- | ----- | ------------ | -------------------------------------- |
| `max_retries` | int   | 3            | Maximum number of retry attempts       |
| `delay`       | float | 1.0          | Delay in seconds between retries       |
| `fallback`    | any   | None         | Value to return if all retries fail    |
| `exceptions`  | tuple | (Exception,) | Specific exceptions to catch and retry |

---

## 📝 Real-World Use Cases

### 1. LLM API Calls

```python
@guard(max_retries=5, delay=2.0, fallback="Sorry, AI is unavailable")
def ask_chatgpt(prompt):
    return openai.ChatCompletion.create(...)
```

### 2. Database Connections

```python
@guard(max_retries=3, delay=1.0, exceptions=(ConnectionError,))
def connect_to_db():
    return psycopg2.connect(...)
```

### 3. Web Scraping

```python
@guard(max_retries=4, delay=3.0, fallback=[])
def scrape_website(url):
    response = requests.get(url, timeout=5)
    return response.json()
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - feel free to use in your projects!

---

## 🌟 Star Us!

If Veridian Guard helped you build more resilient AI agents, give us a star on GitHub! ⭐

---

**Made with 💚 for the AI Agent community**
