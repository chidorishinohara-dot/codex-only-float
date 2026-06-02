import argparse
import json
import os
import ssl
import subprocess
import time
import tkinter as tk
import unittest
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.json"
USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
DEFAULT_CONFIG = {"x": 1180, "y": 80, "refresh_seconds": 60, "theme": "light"}
TRANSPARENT_COLOR = "#ff00ff"
PANEL_BG = "#ffffff"
TEXT = "#111827"
MUTED = "#4b5563"
SUBTLE = "#f3f4f6"
BORDER = "#d1d5db"
GREEN = "#10a37f"
AMBER = "#b45309"
RED = "#b91c1c"
FONT = "Cambria"
WINDOW_WIDTH = 316
WINDOW_HEIGHT = 236
SURFACE_RADIUS = 32
BAR_HEIGHT = 16
TITLE_SIZE = 20
BODY_SIZE = 12
ROW_TITLE_SIZE = 13


@dataclass
class WindowInfo:
    title: str
    used_percent: float
    reset_at: int | None
    reset_text: str | None

    @property
    def remaining_percent(self) -> float:
        return max(0.0, min(100.0, 100.0 - self.used_percent))


@dataclass
class UsageInfo:
    plan: str
    primary: WindowInfo
    secondary: WindowInfo | None
    code_review: WindowInfo | None
    extras: list[WindowInfo]
    credits: str | None
    fetched_at: datetime


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()
    config = DEFAULT_CONFIG.copy()
    for key in DEFAULT_CONFIG:
        if key in data:
            config[key] = data[key]
    return config


def save_config(config: dict[str, Any]) -> None:
    safe = {
        "x": int(config.get("x", DEFAULT_CONFIG["x"])),
        "y": int(config.get("y", DEFAULT_CONFIG["y"])),
        "refresh_seconds": int(config.get("refresh_seconds", DEFAULT_CONFIG["refresh_seconds"])),
        "theme": str(config.get("theme", DEFAULT_CONFIG["theme"])),
    }
    CONFIG_FILE.write_text(json.dumps(safe, indent=2), encoding="utf-8")


def auth_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        return Path(codex_home) / "auth.json"
    return Path.home() / ".codex" / "auth.json"


def load_credentials() -> tuple[str, str | None]:
    path = auth_path()
    if not path.exists():
        raise RuntimeError(f"Codex auth not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    api_key = str(data.get("OPENAI_API_KEY") or "").strip()
    if api_key:
        return api_key, None
    tokens = data.get("tokens")
    if not isinstance(tokens, dict):
        raise RuntimeError("Codex auth.json has no tokens object.")
    access_token = str(tokens.get("access_token") or "").strip()
    if not access_token:
        raise RuntimeError("Codex auth.json is missing access_token.")
    account_id = str(tokens.get("account_id") or "").strip() or None
    return access_token, account_id


def plan_label(plan_type: Any) -> str:
    raw = str(plan_type or "").strip()
    if not raw:
        return "Codex"
    mapping = {
        "guest": "Guest",
        "free": "ChatGPT Free",
        "go": "Codex Go",
        "plus": "ChatGPT Plus",
        "pro": "ChatGPT Pro",
        "pro_lite": "Pro Lite",
        "prolite": "Pro Lite",
        "pro-lite": "Pro Lite",
        "team": "ChatGPT Team",
        "business": "ChatGPT Business",
        "enterprise": "ChatGPT Enterprise",
        "education": "ChatGPT Education",
        "edu": "ChatGPT Education",
        "quorum": "Codex Quorum",
        "k12": "Codex K12",
    }
    return mapping.get(raw.lower(), f"ChatGPT {raw[:1].upper()}{raw[1:]}")


def number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def parse_reset_text(reset_at: int | None) -> str | None:
    if not reset_at:
        return None
    remaining = reset_at - int(time.time())
    if remaining <= 0:
        return "now"
    minutes = remaining // 60
    hours = minutes // 60
    mins = minutes % 60
    if hours >= 24:
        days = hours // 24
        rem_hours = hours % 24
        return f"{days}d {rem_hours}h" if rem_hours else f"{days}d"
    if hours:
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    return f"{mins}m"


def parse_window(title: str, data: Any) -> WindowInfo:
    if not isinstance(data, dict):
        data = {}
    reset_at_raw = data.get("reset_at")
    reset_at = int(reset_at_raw) if isinstance(reset_at_raw, (int, float, str)) and str(reset_at_raw).strip() else None
    return WindowInfo(
        title=title,
        used_percent=max(
            0.0,
            min(100.0, number(data.get("used_percent", data.get("usage_percent")))),
        ),
        reset_at=reset_at,
        reset_text=parse_reset_text(reset_at),
    )


def titleize(text: str) -> str:
    parts = [p for p in text.replace("_", " ").replace("-", " ").split(" ") if p]
    return " ".join(p[:1].upper() + p[1:].lower() for p in parts) or "Extra"


def parse_usage_json(data: dict[str, Any]) -> UsageInfo:
    rate_limit = data.get("rate_limit") if isinstance(data.get("rate_limit"), dict) else {}
    primary_data = rate_limit.get("primary_window")
    secondary_data = rate_limit.get("secondary_window")
    code_review_data = rate_limit.get("code_review_window")

    if primary_data is None and isinstance(data.get("rate_limits"), list) and data["rate_limits"]:
        rate_limits = data["rate_limits"]
        primary_data = rate_limits[0]
        secondary_data = rate_limits[1] if len(rate_limits) > 1 else None
        code_review_data = rate_limits[2] if len(rate_limits) > 2 else None

    primary = parse_window("Session", primary_data or data)
    secondary = parse_window("Weekly", secondary_data) if isinstance(secondary_data, dict) else None
    code_review = parse_window("Code review", code_review_data) if isinstance(code_review_data, dict) else None

    extras: list[WindowInfo] = []
    for item in data.get("additional_rate_limits") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("limit_name") or item.get("metered_feature") or "Extra")
        rate = item.get("rate_limit") if isinstance(item.get("rate_limit"), dict) else item
        window = None
        if isinstance(rate, dict):
            window = rate.get("primary_window") or rate.get("secondary_window")
        if isinstance(window, dict):
            extras.append(parse_window(titleize(name), window))

    credits_text = None
    credits = data.get("credits")
    if isinstance(credits, dict) and credits.get("has_credits") and not credits.get("unlimited"):
        balance = number(credits.get("balance"))
        credits_text = f"${balance:.2f} credits"

    return UsageInfo(
        plan=plan_label(data.get("plan_type")),
        primary=primary,
        secondary=secondary,
        code_review=code_review,
        extras=extras,
        credits=credits_text,
        fetched_at=datetime.now(timezone.utc),
    )


