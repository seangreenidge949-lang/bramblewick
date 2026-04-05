#!/bin/bash
# Bramblewick installer

set -e

CLAUDE_DIR="$HOME/.claude"
SCRIPT="$CLAUDE_DIR/bramblewick.py"
STATUSLINE="$CLAUDE_DIR/statusline.sh"
SETTINGS="$CLAUDE_DIR/settings.json"

# 1. 复制脚本
cp "$(dirname "$0")/bramblewick.py" "$SCRIPT"
chmod +x "$SCRIPT"
echo "✓ bramblewick.py → $SCRIPT"

# 2. 注入 statusline.sh
if [ -f "$STATUSLINE" ]; then
    if grep -q "bramblewick" "$STATUSLINE"; then
        echo "✓ statusline.sh 已包含 Bramblewick，跳过"
    else
        python3 - "$STATUSLINE" <<'PYEOF'
import sys, re
path = sys.argv[1]
with open(path) as f:
    content = f.read()
injection = """
# --- Bramblewick ---
BRAMBLE=$(python3 "$HOME/.claude/bramblewick.py" show 2>/dev/null)
if [ -n "$BRAMBLE" ]; then
    echo "${BASE}  🐰｢${BRAMBLE}｣"
else
    echo "$BASE"
fi"""
new_content = re.sub(
    r'^(\s*)(echo\s+)(".*"|\'.*\')(\s*)$',
    lambda m: m.group(1) + 'BASE=' + m.group(3) + m.group(4),
    content, flags=re.MULTILINE
)
new_content = new_content.rstrip() + '\n' + injection + '\n'
with open(path, 'w') as f:
    f.write(new_content)
print("✓ statusline.sh 已注入 Bramblewick")
PYEOF
    fi
else
    echo "⚠ 未找到 statusline.sh，请手动在状态栏脚本末尾添加："
    echo '  BRAMBLE=$(python3 "$HOME/.claude/bramblewick.py" show 2>/dev/null)'
    echo '  [ -n "$BRAMBLE" ] && echo "${YOUR_LINE}  🐰｢${BRAMBLE}｣" || echo "$YOUR_LINE"'
fi

# 3. 注入 UserPromptSubmit hook 到 settings.json
if [ -f "$SETTINGS" ]; then
    if grep -q "bramblewick" "$SETTINGS"; then
        echo "✓ settings.json 已包含 Bramblewick hook，跳过"
    else
        python3 - "$SETTINGS" <<'PYEOF'
import sys, json
path = sys.argv[1]
with open(path) as f:
    settings = json.load(f)
hook = {"matcher": "", "hooks": [{"type": "command", "command": "python3 ~/.claude/bramblewick.py tick", "timeout": 12}]}
hooks = settings.setdefault("hooks", {})
ups = hooks.setdefault("UserPromptSubmit", [])
ups.append(hook)
with open(path, 'w') as f:
    json.dump(settings, f, ensure_ascii=False, indent=2)
print("✓ settings.json 已注入 UserPromptSubmit hook")
PYEOF
    fi
else
    echo "⚠ 未找到 settings.json，请手动在 UserPromptSubmit hooks 里添加："
    echo '  {"type": "command", "command": "python3 ~/.claude/bramblewick.py tick", "timeout": 12}'
fi

echo ""
echo "🐰 Bramblewick 安装完成！发 2-5 条消息后她就会出现在状态栏里。"
echo "   说完即消，不重复展示。"
