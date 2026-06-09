import csv
import io

s = '''MVBNC00116	50000	28/05/2026	MG/CA	FM/CA/III/065A	09	"
Page 3 of 9
01"
MVBNC00116	50000	28/05/2026	MG/CA	FM/CA/III/065A	09	"
Page 4 of 9
04"
MVBNC00116	50000	28/05/2026	MG/CA	FM/CA/III/065A	09	"
Page 5 of 9
01"'''

f = io.StringIO(s)
reader = csv.reader(f, delimiter='\t')
for row in reader:
    print(row)
