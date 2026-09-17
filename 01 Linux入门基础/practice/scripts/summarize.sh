#!/usr/bin/env bash
# A deliberately small report for this course's bundled TSV and logs.
# pipefail makes a failed stage visible in the pipeline's exit status.
set -o pipefail
if [ "$#" -ne 1 ]; then
  echo 'Usage: bash summarize.sh <linux-lab directory>' >&2
  exit 2
fi
project=$1
for required in tables/observations.tsv logs/day-01.log logs/day-02.log; do
  if [ ! -r "$project/$required" ]; then
    printf 'Cannot read: %s\n' "$project/$required" >&2
    exit 2
  fi
done
output="$project/results/report"
if ! mkdir -p "$output"; then
  exit 1
fi
if ! tail -n +2 "$project/tables/observations.tsv" | cut -f 3 | sort | uniq -c > "$output/species-records.txt"; then
  echo 'Could not build species record counts.' >&2
  exit 1
fi
grep -n -F 'WARN' "$project/logs/day-01.log" "$project/logs/day-02.log" > "$output/warnings.txt"
status=$?
if [ "$status" -gt 1 ]; then
  echo 'Could not search the logs.' >&2
  exit "$status"
fi
printf 'Report saved in: %s\n' "$output"
cat "$output/species-records.txt"
