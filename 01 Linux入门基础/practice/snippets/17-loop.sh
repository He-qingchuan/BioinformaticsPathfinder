for record in logs/*.log; do
  if [ -f "$record" ]; then
    printf '%s: ' "$record"
    wc -l < "$record"
  fi
done
