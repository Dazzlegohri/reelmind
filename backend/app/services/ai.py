import json
import os
from typing import Any

from app.core.config import settings


# ============================================================
# LOCAL RULE-BASED FALLBACK
# ============================================================

def local_analysis(
    transcript: str,
    duration: float
) -> dict[str, Any]:

    text = transcript or ""
    lower = text.lower()

    words = text.split()
    first_words = " ".join(words[:18])

    hook = 62

    if any(
        x in lower
        for x in [
            "stop",
            "mistake",
            "secret",
            "why",
            "before",
            "don't",
            "wait",
            "how",
        ]
    ):
        hook += 15

    if duration <= 35:
        retention = 78
    elif duration <= 60:
        retention = 68
    else:
        retention = 58

    cta = (
        72
        if any(
            x in lower
            for x in [
                "follow",
                "comment",
                "save",
                "share",
            ]
        )
        else 45
    )

    score = round(
        hook * 0.30
        + retention * 0.30
        + 78 * 0.15
        + cta * 0.15
        + 70 * 0.10
    )

    issues = []

    if duration > 3 and len(first_words.split()) < 8:
        issues.append({
            "type": "hook",
            "severity": "high",
            "message": (
                "Opening has low information density. "
                "The strongest idea should appear faster."
            ),
        })

    if duration > 45:
        issues.append({
            "type": "pacing",
            "severity": "medium",
            "message": (
                "The Reel is relatively long. "
                "Consider tighter pacing and removing filler."
            ),
        })

    if cta < 60:
        issues.append({
            "type": "cta",
            "severity": "medium",
            "message": (
                "No clear audience action was detected."
            ),
        })

    return {
        "viral_score": max(0, min(100, score)),

        "scores": {
            "hook": hook,
            "retention": retention,
            "clarity": 78,
            "shareability": 70,
            "cta": cta,
        },

        "issues": issues,

        "recommendations": [
            "Lead with the strongest claim or outcome.",
            "Remove filler before the first valuable statement.",
            "Use readable captions and visual pattern interrupts.",
            "End with one clear, natural CTA.",
        ],

        "suggested_hooks": [
            "You're probably making this mistake without realizing it.",
            "I wish I knew this before I started.",
            "Stop scrolling if you want the fastest way to improve this.",
        ],
    }


# ============================================================
# OLLAMA LOCAL AI
# ============================================================

def ollama_generate(prompt: str) -> str | None:

    try:
        import requests

        url = (
            settings.OLLAMA_BASE_URL.rstrip("/")
            + "/api/generate"
        )

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
            },
        }

        response = requests.post(
            url,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        result = data.get("response")

        if result:
            print(
                "[ReelMind] AI provider used: ollama"
            )
            return result.strip()

    except Exception as e:

        print(
            f"[ReelMind] Ollama unavailable: {e}"
        )

    return None


# ============================================================
# GEMINI
# ============================================================

def gemini_generate(prompt: str) -> str | None:

    if not settings.GEMINI_API_KEY:
        return None

    try:

        from google import genai

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        result = getattr(
            response,
            "text",
            None
        )

        if result:
            print(
                "[ReelMind] AI provider used: gemini"
            )
            return result.strip()

    except Exception as e:

        print(
            f"[ReelMind] Gemini unavailable: {e}"
        )

    return None


# ============================================================
# GROQ
# ============================================================

def groq_generate(prompt: str) -> str | None:

    if not settings.GROQ_API_KEY:
        return None

    try:

        from groq import Groq

        client = Groq(
            api_key=settings.GROQ_API_KEY
        )

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are ReelMind, an expert "
                        "Instagram Reel growth agent."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
        )

        result = response.choices[0].message.content

        if result:
            print(
                "[ReelMind] AI provider used: groq"
            )
            return result.strip()

    except Exception as e:

        print(
            f"[ReelMind] Groq unavailable: {e}"
        )

    return None


# ============================================================
# OPENAI
# ============================================================

def openai_generate(prompt: str) -> str | None:

    if not settings.OPENAI_API_KEY:
        return None

    try:

        from openai import OpenAI

        client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are ReelMind, an expert "
                        "Instagram Reel growth agent."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
        )

        result = response.choices[0].message.content

        if result:
            print(
                "[ReelMind] AI provider used: openai"
            )
            return result.strip()

    except Exception as e:

        print(
            f"[ReelMind] OpenAI unavailable: {e}"
        )

    return None


# ============================================================
# AI ROUTER
# ============================================================

def ai_generate(
    prompt: str,
    task: str = "general",
) -> tuple[str, str]:

    configured = settings.AI_PROVIDER.lower()

    # --------------------------------------------------------
    # AUTO MODE
    #
    # Local Ollama is deliberately included as a fallback.
    # --------------------------------------------------------

    if configured == "auto":

        providers = [
            "gemini",
            "groq",
            "openai",
            "ollama",
        ]

    elif configured == "local":

        providers = [
            "ollama",
            "gemini",
            "groq",
            "openai",
        ]

    elif configured == "gemini":

        providers = [
            "gemini",
            "groq",
            "ollama",
            "openai",
        ]

    elif configured == "groq":

        providers = [
            "groq",
            "gemini",
            "ollama",
            "openai",
        ]

    elif configured == "openai":

        providers = [
            "openai",
            "gemini",
            "groq",
            "ollama",
        ]

    else:

        providers = [
            "ollama",
            "gemini",
            "groq",
            "openai",
        ]

    for provider in providers:

        if provider == "ollama":
            result = ollama_generate(prompt)

        elif provider == "gemini":
            result = gemini_generate(prompt)

        elif provider == "groq":
            result = groq_generate(prompt)

        elif provider == "openai":
            result = openai_generate(prompt)

        else:
            result = None

        if result:
            return result, provider

    return "", "local"


