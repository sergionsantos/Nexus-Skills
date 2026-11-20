#!/usr/bin/env bash
# Poll a generate_deep_doc.py status file until the run reaches a terminal state.
#
#   wait_for_status.sh <status-file> [max_polls] [interval_secs]
#
# Exit: 0 = done | 1 = error | 2 = worker died without writing a terminal state
#       | 3 = timed out
#
# A plain `until grep done|error; do sleep; done` never returns when the child
# is SIGKILLed (only the live child writes the status), so this checks liveness
# via the recorded pid and is bounded. ponytail: sed on the JSON, no jq
# dependency — the file is written by _write_status() with a fixed shape.
set -uo pipefail

STATUS="${1:?usage: wait_for_status.sh <status-file> [max_polls] [interval_secs]}"
MAX="${2:-90}"
INTERVAL="${3:-20}"

# Exit 0 is the ONE value the caller does not question, so a bad argument must
# never be able to produce it. Unvalidated, `seq 1 abc` skips the loop entirely
# and the script falls off the end with whatever status was pending — 0.
case "$MAX" in ''|*[!0-9]*)
    echo "max_polls must be a non-negative integer, got '$MAX'" >&2; exit 3 ;;
esac
case "$INTERVAL" in ''|*[!0-9]*)
    echo "interval_secs must be a non-negative integer, got '$INTERVAL'" >&2; exit 3 ;;
esac
# The form check passes all-digit values above 2^63, which then blow up in the
# loop's arithmetic — exit 3 for the wrong reason, with a shell error instead of
# ours. 9 digits is already ~31 years of polling at 1s.
if [ "${#MAX}" -gt 9 ] || [ "${#INTERVAL}" -gt 9 ]; then
    echo "max_polls/interval must be a non-negative integer of at most 9 digits" >&2
    exit 3
fi

_field() { printf '%s' "$1" | sed -n "s/.*\"$2\": \"\([^\"]*\)\".*/\1/p"; }
_pid()   { printf '%s' "$1" | sed -n 's/.*"pid": \([0-9]*\).*/\1/p'; }

state=""
# `seq 1 $MAX` materialises the whole sequence first: an all-digits typo like
# 9000000000 tries to allocate hundreds of GB before the first poll runs.
# A counting loop allocates nothing.
i=0
while [ "$i" -lt "$MAX" ]; do
    i=$((i + 1))
    if [ -f "$STATUS" ]; then
        snap=$(cat "$STATUS" 2>/dev/null)
        state=$(_field "$snap" state)
        case "$state" in
            done)  echo "done"; exit 0 ;;
            error) echo "error: $(_field "$snap" error)"; exit 1 ;;
        esac
        pid=$(_pid "$snap")
        # ponytail: `kill -0` cannot tell ESRCH (gone) from EPERM (alive but
        # another user's) — a recycled pid owned by root would read as death.
        # Needs pid wraparound to bite; if it ever does, compare the process
        # start time too. A non-numeric pid just disables liveness (-> timeout).
        if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
            # Re-read once: the worker may have finished between the snapshot
            # and the liveness check, which is a clean exit, not a death.
            state=$(_field "$(cat "$STATUS" 2>/dev/null)" state)
            case "$state" in
                done)  echo "done"; exit 0 ;;
                error) echo "error"; exit 1 ;;
            esac
            echo "worker pid $pid is gone, status still '$state' — run died" >&2
            exit 2
        fi
    fi
    sleep "$INTERVAL"
done

# MAX x INTERVAL, not $((MAX * INTERVAL)): the product overflows silently in
# 64-bit shell arithmetic and would print a negative or wrapped number.
echo "timed out after ${MAX} polls x ${INTERVAL}s, last state='${state:-<no status file>}'" >&2
exit 3
