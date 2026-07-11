#!/usr/bin/env bash
# eskill-analyze installer — links the frontier analysis suite into your harness skills dir.
#
#   ./install.sh                      # symlink into ~/.claude/skills/
#   ./install.sh --copy               # copy instead of symlink
#   ./install.sh --harness codex grok # ALSO link into ~/.codex/skills and ~/.grok/skills
#   ./install.sh --uninstall          # remove installed skills/links
#   ./install.sh --force              # replace/remove a colliding foreign path
#
# The canonical copy always lands in ~/.claude/skills/ so the inter-skill
# "~/.claude/skills/..." references resolve no matter which harness invokes them.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/skills" && pwd)"
SKILLS=(eskill-common eskill-analyze esa esat esat-fleet esat-frontier)
OWNERSHIP_MARKER=.eskill-analyze-installed

MODE=symlink
ACTION=install
FORCE=0
EXTRA_HARNESSES=()
LOCKS=()
STAGES=()
STAGE_TARGETS=()
STAGE_SKILLS=()
SWAPPED_TARGETS=()
SWAPPED_BACKUPS=()
COMMIT_ACTIVE=0
COMMIT_COMPLETE=0

_target_exists() {
  [ -L "$1" ] || [ -e "$1" ]
}

_rollback_swaps() {
  local i tgt backup
  for ((i=${#SWAPPED_TARGETS[@]} - 1; i >= 0; i--)); do
    tgt="${SWAPPED_TARGETS[$i]}"
    backup="${SWAPPED_BACKUPS[$i]}"
    _target_exists "$tgt" && rm -rf -- "$tgt"
    if [ -n "$backup" ] && _target_exists "$backup"; then
      if ! mv "$backup" "$tgt"; then
        echo "rollback failed; original remains at: $backup" >&2
      fi
    fi
  done
}

_cleanup() {
  local p
  if [ "$COMMIT_ACTIVE" -eq 1 ] && [ "$COMMIT_COMPLETE" -ne 1 ]; then
    _rollback_swaps
  fi
  for p in "${STAGES[@]:-}"; do [ -n "$p" ] && rm -rf -- "$p"; done
  if [ "$COMMIT_COMPLETE" -eq 1 ]; then
    for p in "${SWAPPED_BACKUPS[@]:-}"; do [ -n "$p" ] && rm -rf -- "$p"; done
  fi
  for p in "${LOCKS[@]:-}"; do
    if [ -n "$p" ]; then rmdir "$p" 2>/dev/null || true; fi
  done
}
trap _cleanup EXIT

_target_owned() {
  local tgt="$1" src_skill="$2" skill="$3"
  if [ -L "$tgt" ]; then
    [ "$(readlink "$tgt")" = "$src_skill" ]
    return
  fi
  [ -d "$tgt" ] && [ -f "$tgt/$OWNERSHIP_MARKER" ] &&
    [ "$(cat "$tgt/$OWNERSHIP_MARKER")" = "eskill-analyze:$skill" ]
}

# Only claude|codex|grok may be interpolated into $HOME/.$h/skills.
_validate_harness() {
  local h="$1"
  case "$h" in
    claude|codex|grok) return 0 ;;
    *)
      echo "invalid --harness value: $h (allowed: claude, codex, grok)" >&2
      exit 2
      ;;
  esac
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy; shift ;;
    --uninstall) ACTION=uninstall; shift ;;
    --force) FORCE=1; shift ;;
    --harness)
      shift
      while [ $# -gt 0 ] && [[ "$1" != --* ]]; do
        _validate_harness "$1"
        EXTRA_HARNESSES+=("$1")
        shift
      done ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Build the target list. ~/.claude is always canonical.
TARGETS=("$HOME/.claude/skills")
for h in "${EXTRA_HARNESSES[@]:-}"; do
  [ -n "$h" ] || continue
  _validate_harness "$h"  # belt-and-suspenders before any path use
  case "$h" in
    claude) : ;;  # already present
    codex|grok) TARGETS+=("$HOME/.$h/skills") ;;
  esac
done

# Serialize each destination so concurrent installers cannot interleave
# check/remove/create operations or make `ln` follow a just-created directory.
for dest in "${TARGETS[@]}"; do
  mkdir -p "$dest"
  lock="$dest/.eskill-analyze-install.lock"
  if ! mkdir "$lock" 2>/dev/null; then
    echo "another eskill-analyze install is active (or stale lock exists): $lock" >&2
    exit 4
  fi
  LOCKS+=("$lock")
done

# Refuse every foreign install collision before mutating any skill target.
if [ "$ACTION" = install ] && [ "$FORCE" -ne 1 ]; then
  for dest in "${TARGETS[@]}"; do
    for s in "${SKILLS[@]}"; do
      tgt="$dest/$s"
      if _target_exists "$tgt" && ! _target_owned "$tgt" "$SRC/$s" "$s"; then
        echo "refusing to replace unowned path: $tgt (use --force to replace)" >&2
        exit 3
      fi
    done
  done
fi

if [ "$ACTION" = uninstall ]; then
  for dest in "${TARGETS[@]}"; do
    for s in "${SKILLS[@]}"; do
      tgt="$dest/$s"
      if _target_exists "$tgt"; then
        if [ "$FORCE" -eq 1 ] || _target_owned "$tgt" "$SRC/$s" "$s"; then
          rm -rf -- "$tgt"; echo "removed  $tgt"
        else
          echo "kept foreign  $tgt"
        fi
      fi
    done
  done
  exit 0
fi

# Build every replacement before changing a live skill target.
for dest in "${TARGETS[@]}"; do
  for s in "${SKILLS[@]}"; do
    stage="$(mktemp -d "$dest/.eskill-analyze-stage-$s.XXXXXX")"
    STAGES+=("$stage")
    STAGE_TARGETS+=("$dest/$s")
    STAGE_SKILLS+=("$s")
    if [ "$MODE" = copy ]; then
      cp -R "$SRC/$s/." "$stage/"
      printf 'eskill-analyze:%s\n' "$s" > "$stage/$OWNERSHIP_MARKER"
    else
      rmdir "$stage"
      ln -s "$SRC/$s" "$stage"
    fi
  done
done

# Commit replacements with recoverable backups. The EXIT trap restores every
# prior target in reverse order if any rename fails.
COMMIT_ACTIVE=1
for ((i=0; i<${#STAGES[@]}; i++)); do
  stage="${STAGES[$i]}"
  tgt="${STAGE_TARGETS[$i]}"
  s="${STAGE_SKILLS[$i]}"
  dest="$(dirname "$tgt")"
  backup=""
  if _target_exists "$tgt"; then
    backup="$(mktemp -d "$dest/.eskill-analyze-backup-$s.XXXXXX")"
    rmdir "$backup"
    mv "$tgt" "$backup"
  fi
  SWAPPED_TARGETS+=("$tgt")
  SWAPPED_BACKUPS+=("$backup")
  mv "$stage" "$tgt"
    if [ "$MODE" = copy ]; then
      echo "copied   $SRC/$s -> $tgt"
    else
      echo "linked   $tgt -> $SRC/$s"
    fi
done
COMMIT_COMPLETE=1

echo
echo "Done. Invoke inside your harness:  /esa   /esat   /esat-fleet   /esat-frontier"
