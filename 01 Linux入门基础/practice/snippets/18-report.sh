mkdir -p results/report
tail -n +2 tables/observations.tsv | cut -f 3 | sort | uniq -c > results/report/species-records.txt
grep -n -F 'WARN' logs/day-01.log logs/day-02.log > results/report/warnings.txt
cat results/report/species-records.txt
cat results/report/warnings.txt
