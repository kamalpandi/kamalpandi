#!/usr/bin/env python3
"""Generate the kamalpandi/kamalpandi GitHub profile README.

Pulls live metadata from the public GitHub REST API (no dependencies beyond the
standard library) and renders a polished, static README.md.  LinkedIn-derived
profile details live in ``PROFILE`` below because LinkedIn exposes no public API.

Usage
-----
    python scripts/generate_readme.py
    GITHUB_TOKEN=ghp_... python scripts/generate_readme.py
    python scripts/generate_readme.py --check      # fail if README is stale
    python scripts/generate_readme.py --dry-run    # print, do not write
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

USERNAME = "kamalpandi"
API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

PROFILE = {
    "name": "Kamal Pandi V",
    "handle": "kamalpandi",
    "role": "Software Engineer",
    "location": "Bengaluru, India",
    "headline": "Backend Engineer · Agentic AI & RAG",
    "email": "kamalpandi123@gmail.com",
    "portfolio": "https://django-frontend-two.vercel.app/",
    "linkedin": "https://www.linkedin.com/in/kamalpandi/",
    "github": "https://github.com/kamalpandi",
    "leetcode": "https://leetcode.com/u/kamalpandi123/",
    "picoctf": "https://play.picoctf.org/users/kamal144",
    "bootdev": "https://www.boot.dev/u/helplessmodel11",
    "bio": "Coding for passion. Engineering for fun.",
}


# --------------------------------------------------------------------------- #
# Editable content
# --------------------------------------------------------------------------- #

TECH_COLORS = {
    "Python": ("3776AB", "python", "white"),
    "FastAPI": ("009688", "fastapi", "white"),
    "Django": ("092E20", "django", "white"),
    "DRF": ("A30000", None, "white"),
    "Flask": ("000000", "flask", "white"),
    "PostgreSQL": ("4169E1", "postgresql", "white"),
    "PGVector": ("4169E1", "postgresql", "white"),
    "Pinecone": ("000000", None, "white"),
    "LangChain": ("1C3C3C", "langchain", "white"),
    "LangGraph": ("1C3C3C", "langchain", "white"),
    "ChromaDB": ("FFDE2D", None, "black"),
    "Ollama": ("000000", None, "white"),
    "htmx": ("3366CC", None, "white"),
    "JWT": ("000000", "jsonwebtokens", "white"),
    "SQLite": ("003B57", "sqlite", "white"),
    "TypeScript": ("3178C6", "typescript", "white"),
    "React": ("61DAFB", "react", "black"),
    "JavaScript": ("F7DF1E", "javascript", "black"),
    "C": ("A8B9CC", "c", "black"),
    "AVR": ("A8B9CC", None, "black"),
    "ATmega328P": ("A8B9CC", None, "black"),
    "ESP8266": ("000000", "espressif", "white"),
    "UART": ("555555", None, "white"),
}


@dataclass
class Featured:
    name: str
    repo: str
    tagline: str
    description: str
    tech: list[str] = field(default_factory=list)
    live: str | None = None


FEATURED = [
    Featured(
        name="Ragworks",
        repo="Ragworks",
        tagline="Vendor-agnostic, production-ready RAG framework",
        description=(
            "Modular RAG backend with swappable vector stores, LLMs, and embedders. "
            "Develop locally with PGVector + Llama, then scale to Pinecone + OpenAI "
            "with a single env var."
        ),
        tech=["Python", "FastAPI", "PGVector", "Pinecone", "LangChain", "htmx"],
    ),
    Featured(
        name="Code Crawler",
        repo="code-crawler-ollama",
        tagline="Chat with your codebase — fully local",
        description=(
            "Index any repository and ask questions in natural language, or dispatch "
            "an autonomous LangGraph agent to improve code. Runs entirely on Ollama, "
            "so your code never leaves your machine."
        ),
        tech=["Python", "Flask", "LangGraph", "ChromaDB", "Ollama"],
    ),
    Featured(
        name="Django Multi-App API Server",
        repo="Django-api-server",
        tagline="The REST backend behind my portfolio",
        description=(
            "Django REST API with JWT auth serving Weather, Todo, and Pic-to-ASCII "
            "endpoints. Modular app-per-feature structure, deployed on PythonAnywhere."
        ),
        tech=["Python", "Django", "DRF", "JWT", "SQLite"],
    ),
    Featured(
        name="Uno Bare-Metal WiFi",
        repo="uno-baremetal-wifi",
        tagline="Bare-metal C on an Arduino Uno R3",
        description=(
            "No Arduino core, no libraries. avr-gcc talks directly to the ATmega328P "
            "over memory-mapped I/O and drives an ESP8266 WiFi shield with raw AT "
            "commands — in under 10 KB of flash."
        ),
        tech=["C", "AVR", "ATmega328P", "ESP8266", "UART"],
    ),
]

# Curated entries shown in the "More projects" table.  Any public, non-fork repo
# that is not featured and not listed here is appended automatically.
MORE = [
    {
        "repo": "RAG_code_analyzer",
        "title": "RAG Code Analyzer",
        "description": "Turns any codebase into a structured Markdown knowledge base, with SHA256-based caching.",
        "stack": "Python · Ollama · tiktoken",
    },
    {
        "repo": "Django-frontend",
        "title": "Kamal.dev Portfolio",
        "description": "A React + TypeScript portfolio with live demos and project deep-dives.",
        "stack": "React 19 · TypeScript · Vite",
    },
    {
        "repo": "Real-Time-Collaborative-Whiteboard",
        "title": "Collaborative Whiteboard",
        "description": "A shared canvas where multiple users can draw together in real time.",
        "stack": "JavaScript · WebSockets · Canvas",
    },
    {
        "repo": "Task-Tracker",
        "title": "Task Tracker",
        "description": "A small CLI task manager built for the roadmap.sh task-tracker challenge.",
        "stack": "Python · CLI",
    },
    {
        "repo": "Asteroids-Game",
        "title": "Asteroids Game",
        "description": "Classic Asteroids rebuilt with pygame and a multi-file OOP design.",
        "stack": "Python · pygame",
    },
    {
        "repo": "IoT-SonarQube",
        "title": "IoT SonarQube",
        "description": "Django REST API for IoT devices, users, and sensor readings with date filters and min/max/avg summaries.",
        "stack": "Django · DRF · PostgreSQL",
    },
    {
        "repo": "MCA_Project",
        "title": "Covid-19 Trend Forecasting",
        "description": "Covid-19 trend forecasting for Tamil Nadu using Prophet, ARIMA, and SVR.",
        "stack": "Python · Pandas · Prophet",
    },
    {
        "repo": "MCA_mini_projct",
        "title": "Face Recognition API",
        "description": "A minimal facial-recognition API built on the face_recognition package.",
        "stack": "Python · face_recognition",
    },
    {
        "repo": "Portfolio",
        "title": "Single-Page Portfolio",
        "description": "A single-page resume and project showcase.",
        "stack": "HTML · CSS",
    },
]


# --------------------------------------------------------------------------- #
# GitHub helpers
# --------------------------------------------------------------------------- #

def _curl_get(url: str, token: str | None) -> object:
    """Fallback for Python builds without SSL support (e.g. a stripped 3.14)."""
    cmd = [
        "curl",
        "-fsSL",
        "--max-time",
        "30",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        f"User-Agent: {USERNAME}-profile-readme-generator",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
    ]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=40, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise SystemExit(f"Could not reach GitHub ({url}): {detail.strip()[:300]}") from exc
    return json.loads(result.stdout)


def api_get(path: str) -> object:
    url = f"{API}{path}"
    token = os.environ.get("GITHUB_TOKEN")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-readme-generator",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"GitHub API error {exc.code} for {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        if "unknown url type" in str(exc.reason).lower() or "ssl" in str(exc.reason).lower():
            return _curl_get(url, token)
        raise SystemExit(f"Could not reach GitHub: {exc.reason}") from exc


def fetch_data() -> tuple[dict, list[dict]]:
    user = api_get(f"/users/{USERNAME}")
    repos: list[dict] = []
    page = 1
    while True:
        batch = api_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&sort=pushed")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return user, repos


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #

def badge(label: str, color: str, logo: str | None = None, logo_color: str = "white") -> str:
    slug = urllib.parse.quote(label.replace("-", "--").replace(" ", "_"), safe="")
    url = f"https://img.shields.io/badge/{slug}-{color}?style=flat-square"
    if logo:
        url += f"&logo={urllib.parse.quote(logo)}&logoColor={logo_color}"
    return f'<img src="{url}" alt="{label}" />'


def tech_badges(tech: list[str]) -> str:
    out = []
    for name in tech:
        color, logo, logo_color = TECH_COLORS.get(name, ("555555", None, "white"))
        out.append(badge(name, color, logo, logo_color))
    return " ".join(out)


def featured_card(project: Featured, repo: dict | None) -> str:
    url = f"https://github.com/{USERNAME}/{project.repo}"
    title = f'<a href="{url}"><b>{project.name}</b></a>'
    if project.live:
        title += f' &nbsp;<a href="{project.live}"><img src="https://img.shields.io/badge/live-demo-2ea043?style=flat-square" alt="Live demo" /></a>'
    pushed = ""
    if repo and repo.get("pushed_at"):
        pushed = f' · Updated {repo["pushed_at"][:10]}'
    return f"""<td width="50%" valign="top">
