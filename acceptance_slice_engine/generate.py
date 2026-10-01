"""Generation backends and acceptance-slice prompt for Acceptance Slice Engine v0."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request

from .validate import REQUIRED_HEADINGS

XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-4.7-build-fast"
GROK_BIN_DIR = os.path.join(os.path.expanduser("~"), ".grok", "bin")

FIRST_HEADING = "## 工单目标"
HEADING_BLOCK = "\n".join(REQUIRED_HEADINGS)

SYSTEM_PROMPT = f"""你是验收切片撰写器。把一份范围说明或 PRD（以及可选约束）写成一份可以直接派给 Eng 的验收切片 Markdown。只输出这份 Markdown，不要前言、后记、解释、问候，也不要在标题之外另起一段开场白。

必须且只能使用下面 6 个 H2。顺序固定，文字必须逐字相同，不得翻译、改写、增删标点或空格，也不得改成别的标题级别：

{HEADING_BLOCK}

内容规则：
- 全文中文。路径、码值、列名、仓库名和 sev 级别保留材料中的原文，不要为了“全中文”把它们翻译掉。
- 不要用 markdown 代码围栏把整篇文档包起来。
- 「工单目标」写清本单要交付的可观察结果：谁在什么前提下能看到什么。不写实现步骤，不替 Eng 做技术选型。
- 「验收条目」使用 `- [ ]` 写成可勾选条目。每一条都要可测，并且失败时能被观察：写明动作、期望结果、以及怎样算失败。禁止空话，例如「体验良好」「尽快完成」「适当优化」「基本可用」「符合预期」。
- 「非本单 / 明确不做」必须非空。列出本单明确不做、但容易被顺手做进去的事项。
- 「风险与 sev 提示」写出验收若失败会误伤什么，并带上 sev 提示（sev-1、sev-2 或 sev-3）。只写风险和可观察的失败信号，不展开实现方案。
- 「给实现的边界」只写仓库路径和交付形态约束。材料写了仓路径、目录或入口形态，就按材料写。材料没有指定语言、框架、数据库或云厂商时，写「材料未指定」。不要替 Eng 点名技术栈，不要建议该用哪个库或哪家云。
- 「待确认的开放问题」只列材料没写死、而且会改变验收判定的问题。没有这类问题时，该节正文只写「无」，不要留空，也不要编造问题。
- 不要宣称本单包含登录、支付、自动建 Issue、获客或营销，也不要出现「已可售」或同类可售承诺。这些事项若需要出现，只能写在「非本单 / 明确不做」里，作为不做的内容。
- 若提供了约束，遵守约束。

标题保真：
- 材料中的第三方 `## …` 标题保持原文 verbatim。
- 不得把本引擎六个 H2 文案投射进对外部系统、上游文档或材料本身的描述。引用第三方标题时用材料原文，不得改写成本引擎六块标题。
- 引用第三方标题时放在正文中（可用行内代码），不要把它们写成额外的 H2。本引擎输出结构仍必须且只能是上述六个 H2，顺序不变。
"""

USER_TEMPLATE = """请根据下面的范围/PRD 和约束，生成可派给 Eng 的验收切片。

# 范围/PRD
{scope}

# 约束
{constraints}
"""


def build_user_prompt(scope: str, constraints: str) -> str:
    constraints_text = constraints.strip() if constraints and constraints.strip() else "（无）"
    return USER_TEMPLATE.format(
        scope=scope.strip(),
        constraints=constraints_text,
    )


def combined_prompt(scope: str, constraints: str) -> str:
    return SYSTEM_PROMPT + "\n\n" + build_user_prompt(scope, constraints)


def strip_wrapping_fences(text: str) -> str:
    """Remove a single markdown fence wrapping the whole document, if present."""
    body = text.strip()
    if not body.startswith("```"):
        return body
    lines = body.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def strip_leading_preamble(markdown: str) -> str:
    """Slice from the first exact ``## 工单目标`` so the file starts at that heading."""
    idx = markdown.find(FIRST_HEADING)
    if idx == -1:
        return markdown
    return markdown[idx:].lstrip()


def generate(scope: str, constraints: str = "") -> str:
    """Generate acceptance-slice markdown via xAI API (if XAI_API_KEY) or grok CLI."""
    api_key = os.environ.get("XAI_API_KEY", "").strip()
    if api_key:
        return _generate_via_api(scope, constraints, api_key)
    return _generate_via_grok_cli(scope, constraints)


def _generate_via_api(scope: str, constraints: str, api_key: str) -> str:
    payload = {
        "model": XAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(scope, constraints)},
        ],
        "stream": False,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        XAI_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI API HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"xAI API request failed: {exc}") from exc

    try:
        body = json.loads(raw)
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"xAI API returned unexpected payload: {raw[:2000]}") from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("xAI API returned empty content")
    return content


def _generate_via_grok_cli(scope: str, constraints: str) -> str:
    env = os.environ.copy()
    env["PATH"] = GROK_BIN_DIR + os.pathsep + env.get("PATH", "")
    prompt = combined_prompt(scope, constraints)
    cmd = [
        "grok",
        "-p",
        prompt,
        "-m",
        XAI_MODEL,
        "--effort",
        "xhigh",
        "--always-approve",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=600,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "grok CLI not found. Set XAI_API_KEY or install grok at ~/.grok/bin"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("grok CLI timed out") from exc

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"grok CLI failed (exit {result.returncode}): {err}")

    stdout = (result.stdout or "").strip()
    if not stdout:
        raise RuntimeError("grok CLI returned empty stdout")
    return stdout