def is_transient_network_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return isinstance(exc, (TimeoutError, ssl.SSLError)) or "eof occurred" in text or "unexpected_eof" in text


def fetch_usage() -> UsageInfo:
    token, account_id = load_credentials()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": "CodexOnlyFloat",
    }
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id
    request = urllib.request.Request(USAGE_URL, headers=headers, method="GET")
    last_network_error: BaseException | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
            return parse_usage_json(json.loads(body))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise RuntimeError("Codex login expired. Run codex login again.") from exc
            raise RuntimeError(f"Codex API returned HTTP {exc.code}.") from exc
        except urllib.error.URLError as exc:
            reason = exc.reason if isinstance(exc.reason, BaseException) else exc
            last_network_error = reason
            if attempt < 2 and is_transient_network_error(reason):
                time.sleep(1.5)
                continue
            raise RuntimeError("Network temporarily unavailable. Retrying automatically.") from exc
        except (TimeoutError, ssl.SSLError) as exc:
            last_network_error = exc
            if attempt < 2:
                time.sleep(1.5)
                continue
            raise RuntimeError("Network temporarily unavailable. Retrying automatically.") from exc
    raise RuntimeError("Network temporarily unavailable. Retrying automatically.") from last_network_error


def codex_is_running() -> bool:
    if os.name != "nt":
        return True
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Codex.exe"],
            capture_output=True,
            creationflags=flags,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return True
    return "Codex.exe" in result.stdout


def rounded_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    **kwargs: Any,
) -> int:
    radius = max(0, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=16, **kwargs)


