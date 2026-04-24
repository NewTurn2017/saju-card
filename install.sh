#!/usr/bin/env bash
# saju-card one-shot installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/NewTurn2017/saju-card/main/install.sh | bash
#
# What it does:
#   1. Verifies prerequisites: uv, codex >= 0.121.0, Codex OAuth login
#   2. Installs the `saju-card` CLI globally via uv tool install
#   3. Registers the saju-card skill for both Codex and Claude Code
#   4. Runs a smoke check
#
# Safe to re-run.

set -euo pipefail

REPO_URL="https://github.com/NewTurn2017/saju-card"
RAW_URL="https://raw.githubusercontent.com/NewTurn2017/saju-card/main"
SKILL_NAME="saju-card"
CODEX_SKILL_DIR="$HOME/.codex/skills/$SKILL_NAME"
CLAUDE_SKILL_DIR="$HOME/.claude/skills/$SKILL_NAME"

color() { printf "\033[%sm%s\033[0m" "$1" "$2"; }
ok() { echo "  $(color 32 "OK") $1"; }
fail() { echo "  $(color 31 "ERROR") $1" >&2; exit 1; }
step() { echo; echo "$(color 36 "==>") $1"; }

install_skill_files() {
  local dest="$1"
  mkdir -p "$dest/agents"
  curl -fsSL "$RAW_URL/SKILL.md" -o "$dest/SKILL.md"
  curl -fsSL "$RAW_URL/agents/openai.yaml" -o "$dest/agents/openai.yaml"
}

step "1/4  Prerequisite check"

if ! command -v uv >/dev/null 2>&1; then
  fail "uv not found. Install it first: brew install uv  (or see https://github.com/astral-sh/uv)"
fi
ok "uv $(uv --version | awk '{print $2}')"

if ! command -v codex >/dev/null 2>&1; then
  fail "codex CLI not found. Install it first: npm install -g @openai/codex"
fi

CODEX_VER="$(codex --version 2>/dev/null | awk '{print $2}' | head -1)"
if [ -z "$CODEX_VER" ]; then
  fail "could not parse codex version"
fi

if [[ "$CODEX_VER" =~ ^0\.([0-9]+)\. ]]; then
  MINOR="${BASH_REMATCH[1]}"
  if [ "$MINOR" -lt 121 ]; then
    fail "codex $CODEX_VER is too old. Upgrade with: npm install -g @openai/codex@latest"
  fi
fi
ok "codex $CODEX_VER"

if ! LOGIN_STATUS="$(codex login status 2>&1)"; then
  fail "codex is not logged in. Run: codex login  (choose ChatGPT/OAuth)"
fi
ok "codex login: $(echo "$LOGIN_STATUS" | head -1)"

if [ -n "${CODEX_API_KEY:-}" ]; then
  fail "CODEX_API_KEY is set. Unset it first so Codex uses ChatGPT/OAuth: unset CODEX_API_KEY"
fi

step "2/4  Install saju-card CLI"
uv tool install --reinstall "git+$REPO_URL" >/dev/null 2>&1 || uv tool install "git+$REPO_URL"
ok "saju-card $(saju-card --version | awk '{print $2}')"

step "3/4  Register Codex and Claude skills"
install_skill_files "$CODEX_SKILL_DIR"
ok "Codex skill: $CODEX_SKILL_DIR/SKILL.md"

install_skill_files "$CLAUDE_SKILL_DIR"
ok "Claude Code skill: $CLAUDE_SKILL_DIR/SKILL.md"

step "4/4  Smoke check"
saju-card --help | head -1 | grep -q "saju-card" && ok "saju-card CLI responds to --help"

echo
echo "$(color 32 "saju-card is ready.")"
echo
echo "Try:"
echo "  saju-card --name \"김하늘\" --birth \"1994년 3월 20일 오전 9시 30분, 양력\" --question \"올해 이직해도 괜찮을까?\" --output ./out"
echo
echo "Restart Codex or Claude Code if the new skill is not visible yet."
