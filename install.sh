#!/bin/bash
# Bramblewick installer
# 将 bramblewick.py 放到 ~/.claude/，并自动注入 statusline.sh

set -e

CLAUDE_DIR="$HOME/.claude"
SCRIPT="$CLAUDE_DIR/bramblewick.py"
STATUSLINE="$CLAUDE_DIR/statusline.sh"

# 1. 复制脚本
cp "$(dirname "$0")/bramblewick.py" "$SCRIPT"
chmod +x "$SCRIPT"
echo "✓ bramblewick.py → $SCRIPT"

# 2. 修改 statusline.sh（如果存在且还没注入过）
if [ -f "$STATUSLINE" ]; then
    if grep -q "bramblewick" "$STATUSLINE"; then
        echo "✓ statusline.sh 已包含 Bramblewick，跳过"
    else
        # 在文件末尾的 echo 语句前注入
        # 找到最后一个 echo 行，在它前面插入 Bramblewick 逻辑
        python3 - "$STATUSLINE" <<'PYEOF'
import sys, re

path = sys.argv[1]
with open(path) as f:
    content = f.read()

injection = '''
# --- Bramblewick ---
BRAMBLE=$(python3 "$HOME/.claude/bramblewick.py" 2>/dev/null)
if [ -n "$BRAMBLE" ]; then
    echo "${BASE}  🐰｢${BRAMBLE}｣"
else
    echo "$BASE"
fi'''

# 把最后一个裸 echo 替换成先赋值 BASE，再走 Bramblewick 分支
# 模式：echo "..." 或 echo '...' 结尾
# 先把所有 echo "..." 改成 BASE="..."
new_content = re.sub(
    r'^(\s*)(echo\s+)(".*"|\'.*\')(\s*)$',
    lambda m: m.group(1) + 'BASE=' + m.group(3) + m.group(4),
    content,
    flags=re.MULTILINE
)

# 追加 Bramblewick 注入
new_content = new_content.rstrip() + '\n' + injection + '\n'

with open(path, 'w') as f:
    f.write(new_content)

print("✓ statusline.sh 已注入 Bramblewick")
PYEOF
    fi
else
    echo "⚠ 未找到 $STATUSLINE，请手动添加以下内容到你的 statusline 脚本末尾："
    echo ""
    echo '  BRAMBLE=$(python3 "$HOME/.claude/bramblewick.py" 2>/dev/null)'
    echo '  if [ -n "$BRAMBLE" ]; then'
    echo '      echo "${YOUR_STATUS_LINE}  🐰｢${BRAMBLE}｣"'
    echo '  else'
    echo '      echo "$YOUR_STATUS_LINE"'
    echo '  fi'
fi

echo ""
echo "🐰 Bramblewick 安装完成！下次 statusLine 刷新时她就会出现。"
echo "   首次触发立即生效，之后每 30 分钟更新一次。"
echo "   如需调整间隔，在 ~/.claude/settings.json 的 env 里加："
echo '   "BRAMBLEWICK_INTERVAL": "1800"  # 单位：秒'
