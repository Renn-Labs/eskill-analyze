#!/usr/bin/env bash
# eskill-analyze installer — links the three-tier suite into your harness skills dir.
#
#   ./install.sh                      # symlink into ~/.claude/skills/
#   ./install.sh --copy               # copy instead of symlink
#   ./install.sh --harness codex grok # ALSO link into ~/.codex/skills and ~/.grok/skills
#   ./install.sh --uninstall          # remove installed skills/links
#
# The canonical copy always lands in ~/.claude/skills/ so the inter-skill
# "~/.claude/skills/..." references resolve no matter which harness invokes them.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/skills" && pwd)"
SKILLS=(eskill-common eskill-analyze esat esat-fleet)

MODE=symlink
ACTION=install
EXTRA_HARNESSES=()

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy; shift ;;
    --uninstall) ACTION=uninstall; shift ;;
    --harness)
      shift
      while [ $# -gt 0 ] && [[ "$1" != --* ]]; do EXTRA_HARNESSES+=("$1"); shift; done ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Build the target list. ~/.claude is always canonical.
TARGETS=("$HOME/.claude/skills")
for h in "${EXTRA_HARNESSES[@]:-}"; do
  [ -n "$h" ] || continue
  case "$h" in
    claude) : ;;  # already present
    *) TARGETS+=("$HOME/.$h/skills") ;;
  esac
done

for dest in "${TARGETS[@]}"; do
  mkdir -p "$dest"
  for s in "${SKILLS[@]}"; do
    tgt="$dest/$s"
    if [ "$ACTION" = uninstall ]; then
      if [ -L "$tgt" ] || [ -e "$tgt" ]; then rm -rf "$tgt"; echo "removed  $tgt"; fi
      continue
    fi
    # install
    [ -e "$tgt" ] || [ -L "$tgt" ] && rm -rf "$tgt"
    if [ "$MODE" = copy ]; then
      cp -R "$SRC/$s" "$tgt"; echo "copied   $SRC/$s -> $tgt"
    else
      ln -s "$SRC/$s" "$tgt"; echo "linked   $tgt -> $SRC/$s"
    fi
  done
done

if [ "$ACTION" = install ]; then
  echo
  echo "Done. Invoke inside your harness:  /esa   /esat   /esat-fleet"
fi