<h3>{title}</h3>
<p><b>{project.tagline}</b></p>
<p>{project.description}</p>
<p>{tech_badges(project.tech)}</p>
<p><sub><a href="{url}">Source on GitHub</a>{pushed}</sub></p>
</td>"""


def more_projects(repos: list[dict], featured_names: set[str]) -> list[dict]:
    by_name = {repo["name"]: repo for repo in repos}
    rows: list[dict] = []
    seen: set[str] = set()

    for item in MORE:
        if item["repo"] in by_name:
            rows.append(item)
            seen.add(item["repo"])

    # Pick up any new public repo so the profile stays current.
    extras = [
        repo
        for repo in repos
        if not repo.get("fork")
        and repo["name"] not in featured_names
        and repo["name"] not in seen
        and repo["name"] != USERNAME
        and repo.get("size", 0) > 0
    ]
    extras.sort(key=lambda repo: repo.get("pushed_at") or "", reverse=True)
    for repo in extras:
        rows.append(
            {
                "repo": repo["name"],
                "title": repo["name"].replace("-", " ").replace("_", " "),
                "description": repo.get("description") or "No description yet.",
                "stack": repo.get("language") or "—",
            }
        )
    return rows


def render(user: dict, repos: list[dict]) -> str:
    repo_index = {repo["name"]: repo for repo in repos}
    featured_names = {project.repo for project in FEATURED}
    rows = more_projects(repos, featured_names)

    cards = [featured_card(project, repo_index.get(project.repo)) for project in FEATURED]
    featured_html = (
        "<table>\n<tr>\n"
        + cards[0]
        + "\n"
        + cards[1]
        + "\n</tr>\n<tr>\n"
        + cards[2]
        + "\n"
        + cards[3]
        + "\n</tr>\n</table>"
    )

    more_table = "\n".join(
        f'| <b><a href="https://github.com/{USERNAME}/{row["repo"]}">{row["title"]}</a></b> '
        f'| {row["description"]} | {row["stack"]} |'
        for row in rows
    )

    public_repos = user.get("public_repos", len(repos))
    generated = date.today().isoformat()

    return f"""<!-- Generated by scripts/generate_readme.py — {public_repos} public repos — edit the script, not this file. -->

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:161b22,100:1f6feb&height=230&section=header&text=Kamal%20Pandi&fontSize=64&fontColor=ffffff&fontAlignY=32&desc=Backend%20Engineer%20%C2%B7%20Agentic%20AI%20%26%20RAG&descAlignY=54&descSize=20&animation=fadeIn" alt="Kamal Pandi" width="100%" />

