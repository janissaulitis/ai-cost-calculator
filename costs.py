"""What an AI task costs to run each month, on each model, against the staff time it saves.

Prices are the providers' published standard rates per million tokens (no batch or cache discounts), checked on
PRICES_CHECKED. Token counts per item are typical sizes and can be changed in the app. One token is about
three quarters of an English word; Latvian and other languages with long words use more.
"""
from __future__ import annotations

PRICES_CHECKED = "13 Nov 2026"
USD_TO_EUR = 0.89  # 1 EUR ≈ 1.12 USD on the day prices were checked

# name, provider, tier, $ per 1M input, $ per 1M output, note, source
MODELS = [
    ("Claude Haiku 5.5", "Anthropic", "fast", 0.10, 0.50, "prompts under 100k tokens; 5× more above that",
     "https://platform.claude.com/docs/en/about-claude/pricing"),
    ("Claude Sonnet 5.5", "Anthropic", "strong", 2.00, 10.00, "", "https://platform.claude.com/docs/en/about-claude/pricing"),
    ("Claude Opus 5.5", "Anthropic", "best", 4.00, 20.00, "", "https://platform.claude.com/docs/en/about-claude/pricing"),
    ("Gemini 3.5 Flash-Lite", "Google", "fast", 0.30, 2.50, "free tier available", "https://ai.google.dev/pricing"),
    ("Gemini 3.8 Flash", "Google", "strong", 0.75, 3.75, "free tier available; price doubles on 1 Jan 2027",
     "https://ai.google.dev/pricing"),
    ("Gemini 4 Argon", "Google", "best", 2.00, 10.00, "price doubles on 1 Dec 2026", "https://ai.google.dev/pricing"),
    ("GPT-5.4 nano", "OpenAI", "fast", 0.20, 1.25, "", "https://developers.openai.com/api/docs/pricing"),
    ("GPT-5.4 mini", "OpenAI", "strong", 0.75, 4.50, "", "https://developers.openai.com/api/docs/pricing"),
    ("GPT-6 Astra", "OpenAI", "best", 10.00, 50.00, "", "https://developers.openai.com/api/docs/pricing"),
]
TIERS = {"fast": "Fast and cheap", "strong": "Strong all-rounder", "best": "Top model"}

# key: label, unit, default volume, tokens in, tokens out, staff minutes per item, smallest tier that does it well, note
TASKS = {
    "emails": ("Sort customer emails and draft replies", "emails a month", 2000, 900, 350, 3.0, "fast",
               "Email plus instructions in, category and a short draft out."),
    "documents": ("Read statements, invoices or contracts", "documents a month", 500, 6000, 800, 8.0, "strong",
                  "A 3–4 page document as text in, the key fields out."),
    "chat": ("Answer customer chat from your help pages", "conversations a month", 3000, 4000, 600, 4.0, "strong",
             "Help-page excerpts and a 5-message chat in, answers out."),
    "content": ("Write product texts and posts", "texts a month", 200, 1200, 700, 20.0, "strong",
                "Brief and tone guide in, a 400-word text out."),
    "meetings": ("Summarise meetings", "meeting hours a month", 40, 12000, 900, 25.0, "strong",
                 "An hour's transcript in, summary and action points out."),
    "translate": ("Translate texts", "pages a month", 300, 900, 900, 15.0, "strong",
                  "One page in, the same page in another language out."),
}


def monthly(volume: float, tin: float, tout: float, price_in: float, price_out: float, fx: float = USD_TO_EUR) -> float:
    """€ a month for `volume` items of `tin` input and `tout` output tokens."""
    return volume * (tin * price_in + tout * price_out) / 1e6 * fx


def compare(volume, tin, tout, minutes, hourly, automated, min_tier="fast", fx=USD_TO_EUR, review_minutes=0.0,
            platform=0.0, setup=0.0) -> dict:
    """Everything a month: AI bill, hosting/tools, and the staff time spent checking the AI's work."""
    order = ["fast", "strong", "best"]
    rows = []
    for name, prov, tier, pi, po, note, src in MODELS:
        cost = monthly(volume, tin, tout, pi, po, fx)
        rows.append({"model": name, "provider": prov, "tier": tier, "cost": cost, "per_item": cost / max(volume, 1),
                     "suited": order.index(tier) >= order.index(min_tier), "note": note, "source": src})
    rows.sort(key=lambda r: r["cost"])
    saved_hours = volume * minutes / 60 * automated
    saved = saved_hours * hourly
    pick = next(r for r in rows if r["suited"])
    review = volume * review_minutes / 60 * hourly
    running = pick["cost"] + platform + review
    net = saved - running
    return {"rows": rows, "pick": pick, "saved_hours": saved_hours, "saved": saved, "review": review,
            "platform": platform, "running": running, "net": net, "setup": setup,
            "payback": setup / net if net > 0 else float("inf"),
            "ai_share": pick["cost"] / running if running else 0.0}