class CodexFloat(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.drag_offset: tuple[int, int] | None = None
        self.refresh_after_id: str | None = None
        self.codex_miss_count = 0
        self.last_usage: UsageInfo | None = None
        self.network_error_count = 0
        self.title("Codex quota")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{self.config_data['x']}+{self.config_data['y']}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(bg=TRANSPARENT_COLOR)
        try:
            self.attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass

        self.shell = tk.Canvas(
            self,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=TRANSPARENT_COLOR,
            highlightthickness=0,
            bd=0,
        )
        self.shell.pack(fill="both", expand=True)
        rounded_rect(
            self.shell,
            6,
            6,
            WINDOW_WIDTH - 6,
            WINDOW_HEIGHT - 6,
            SURFACE_RADIUS,
            fill=PANEL_BG,
            outline=BORDER,
            width=1,
        )
        rounded_rect(
            self.shell,
            8,
            8,
            WINDOW_WIDTH - 8,
            WINDOW_HEIGHT - 8,
            SURFACE_RADIUS,
            fill=PANEL_BG,
            outline="",
        )
        self.shell.bind("<ButtonPress-1>", self.start_drag)
        self.shell.bind("<B1-Motion>", self.drag)
        self.shell.bind("<ButtonRelease-1>", self.end_drag)

        self.content = tk.Frame(self, bg=PANEL_BG)
        self.content.place(x=22, y=18, width=272, height=200)

        header = tk.Frame(self.content, bg=PANEL_BG)
        header.pack(fill="x", pady=(0, 5))
        header.columnconfigure(3, weight=1)

        self.title_label = tk.Label(header, text="Codex", bg=PANEL_BG, fg=TEXT, font=(FONT, TITLE_SIZE, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w")
        self.plan_label = tk.Label(header, text="Loading", bg=PANEL_BG, fg=MUTED, font=(FONT, BODY_SIZE))
        self.plan_label.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.status_label = tk.Label(header, text="", width=5, bg=PANEL_BG, fg=MUTED, font=(FONT, BODY_SIZE))
        self.status_label.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.close_btn = tk.Label(header, text="脳", bg=PANEL_BG, fg=MUTED, font=("Segoe UI", 18), cursor="hand2")
        self.close_btn.grid(row=0, column=4, sticky="e")
        self.close_btn.bind("<Button-1>", lambda _event: self.close())

        self.rows_frame = tk.Frame(self.content, bg=PANEL_BG)
        self.rows_frame.pack(fill="x")

        footer = tk.Frame(self.content, bg=PANEL_BG)
        footer.pack(fill="x", pady=(4, 0))
        self.make_button(footer, "↻", self.refresh_now).pack(side="left")
        self.bind_drag_recursive(self)
        self.close_btn.bind("<Button-1>", lambda _event: self.close())

        self.refresh_now()
        self.after(5000, self.check_codex_running)

    def make_button(self, parent: tk.Widget, text: str, command) -> tk.Canvas:
        canvas = tk.Canvas(parent, width=38, height=30, bg=PANEL_BG, highlightthickness=0, bd=0, cursor="hand2")
        rounded_rect(canvas, 1, 1, 37, 29, SURFACE_RADIUS, fill=SUBTLE, outline=BORDER, width=1)
        canvas.create_text(19, 14, text=text, fill=TEXT, font=(FONT, 16, "bold"))
        canvas.bind("<Button-1>", lambda _event: command())
        return canvas

    def bind_drag_recursive(self, widget: tk.Widget):
        if widget not in (self.close_btn,):
            widget.bind("<ButtonPress-1>", self.start_drag, add="+")
            widget.bind("<B1-Motion>", self.drag, add="+")
            widget.bind("<ButtonRelease-1>", self.end_drag, add="+")
        for child in widget.winfo_children():
            if isinstance(child, tk.Canvas):
                continue
            self.bind_drag_recursive(child)

    def start_drag(self, event):
        self.drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def drag(self, event):
        if self.drag_offset:
            ox, oy = self.drag_offset
            self.geometry(f"+{event.x_root - ox}+{event.y_root - oy}")

    def end_drag(self, _event):
        self.config_data["x"] = self.winfo_x()
        self.config_data["y"] = self.winfo_y()
        save_config(self.config_data)

    def schedule_refresh(self):
        if self.refresh_after_id:
            self.after_cancel(self.refresh_after_id)
        seconds = max(60, int(self.config_data.get("refresh_seconds", 60)))
        self.refresh_after_id = self.after(seconds * 1000, self.refresh_now)

    def check_codex_running(self):
        if codex_is_running():
            self.codex_miss_count = 0
        else:
            self.codex_miss_count += 1
            if self.codex_miss_count >= 2:
                self.close()
                return
        self.after(5000, self.check_codex_running)

    def refresh_now(self):
        self.status_label.config(text="...")
        self.after(10, self.do_fetch)

    def do_fetch(self):
        try:
            usage = fetch_usage()
        except Exception as exc:
            self.render_fetch_error(str(exc))
        else:
            self.render_usage(usage)
        self.schedule_refresh()

    def clear_rows(self):
        for child in self.rows_frame.winfo_children():
            child.destroy()

    def render_usage(self, usage: UsageInfo):
        self.last_usage = usage
        self.network_error_count = 0
        self.clear_rows()
        self.plan_label.config(text=usage.plan)
        windows = [usage.primary]
        if usage.secondary:
            windows.append(usage.secondary)
        if usage.code_review:
            windows.append(usage.code_review)
        windows = windows[:2]
        for info in windows:
            self.add_usage_row(info)
        if usage.credits:
            self.add_note(usage.credits)
        self.status_label.config(text=time.strftime("%H:%M"))

    def render_fetch_error(self, message: str):
        is_network = "Network temporarily unavailable" in message
        if is_network and self.last_usage:
            self.network_error_count += 1
            self.plan_label.config(text=self.last_usage.plan)
            self.status_label.config(text="retry")
            return
        self.render_error(message)

    def add_usage_row(self, info: WindowInfo):
        row = tk.Frame(self.rows_frame, bg=PANEL_BG)
        row.pack(fill="x", pady=3)
        top = tk.Frame(row, bg=PANEL_BG)
        top.pack(fill="x")
        tk.Label(top, text=info.title, bg=PANEL_BG, fg=TEXT, font=(FONT, ROW_TITLE_SIZE, "bold")).pack(side="left")
        reset = f"reset {info.reset_text}" if info.reset_text else ""
        tk.Label(top, text=reset, bg=PANEL_BG, fg=MUTED, font=(FONT, BODY_SIZE)).pack(side="right")
        track = tk.Canvas(row, height=BAR_HEIGHT + 2, bg=PANEL_BG, highlightthickness=0)
        track.pack(fill="x", pady=(3, 0))
        track.bind("<Configure>", lambda event, pct=info.used_percent, canvas=track: draw_bar(canvas, pct))
        self.bind_drag_recursive(row)
        tk.Label(
            row,
            text=f"{round(info.remaining_percent)}% left / {round(info.used_percent)}% used",
            bg=PANEL_BG,
            fg=MUTED,
            font=(FONT, BODY_SIZE),
        ).pack(anchor="w")

    def add_note(self, text: str):
        tk.Label(self.rows_frame, text=text, bg=PANEL_BG, fg=GREEN, font=(FONT, BODY_SIZE, "bold")).pack(anchor="w", pady=(3, 0))

    def render_error(self, message: str):
        self.clear_rows()
        self.plan_label.config(text="Error")
        if "Network temporarily unavailable" in message:
            message = "Network temporarily unavailable.\nAuto-refresh will retry."
        tk.Label(
            self.rows_frame,
            text=message,
            wraplength=254,
            justify="left",
            bg=PANEL_BG,
            fg=RED,
            font=(FONT, BODY_SIZE),
        ).pack(anchor="w", pady=8)
        self.status_label.config(text="failed")

    def close(self):
        self.config_data["x"] = self.winfo_x()
        self.config_data["y"] = self.winfo_y()
        save_config(self.config_data)
        self.destroy()


def draw_bar(canvas: tk.Canvas, used_percent: float):
    canvas.delete("all")
    width = max(1, canvas.winfo_width())
    height = BAR_HEIGHT
    rounded_rect(canvas, 0, 1, width, height, SURFACE_RADIUS, fill="#ececf1", outline="")
    fill_width = int(width * max(0.0, min(100.0, used_percent)) / 100)
    color = GREEN if used_percent < 75 else AMBER if used_percent < 90 else RED
    if fill_width > 0:
        rounded_rect(canvas, 0, 1, max(10, fill_width), height, SURFACE_RADIUS, fill=color, outline="")


class ParseTests(unittest.TestCase):
    def test_parse_rate_limit_and_extras(self):
        data = {
            "plan_type": "pro",
            "rate_limit": {
                "primary_window": {"used_percent": 25, "reset_at": int(time.time()) + 3600},
                "secondary_window": {"used_percent": "40"},
                "code_review_window": {"usage_percent": 10},
            },
            "additional_rate_limits": [
                {
                    "limit_name": "Codex Spark Weekly",
                    "rate_limit": {"secondary_window": {"used_percent": 62}},
                }
            ],
            "credits": {"has_credits": True, "unlimited": False, "balance": 12.5},
        }
        usage = parse_usage_json(data)
        self.assertEqual(usage.plan, "ChatGPT Pro")
        self.assertEqual(round(usage.primary.remaining_percent), 75)
        self.assertEqual(round(usage.secondary.used_percent), 40)
        self.assertEqual(round(usage.code_review.used_percent), 10)
        self.assertEqual(usage.extras[0].title, "Codex Spark Weekly")
        self.assertEqual(usage.credits, "$12.50 credits")

    def test_parse_direct_percent_fallback(self):
        usage = parse_usage_json({"plan_type": "plus", "used_percent": 7})
        self.assertEqual(usage.plan, "ChatGPT Plus")
        self.assertEqual(usage.primary.title, "Session")
        self.assertEqual(usage.primary.used_percent, 7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ParseTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    CodexFloat().mainloop()


if __name__ == "__main__":
    main()