<a href="https://github.com/{USERNAME}">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=500&size=20&duration=2800&pause=900&color=58A6FF&center=true&vCenter=true&width=750&lines=Building+production-grade+RAG+pipelines;Designing+autonomous+LLM+agents;Shipping+secure+scalable+backends;Sometimes+I+write+bare-metal+C+for+fun" alt="Typing banner" />
</a>

<p>
  <a href="{PROFILE['linkedin']}"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="{PROFILE['github']}"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
  <a href="{PROFILE['portfolio']}"><img src="https://img.shields.io/badge/Portfolio-1F6FEB?style=for-the-badge&logo=vercel&logoColor=white" alt="Portfolio" /></a>
  <a href="mailto:{PROFILE['email']}"><img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email" /></a>
</p>

<img src="https://komarev.com/ghpvc/?username={USERNAME}&style=flat-square&color=1f6feb&label=Profile+views" alt="Profile views" />

</div>

## 👋 About me

I'm a **{PROFILE['role']}** in {PROFILE['location']}, building **AI-backed enterprise integration systems**.

My work sits at the intersection of **agentic AI and workflow orchestration** — RAG pipelines, autonomous agents, and the modular backend architecture that makes AI-driven flow builders work in production.

Before the AI focus, I built secure backend systems for German enterprise clients: **fintech integrations (SEPA, Open Banking)**, **TLS-based credit bureau authentication**, and **lottery backend logic with RESTful APIs**.

