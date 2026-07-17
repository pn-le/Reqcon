#!/bin/zsh
# Daily run: scan boards, then publish the refreshed README openings to GitHub.
# Invoked by launchd (com.pnle.reqcon.plist).

cd "$(dirname "$0")/.."

.venv/bin/reqcon scan
scan_rc=$?

if ! git diff --quiet -- README.md; then
    git add README.md
    git commit -m "chore: update current openings ($(date +%F))"
    git push origin main
fi

exit $scan_rc
