"""vis-fix: AI-powered screenshot debugging assistant."""
import asyncio
import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from .image_processor import process_image
from .tools import TOOLS, run_web_search
from .system_prompt import SYSTEM_PROMPT

MODEL = "google/gemini-3-flash-preview"


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <path-to-screenshot> [prompt]", file=sys.stderr)
        raise SystemExit(1)

    image_path = sys.argv[1]
    user_prompt = sys.argv[2] if len(sys.argv) > 2 else "Please analyze this screenshot and help me fix the error."

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        raise SystemExit(1)

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    sys.stderr.write("[DEBUG] Starting vis-fix...\n")
    sys.stderr.write(f"[DEBUG] Image path: {image_path}\n")
    sys.stderr.write(f"[DEBUG] Prompt: {user_prompt}\n\n")

    # Process image to base64
    base64_image = process_image(image_path)
    data_url = f"data:image/jpeg;base64,{base64_image}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    sys.stderr.write(f"[DEBUG] Sending request to {MODEL}...\n")

    first_response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2048,
        messages=messages,
        tools=TOOLS,
    )

    first_message = first_response.choices[0].message if first_response.choices else None
    if not first_message:
        print("No response received from the model.", file=sys.stderr)
        raise SystemExit(1)

    # Handle tool call
    if first_message.tool_calls:
        tool_call = first_message.tool_calls[0]
        sys.stderr.write(f"[DEBUG] Model requested tool: {tool_call.function.name}\n")

        args = json.loads(tool_call.function.arguments)
        sys.stderr.write(f'[DEBUG] Search query: "{args["query"]}"\n\n')

        search_results = await run_web_search(args["query"])

        follow_up_messages = [
            *messages,
            {
                "role": "assistant",
                "content": first_message.content,
                "tool_calls": [tc.model_dump() for tc in first_message.tool_calls],
            },
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": search_results,
            },
        ]

        sys.stderr.write("[DEBUG] Sending follow-up request with search results...\n\n")

        second_response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2048,
            messages=follow_up_messages,
            tools=TOOLS,
        )

        final_answer = second_response.choices[0].message.content if second_response.choices else None
        if not final_answer:
            print("No final response received from the model.", file=sys.stderr)
            raise SystemExit(1)

        print(final_answer)
    else:
        direct_answer = first_message.content
        if not direct_answer:
            print("No response content received from the model.", file=sys.stderr)
            raise SystemExit(1)
        print(direct_answer)


if __name__ == "__main__":
    asyncio.run(main())