- 🔭 **Currently building** — production RAG pipelines, agentic workflows, and config-driven integrations
- 🧠 **Exploring** — bare-metal C, AVR, embedded networking, and application security
- 🤝 **Open to** — collaborating on open-source RAG, agentic AI, and backend tooling
- 💬 **Ask me about** — Python, FastAPI, Django, RAG, LangGraph, Linux, application security
- ⚡ **Fun fact** — once you try Linux, there's no going back.

> `{PROFILE['bio']}`

## 🚀 Featured projects

{featured_html}

## 📦 More projects

| Project | What it does | Stack |
| :------ | :----------- | :---- |
{more_table}

<p align="right"><a href="https://github.com/{USERNAME}?tab=repositories"><b>All repositories →</b></a></p>

## 🛠️ Languages & tools

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,fastapi,django,flask,ts,react,nodejs,go,c,postgres,redis,docker,linux,bash,git,nginx,aws,azure,githubactions,vite&perline=10" alt="Languages and tools" />
</p>

<p align="center">
  <img src="https://skillicons.dev/icons?i=lua,mysql,neovim,express,opencv,pandas,postman,pytorch,html,css,pytest&perline=11" alt="More languages and tools" />
</p>

<p align="center">
  {badge("LangChain", "1C3C3C", "langchain")}
  {badge("LangGraph", "1C3C3C", "langchain")}
  {badge("Pinecone", "000000")}
  {badge("ChromaDB", "FFDE2D", None, "black")}
  {badge("pgvector", "4169E1", "postgresql")}
  {badge("Ollama", "000000")}
  {badge("llama.cpp", "0B5FFF")}
  {badge("OpenAI", "412991", "openai")}
  {badge("Hugging Face", "FFD21E", "huggingface", "black")}
  {badge("htmx", "3366CC")}
  {badge("uv", "0B5FFF", "uv")}
</p>

## 📊 GitHub at a glance

<p align="center">
  <img width="100%" src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details?username={USERNAME}&theme=tokyonight" alt="GitHub profile summary" />
</p>

