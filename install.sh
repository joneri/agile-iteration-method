#!/bin/sh
set -eu

cat >&2 <<'EOF'
AIM remote bootstrap has been retired for security.

Install the complete portable skill with:
  npx skills add joneri/agile-iteration-method --skill agile-iteration-method

For adaptive repository setup, clone the public AIM repository, review the
source locally, and follow docs/workflow/install-aim-2.0.md. The adaptive
installer always begins with a dry-run preview before any apply decision.
EOF

exit 2
