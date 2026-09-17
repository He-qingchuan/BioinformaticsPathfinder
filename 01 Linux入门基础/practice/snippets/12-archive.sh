tar -czf results/notes.tar.gz notes
tar -tzf results/notes.tar.gz | sort
mkdir -p results/unpacked
tar -xzf results/notes.tar.gz -C results/unpacked
cat results/unpacked/notes/morning.txt