<p align="center">
  <img width="49%" src="https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language?username={USERNAME}&theme=tokyonight" alt="Top languages by repo" />
  <img width="49%" src="https://github-profile-summary-cards.vercel.app/api/cards/most-commit-language?username={USERNAME}&theme=tokyonight" alt="Top languages by commit" />
</p>

<p align="center">
  <img width="100%" src="https://ghchart.rshah.org/58a6ff/{USERNAME}" alt="Contribution chart" />
</p>

## 💼 Experience

**{PROFILE['role']}** · {PROFILE['location']}

- Build AI-backed enterprise integration features: RAG pipelines, autonomous agents, workflow orchestration, and modular backend services.
- Design config-driven integration workflows that cut customer setup time by **50–75%**.
- Built secure fintech backend components — **SEPA Direct Debit**, **Open Banking**, and **TLS-based credit bureau authentication**.
- Implemented backend logic and fair-selection algorithms for a **national lottery platform**.

**MCA, Computer Applications** · The American College · 2021–2023

**Certifications** — Boot.dev Python / Backend Development (2024) · Udemy Python (2023)

## 🌱 Currently learning

<p align="left">
  <a href="{PROFILE['bootdev']}">
    <img src="https://api.boot.dev/v1/users/public/6f1a4ce8-2400-48c4-9a55-eb734a368617/thumbnail" width="150" alt="Boot.dev profile" />
  </a>
</p>

Sharpening backend fundamentals on **[Boot.dev]({PROFILE['bootdev']})** — Linux, Go, and distributed systems — while exploring bare-metal C and embedded networking.

## 🤝 Connect

<p align="center">
  <a href="{PROFILE['linkedin']}"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
  <a href="{PROFILE['github']}"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
  <a href="{PROFILE['portfolio']}"><img src="https://img.shields.io/badge/Portfolio-1F6FEB?style=for-the-badge&logo=vercel&logoColor=white" alt="Portfolio" /></a>
  <a href="mailto:{PROFILE['email']}"><img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Gmail" /></a>
</p>

<p align="center">
  <a href="{PROFILE['leetcode']}"><img src="https://img.shields.io/badge/LeetCode-FFA116?style=for-the-badge&logo=leetcode&logoColor=black" alt="LeetCode" /></a>
  <a href="{PROFILE['picoctf']}"><img src="https://img.shields.io/badge/picoCTF-1F6FEB?style=for-the-badge&logo=hackthebox&logoColor=white" alt="picoCTF" /></a>
  <a href="{PROFILE['bootdev']}"><img src="https://img.shields.io/badge/Boot.dev-0B5FFF?style=for-the-badge&logo=python&logoColor=white" alt="Boot.dev" /></a>
  <a href="mailto:kamalpandi@protonmail.com"><img src="https://img.shields.io/badge/ProtonMail-8B89CC?style=for-the-badge&logo=protonmail&logoColor=white" alt="ProtonMail" /></a>
</p>

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:1f6feb,50:161b22,100:0d1117&height=120&section=footer" alt="Footer" width="100%" />
  <sub>Generated from GitHub + LinkedIn · {generated}</sub>
</div>
"""


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if README.md is out of date")
    parser.add_argument("--dry-run", action="store_true", help="print the README instead of writing it")
    parser.add_argument("--output", type=Path, default=README, help="output path (default: README.md)")
    args = parser.parse_args()

    user, repos = fetch_data()
    content = render(user, repos)

    print(
        f"Fetched {user.get('login')} — {len(repos)} repos, "
        f"{user.get('public_repos')} public, {user.get('followers')} followers",
        file=sys.stderr,
    )

    if args.dry_run:
        print(content)
        return 0

    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if current != content:
            print(f"{args.output} is out of date; run scripts/generate_readme.py", file=sys.stderr)
            return 1
        print(f"{args.output} is up to date", file=sys.stderr)
        return 0

    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote {args.output} ({len(content):,} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
