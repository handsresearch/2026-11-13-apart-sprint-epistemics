# Source before running Inspect:  source scripts/env.sh
# - Maps the environment's MY_ANTHROPIC_API_KEY to the name Inspect reads.
# - Unsets ANTHROPIC_BASE_URL, which the Claude cloud container pre-sets for
#   Claude Code itself; Inspect must talk to api.anthropic.com directly.
if [ -n "${MY_ANTHROPIC_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  export ANTHROPIC_API_KEY="$MY_ANTHROPIC_API_KEY"
fi
unset ANTHROPIC_BASE_URL
for v in ANTHROPIC_API_KEY OPENROUTER_API_KEY; do
  if [ -n "${!v:-}" ]; then echo "$v: set"; else echo "$v: NOT set"; fi
done
