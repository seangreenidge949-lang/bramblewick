#!/usr/bin/env python3
"""
Bramblewick — 陪伴程序员工作的小兔子
每隔 30 分钟读取当前会话 transcript，用 Haiku 生成一句有情境的碎碎念。
"""
import os
import sys
import json
import glob
import subprocess
from datetime import datetime, timezone, timedelta

# --- 配置 ---
INTERVAL_SECONDS = int(os.environ.get("BRAMBLEWICK_INTERVAL", "1800"))  # 默认 30 分钟
STATE_FILE = os.path.expanduser("~/.claude/bramblewick-state.json")
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
MAX_MESSAGES = 10       # 最近读取的消息条数
ASSISTANT_PREVIEW = 200  # assistant 消息最多读取的字符数


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(text):
    now = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump({"last_time": now, "last_text": text}, f, ensure_ascii=False)


def seconds_since_last(state):
    last = state.get("last_time")
    if not last:
        return float("inf")
    try:
        last_dt = datetime.fromisoformat(last)
        now = datetime.now(timezone.utc)
        return (now - last_dt).total_seconds()
    except Exception:
        return float("inf")


def cwd_to_project_dir(cwd):
    """将当前目录路径转换为 ~/.claude/projects/ 下的目录名"""
    # /Users/siyucheng/foo → -Users-siyucheng-foo
    encoded = cwd.replace("/", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return os.path.join(PROJECTS_DIR, encoded)


def find_latest_transcript(cwd):
    """找到当前 cwd 对应的最新 transcript .jsonl 文件"""
    project_dir = cwd_to_project_dir(cwd)
    if not os.path.isdir(project_dir):
        return None
    files = glob.glob(os.path.join(project_dir, "*.jsonl"))
    if not files:
        return None
    # 按修改时间排序，取最新
    return max(files, key=os.path.getmtime)


def extract_context(transcript_path):
    """从 transcript 提取最近 MAX_MESSAGES 条消息"""
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

        msg_type = obj.get("type")
        message = obj.get("message", {})
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            # user 消息：提取文本内容，全量
            if isinstance(content, list):
                texts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        texts.append(c.get("text", ""))
                text = " ".join(texts).strip()
            else:
                text = str(content).strip()
            if text:
                messages.insert(0, f"[用户] {text}")

        elif role == "assistant":
            # assistant 消息：只取文本块的前 ASSISTANT_PREVIEW 字
            if isinstance(content, list):
                texts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        texts.append(c.get("text", ""))
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
    """调用 Haiku 生成 Bramblewick 的碎碎念"""
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


def main():
    cwd = os.environ.get("PWD", os.getcwd())
    state = load_state()
    elapsed = seconds_since_last(state)

    # 未到触发时间 → 直接输出缓存
    if elapsed < INTERVAL_SECONDS:
        cached = state.get("last_text", "")
        if cached:
            print(cached)
        return

    # 到时间了 → 读 transcript，生成新话
    transcript = find_latest_transcript(cwd)
    if not transcript:
        # 没有 transcript，静默
        cached = state.get("last_text", "")
        if cached:
            print(cached)
        return

    context = extract_context(transcript)
    if not context:
        cached = state.get("last_text", "")
        if cached:
            print(cached)
        return

    text = call_llm(context)
    if not text:
        # LLM 失败，保留缓存
        cached = state.get("last_text", "")
        if cached:
            print(cached)
        return

    save_state(text)
    print(text)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # 任何未捕获异常都静默，不破坏 statusLine
        pass
