"""Generate the bundled example error screenshots (frontend/public/examples).

Run once with the backend venv: python scripts/make_examples.py
Renders fake-but-realistic terminal/console errors with Pillow so the demo
needs no third-party screenshots.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parents[1] / "frontend" / "public" / "examples"

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
]

BG = (13, 15, 18)
CHROME = (30, 33, 38)
FG = (208, 208, 200)
RED = (235, 100, 92)
YELLOW = (222, 179, 92)
BLUE = (108, 158, 216)
DIM = (120, 126, 134)

# Each line: (color, text)
EXAMPLES = {
    "python-traceback.png": [
        (DIM, "(.venv) PS C:\\projects\\api> python main.py"),
        (FG, "Traceback (most recent call last):"),
        (FG, '  File "C:\\projects\\api\\main.py", line 4, in <module>'),
        (FG, "    from pydantic import BaseSettings"),
        (RED, "ImportError: cannot import name 'BaseSettings' from 'pydantic'"),
        (RED, "(C:\\projects\\api\\.venv\\Lib\\site-packages\\pydantic\\__init__.py)"),
        (FG, ""),
        (YELLOW, "For further information visit https://errors.pydantic.dev/2.7/u/import-error"),
        (DIM, "(.venv) PS C:\\projects\\api>"),
    ],
    "npm-eresolve.png": [
        (DIM, "PS C:\\projects\\dashboard> npm install react-day-picker"),
        (RED, "npm ERR! code ERESOLVE"),
        (RED, "npm ERR! ERESOLVE unable to resolve dependency tree"),
        (FG, "npm ERR!"),
        (FG, "npm ERR! While resolving: dashboard@0.1.0"),
        (FG, "npm ERR! Found: date-fns@3.6.0"),
        (FG, 'npm ERR! node_modules/date-fns'),
        (FG, 'npm ERR!   date-fns@"^3.6.0" from the root project'),
        (FG, "npm ERR!"),
        (FG, "npm ERR! Could not resolve dependency:"),
        (RED, 'npm ERR! peer date-fns@"^2.28.0" from react-day-picker@8.10.1'),
        (FG, "npm ERR!"),
        (YELLOW, "npm ERR! Fix the upstream dependency conflict, or retry"),
        (YELLOW, "npm ERR! this command with --force or --legacy-peer-deps"),
    ],
    "cors-console.png": [
        (BLUE, "> fetch('http://localhost:8000/api/items').then(r => r.json())"),
        (DIM, "<- Promise {<pending>}"),
        (RED, "Access to fetch at 'http://localhost:8000/api/items' from origin"),
        (RED, "'http://localhost:5173' has been blocked by CORS policy: No"),
        (RED, "'Access-Control-Allow-Origin' header is present on the requested"),
        (RED, "resource. If an opaque response serves your needs, set the request's"),
        (RED, "mode to 'no-cors' to fetch the resource with CORS disabled."),
        (FG, ""),
        (RED, "GET http://localhost:8000/api/items net::ERR_FAILED 200 (OK)"),
        (DIM, "  (anonymous) @ VM312:1"),
    ],
}


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render(name: str, lines: list[tuple[tuple[int, int, int], str]]) -> None:
    font = load_font(16)
    line_h, pad, chrome_h = 26, 24, 36
    width = 880
    height = chrome_h + pad * 2 + line_h * len(lines)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # window chrome with traffic lights
    draw.rectangle([0, 0, width, chrome_h], fill=CHROME)
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([14 + i * 22, 12, 26 + i * 22, 24], fill=color)

    y = chrome_h + pad
    for color, text in lines:
        draw.text((pad, y), text, font=font, fill=color)
        y += line_h

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / name)
    print(f"wrote {OUT_DIR / name}")


if __name__ == "__main__":
    for name, lines in EXAMPLES.items():
        render(name, lines)
