# vis-fix

A command line AI debugging assistant. Give it a screenshot of an error and it tells you how to fix it.

Point it at terminal output, an IDE error, a browser console, or a stack trace. It reads the image, works out what broke, searches the web for current documentation when it spots version numbers or unfamiliar APIs, and gives back an explanation plus a copy-pasteable fix.

There's also a [web version](../vis-fix-web) with streaming output and a proper multi-tool-call loop.

## Demo

```bash
python -m src.main error.png
```

```
[DEBUG] Original size:    284.50 KB
[DEBUG] Processed size:   91.20 KB
[DEBUG] Sending request to google/gemini-3-flash-preview...
[DEBUG] Model requested tool: web_search
[DEBUG] Search query: "TypeError: Cannot read properties of undefined reading 'map' react 18"
[DEBUG] Found 5 results
[DEBUG] Sending follow-up request with search results...

The error is happening because `data` is undefined on the first render...
```

## How it works

1. The image is resized to fit within 1024x1024 and compressed before it goes to the model, which keeps latency and cost down.
2. The model reads the screenshot and identifies the error, the framework, and any version numbers.
3. If anything looks version specific or potentially out of date, it calls the `web_search` tool on its own.
4. It explains the root cause and gives a fix grounded in current documentation.

## Tech stack

Python 3.11+, with:

* OpenAI SDK, pointed at [OpenRouter](https://openrouter.ai) for multimodal model access
* Pillow for image resizing and JPEG compression before the API call
* httpx for async HTTP against Tavily
* Tavily for the web search tool

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

```env
OPENROUTER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

## Usage

```bash
# basic
python -m src.main screenshot.png

# with a custom prompt
python -m src.main error.png "Why is my Docker build failing here?"

# save the fix (debug logs go to stderr, the answer goes to stdout)
python -m src.main error.png > fix.md
```

## Project structure

```
vis-fix/
├── src/
│   ├── main.py               # entry point, orchestrates the full flow
│   ├── image_processor.py    # resize + base64 encode via Pillow
│   ├── tools.py              # tool schema + Tavily web search
│   └── system_prompt.py      # system prompt for the assistant
├── requirements.txt
└── .env.example
```

## Model

Defaults to `google/gemini-3-flash-preview` through OpenRouter. Swap in any multimodal model (GPT-4o, Claude, whatever) by changing `MODEL` in `src/main.py`.

## Known limitation

This version only handles the first tool call the model requests. If it wants a second search before answering, that request is dropped and the answer comes back less researched than it should be. The [web version](../vis-fix-web) fixes this with a proper loop.
