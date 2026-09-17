head -n 1 tables/observations.tsv
tail -n +2 tables/observations.tsv | cut -f 2,4
tail -n +2 tables/observations.tsv | cut -f 4 | sort -n
