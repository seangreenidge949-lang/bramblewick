# 🐰 Bramblewick

A small rabbit companion for Claude Code. She sits quietly, watches what you're working on, and occasionally shares a witty observation in your status bar.

```
📋 brainstorming | 🧠 ctx 45% | ↑12k ↓8k  🐰｢你已经问了三遍同一个问题了，要不要先睡一觉？｣
```

## How it works

Every 2–5 messages (random), Bramblewick reads your current session transcript, passes the recent conversation to Claude Haiku, and generates one contextual comment — max 50 characters, no empty encouragement, just honest observations.

The comment appears in your status bar once, then disappears. She doesn't repeat herself.

Between triggers, she costs zero tokens. She only speaks when she has something to say.

## Requirements

- Claude Code with `statusLine` configured
- Python 3
- `curl`
- `ANTHROPIC_API_KEY` set in your environment or `~/.claude/settings.json`

## Install

```bash
git clone https://github.com/seangreenidge949-lang/bramblewick
cd bramblewick
bash install.sh
```

That's it. Bramblewick will appear the next time your status bar refreshes.

## Adjust trigger frequency

Default is every 2–5 messages (random). No configuration needed — the randomness keeps it feeling natural.

## Manual reset

To force an immediate new comment:

```bash
rm ~/.claude/bramblewick-state.json
```
