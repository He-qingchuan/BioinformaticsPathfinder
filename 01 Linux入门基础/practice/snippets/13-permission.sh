cp notes/morning.txt results/private-note.txt
chmod u=rw,go= results/private-note.txt
stat -c '%a' results/private-note.txt
