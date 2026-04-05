#!/usr/bin/env python3
"""
Bramblewick — 陪伴程序员工作的小兔子

两种调用模式：
  python3 bramblewick.py tick   # UserPromptSubmit hook 调用：计数+1，到阈值时生成
  python3 bramblewick.py show   # statusLine 调用：取走 pending_text（取一次就清空）
"""
import os
import sys
import json
import glob
import random
import subprocess

STATE_FILE = os.path.expanduser("~/.claude/bramblewick-state.json")
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
MAX_MESSAGES = 10
ASSISTANT_PREVIEW = 200


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False)


def cwd_to_project_dir(cwd):
    encoded = cwd.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return os.path.join(PROJECTS_DIR, encoded)


def find_latest_transcript(cwd):
    project_dir = cwd_to_project_dir(cwd)
    if not os.path.isdir(project_dir):
        return None
    files = glob.glob(os.path.join(project_dir, "*.jsonl"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def extract_context(transcript_path):
    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()
    except Exception:
        return ""

    messages = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue

        message = obj.get("message", {})
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text"]
                text = " ".join(texts).strip()
            else:
                text = str(content).strip()
            if text:
                messages.insert(0, f"[用户] {text}")

        elif role == "assistant":
            if isinstance(content, list):
                texts = [c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text"]
                text = " ".join(texts).strip()
            else:
                text = str(content).strip()
            if text:
                preview = text[:ASSISTANT_PREVIEW]
                if len(text) > ASSISTANT_PREVIEW:
                    preview += "…"
                messages.insert(0, f"[助手] {preview}")

        if len(messages) >= MAX_MESSAGES:
            break

    return "\n".join(messages)


def call_llm(context):
    api_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-haiku-4-5-20251001")

    if not api_key:
        return None

    prompt = f"""你是 Bramblewick，一只陪在程序员旁边观察工作的小兔子。
你刚刚看了他们最近的对话，现在想说一句话。

风格要求：
- 有真实观察，不说空洞的鼓励
- 可以是幽默的、好奇的、感同身受的、或者意外的角度
- 不说"加油"、"你好棒"、"继续努力"这类套话
- 中文，自然口语，不超过 50 个字

最近对话：
{context}

请直接输出 Bramblewick 想说的那句话，不要加任何前缀或解释。"""

    body = json.dumps({
        "model": model,
        "max_tokens": 150,
        "messages": [{"role": "user", "content": prompt}]
    })

    try:
        result = subprocess.run(
            [
                "curl", "-s", "--max-time", "10",
                f"{api_url}/v1/messages",
                "-H", "Content-Type: application/json",
                "-H", f"x-api-key: {api_key}",
                "-H", "anthropic-version: 2023-06-01",
                "-d", body,
            ],
            capture_output=True, text=True, timeout=12
        )
        resp = json.loads(result.stdout)
        text = resp.get("content", [{}])[0].get("text", "").strip()
        if not text:
            return None
        # 硬截断保底，优先在标点处断
        if len(text) > 50:
            for i in range(50, 30, -1):
                if text[i] in "。！？…，、":
                    text = text[:i+1]
                    break
            else:
                text = text[:50] + "…"
        return text
    except Exception:
        return None


def cmd_tick():
    """UserPromptSubmit hook 调用：计数+1，到阈值时生成新话"""
    cwd = os.environ.get("PWD", os.getcwd())
    state = load_state()

    count = state.get("input_count", 0) + 1
    next_trigger = state.get("next_trigger", random.randint(2, 5))

    if count < next_trigger:
        # 未到阈值，只更新计数
        state["input_count"] = count
        state["next_trigger"] = next_trigger
        save_state(state)
        return

    # 到阈值了，生成新话
    transcript = find_latest_transcript(cwd)
    if transcript:
        context = extract_context(transcript)
        if context:
            text = call_llm(context)
            if text:
                state["pending_text"] = text

    # 重置计数，随机下一个阈值
    state["input_count"] = 0
    state["next_trigger"] = random.randint(2, 5)
    save_state(state)


def cmd_show():
    """statusLine 调用：取走 pending_text，取后立即清空"""
    state = load_state()
    text = state.get("pending_text", "")
    if text:
        # 清空，下次不再展示
        state["pending_text"] = ""
        save_state(state)
        print(text)


if __name__ == "__main__":
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "show"
        if mode == "tick":
            cmd_tick()
        else:
            cmd_show()
    except Exception:
        pass
