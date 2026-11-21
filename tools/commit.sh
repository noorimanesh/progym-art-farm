#!/bin/sh
# Commit all tracked changes as the build identity and push to the art branch.
set -e
cd "$(dirname "$0")/.."
git add -A
GIT_AUTHOR_NAME=FabaPars GIT_AUTHOR_EMAIL=build@progym.ir \
GIT_COMMITTER_NAME=FabaPars GIT_COMMITTER_EMAIL=build@progym.ir \
git -c user.name=FabaPars -c user.email=build@progym.ir -c commit.gpgsign=false \
  commit -q -m "$1" || true
git push -q origin HEAD:exercise-art
