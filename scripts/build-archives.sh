#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 2 ]]; then
  printf 'Usage: bash scripts/build-archives.sh GRAPHIFY_KIT OUTPUT_DIR\n' >&2
  exit 2
fi

workspace="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kit="$(cd "$1" && pwd)"
mkdir -p "$2"
output="$(cd "$2" && pwd)"
if [[ -n "$(find "$output" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  printf 'Select an empty output directory.\n' >&2
  exit 2
fi

project=vixttha/Provenistem
archive="$output/archive"
source_repo="$(mktemp -d)"
trap 'rm -rf -- "$source_repo"' EXIT
git -C "$source_repo" init -q
export GRAPHIFY_QUERY_LOG_DISABLE=1
export PYTHONHASHSEED=0

for version in v0.0.1 v0.0.2 v0.0.2.1 v0.0.2.2 v0.0.2.3 v0.0.2.4; do
  manifest="$workspace/manifests/$version.json"
  source="$(jq -er '.source_commit | select(test("^[a-f0-9]{40}$"))' "$manifest")"
  git -C "$source_repo" fetch -q --no-tags --depth=1 \
    "https://github.com/$project.git" "$source"
  test "$(git -C "$source_repo" rev-parse FETCH_HEAD)" = "$source"

  evidence="$output/$version"
  (
    cd "$source_repo"
    python "$kit/evidence_map.py" "$manifest" "$evidence"
    python "$kit/evidence_map.py" "$manifest" "$evidence" --check
  )

  node "$workspace/veraphifiy.mjs" import \
    --archive "$archive" --project "$project" --version "$version" \
    --source "$source" --checkout "$source_repo" --evidence "$evidence" \
    > "$evidence/import.json"
  digest="$(jq -er '.archive_sha256 | select(test("^[a-f0-9]{64}$"))' "$evidence/import.json")"
  pins=(--archive "$archive" --project "$project" --version "$version"
    --source "$source" --archive-sha256 "$digest")
  node "$workspace/veraphifiy.mjs" verify "${pins[@]}" > "$evidence/verify.json"
  node "$workspace/veraphifiy.mjs" lookup "${pins[@]}" --feature feature:generated-indexes \
    > "$evidence/lookup.json"

  source_path=packages/provenistem/tools/library.py
  source_line="$(git -C "$source_repo" show "$source:$source_path" \
    | awk '$0 == "def index(kind, rows):" { print NR }')"
  jq -e --arg source "$source" --arg version "$version" --arg path "$source_path" \
    --argjson line "$source_line" \
    '.source == $source and .version == $version and .citations == [{path: $path, line: $line}]' \
    "$evidence/lookup.json" > /dev/null
  printf '%s verified at %s; index implementation %s:%s\n' "$version" "$source" "$source_path" "$source_line"

  if [[ -f "$source_repo/prior-archives.sha256" ]]; then
    sha256sum -c "$source_repo/prior-archives.sha256"
  fi
  sha256sum "$archive"/*.json > "$source_repo/prior-archives.sha256"
done

(
  cd "$output"
  find archive v0.0.1 v0.0.2 v0.0.2.1 v0.0.2.2 v0.0.2.3 v0.0.2.4 -type f -print0 \
    | sort -z | xargs -0 sha256sum | tee SHA256SUMS
)
