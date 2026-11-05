```bash
#!/usr/bin/env bash
set -euo pipefail
dir="${1:-.}"
find "$dir" -maxdepth 1 -type f -name '*.jpeg' -print0 |
while IFS= read -r -d '' f; do
  mv -n -- "$f" "${f%.jpeg}.jpg"
done
```

Одна строка без файла:

```bash
for f in *.jpeg; do [ -e "$f" ] && mv -n -- "$f" "${f%.jpeg}.jpg"; done
```

Что делает:
- `-maxdepth 1` — только текущая папка, без подпапок.
- `-type f` — только файлы, папки с именем `*.jpeg` не трогает.
- `-print0` + `read -d ''` — пробелы и не-ASCII в именах работают.
- `mv -n` — если `f.jpg` уже существует, файл не перезаписывается и не переименовывается; такие случаи увидишь по оставшимся `.jpeg`.

Проверка после запуска: `ls *.jpeg` → должно быть `ls: cannot access '*.jpeg'`. Если файлы остались — это коллизии имён, разбери их вручную.