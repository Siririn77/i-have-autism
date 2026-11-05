Пример bash-скрипта, который считает файлы в указанной папке, изменённые более 30 дней назад:

```bash
#!/usr/bin/env bash
set -euo pipefail

dir="${1:-.}"

if [[ ! -d "$dir" ]]; then
  echo "Ошибка: '$dir' — не папка" >&2
  exit 1
fi

count=0
while IFS= read -r -d '' _; do
  count=$((count + 1))
done < <(find "$dir" -maxdepth 1 -type f -mtime +30 -print0)

echo "$count"
```

Использование:

```bash
./count_old_files.sh /path/to/folder
```

Если папка не указана, берётся текущая:

```bash
./count_old_files.sh
```

Что важно:

- `-maxdepth 1` — считать только файлы непосредственно в папке, без подпапок.
- `-type f` — только обычные файлы, без каталогов.
- `-mtime +30` — файл изменён более 30 дней назад.
- `-print0` + `read -d ''` — корректная обработка имён с пробелами и спецсимволами.

Если нужно считать **рекурсивно**, включая подпапки, уберите `-maxdepth 1`:

```bash
find "$dir" -type f -mtime +30 -print0
```

Короткий вариант одной строкой для текущей папки:

```bash
find . -maxdepth 1 -type f -mtime +30 -printf '.' | wc -c
```

Но он использует GNU `find` из-за `-printf`. Скрипт выше надёжнее и переносимее.