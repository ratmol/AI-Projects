# vis-fix 🔧

A command-line AI debugging assistant that takes a screenshot of an error and tells you how to fix it.

Point it at any terminal output, IDE error, browser console, or stack trace. It reads the image, identifies the error, searches the web for up-to-date documentation when it spots version numbers or unfamiliar APIs, and gives you a clear explanation and a copy-pasteable fix.

---

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

---

## How It Works

1. The image is resized to fit within 1024×1024 and compressed before being sent to the model — keeping latency and costs low
2. The model examines the screenshot and identifies the error, framework, and version numbers
3. If anything looks version-specific or potentially outdated, it calls the `web_search` tool automatically
4. It explains the root cause and gives a fix grounded in current documentation

---

## Tech Stack

- **Python 3.11+**
- **OpenAI SDK** — pointed at [OpenRouter](https://openrouter.ai) for multimodal model access
- **Pillow** — image resizing and JPEG compression before API submission
- **httpx** — async HTTP for Tavily search
- **Tavily** — real-time web search tool

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

```env
OPENROUTER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

---

## Usage

```bash
# Basic usage
python -m src.main screenshot.png

# With a custom prompt
python -m src.main error.png "Why is my Docker build failing here?"

# Save the fix to a file (debug logs go to stderr, answer goes to stdout)
python -m src.main error.png > fix.md
```

---

## Project Structure

```
vis-fix/
├── src/
│   ├── main.py               # Entry point — orchestrates the full flow
│   ├── image_processor.py    # Resize + base64 encode images via Pillow
│   ├── tools.py              # Tool schema + Tavily web search implementation
│   └── system_prompt.py      # System prompt for the debugging assistant
├── requirements.txt
└── .env.example
```

---

## Model

Uses `google/gemini-3-flash-preview` via OpenRouter by default. You can swap it for any multimodal model (GPT-4o, Claude 3.5 Sonnet, etc.) by changing `MODEL` in `src/main.py`.