# ============================================================
# LLM REEL ANALYSIS
# ============================================================

def analyze_with_llm(
    transcript: str,
    duration: float
) -> dict[str, Any]:

    # No speech/transcript = don't waste AI call
    if not transcript.strip():

        return local_analysis(
            transcript,
            duration
        )

    prompt = f"""
You are ReelMind, an expert Instagram Reel growth analyst.

Analyze this short-form video transcript.

Duration:
{duration:.1f} seconds

Transcript:
{transcript[:12000]}

Return ONLY valid JSON.

Schema:

{{
  "viral_score": 0,
  "scores": {{
    "hook": 0,
    "retention": 0,
    "clarity": 0,
    "shareability": 0,
    "cta": 0
  }},
  "issues": [
    {{
      "type": "hook|pacing|clarity|cta|content",
      "severity": "low|medium|high",
      "message": "specific issue"
    }}
  ],
  "recommendations": [
    "specific recommendation"
  ],
  "suggested_hooks": [
    "better hook"
  ]
}}

Rules:

- Scores must be integers from 0 to 100.
- Never guarantee virality.
- Base the analysis on the actual transcript.
- Avoid generic advice.
- Give practical creator-focused recommendations.
"""

    result, provider = ai_generate(
        prompt,
        task="analysis"
    )

    if not result:

        print(
            "[ReelMind] All AI providers unavailable. "
            "Using deterministic local analysis."
        )

        return local_analysis(
            transcript,
            duration
        )

    try:

        cleaned = result.strip()

        if cleaned.startswith("```"):

            cleaned = (
                cleaned
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        data = json.loads(cleaned)

        data["_ai_provider"] = provider

        return data

    except Exception as e:

        print(
            f"[ReelMind] AI returned invalid JSON: {e}"
        )

        return local_analysis(
            transcript,
            duration
        )


# ============================================================
# CHAT
# ============================================================

def chat(
    message: str,
    analysis: dict[str, Any] | None
) -> str:

    context = json.dumps(
        analysis or {},
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are ReelMind, an AI growth agent for Instagram Reels.

You are talking directly to a creator.

REEL ANALYSIS:

{context}

USER QUESTION:

{message}

Instructions:

1. Answer the exact question.
2. Be concise but useful.
3. Give concrete suggestions.
4. If the user asks about the hook, give improved hooks.
5. If the user asks about CTA, give CTA options.
6. If the user asks about retention, give editing/content suggestions.
7. Never guarantee virality.
8. Never claim that a video was edited unless the editing system actually edited it.
9. If the user asks to fix the Reel, explain what changes should be made.
"""

    result, provider = ai_generate(
        prompt,
        task="chat"
    )

    if result:
        return result

    # ========================================================
    # LOCAL CHAT FALLBACK
    # ========================================================

    score = (
        analysis or {}
    ).get(
        "viral_score",
        "unknown"
    )

    issues = (
        analysis or {}
    ).get(
        "issues",
        []
    )

    recommendations = (
        analysis or {}
    ).get(
        "recommendations",
        []
    )

    hooks = (
        analysis or {}
    ).get(
        "suggested_hooks",
        []
    )

    text = message.lower()

    # --------------------------------------------------------
    # ISSUE QUESTION
    # --------------------------------------------------------

    if any(
        x in text
        for x in [
            "issue",
            "problem",
            "kya galat",
            "kya dikkat",
        ]
    ):

        if issues:

            lines = [
                f"Current ReelMind score: {score}/100.",
                "",
                "Main issues:",
            ]

            for issue in issues:

                lines.append(
                    f"• {issue.get('type', 'Issue').title()}: "
                    f"{issue.get('message', '')}"
                )

            return "\n".join(lines)

        return (
            f"Current ReelMind score: {score}/100. "
            "No major issues were detected."
        )

    # --------------------------------------------------------
    # HOOK
    # --------------------------------------------------------

    if (
        "hook" in text
        or "opening" in text
    ):

        if hooks:

            return (
                "Try these hooks:\n\n"
                + "\n".join(
                    f"• {hook}"
                    for hook in hooks
                )
            )

        return (
            "Start with the strongest claim, "
            "result or curiosity gap."
        )

    # --------------------------------------------------------
    # CTA
    # --------------------------------------------------------

    if (
        "cta" in text
        or "call to action" in text
    ):

        return (
            "Try one of these CTAs:\n\n"
            "• Save this for later.\n"
            "• Which one would you choose? Comment below.\n"
            "• Follow for more practical tips."
        )

    # --------------------------------------------------------
    # IMPROVEMENT
    # --------------------------------------------------------

    if any(
        x in text
        for x in [
            "fix",
            "improve",
            "optimize",
        ]
    ):

        if recommendations:

            return (
                "I'd prioritize these changes:\n\n"
                + "\n".join(
                    f"• {item}"
                    for item in recommendations[:4]
                )
            )

        return (
            "I'd first improve the hook, "
            "tighten pacing, remove unnecessary pauses "
            "and finish with one clear CTA."
        )

    return (
        f"Your current ReelMind score is {score}/100. "
        "I can help improve the hook, pacing, retention, "
        "CTA, captions and overall structure."
    )