```bash
#!/usr/bin/env bash
# Переименовывает *.jpeg → *.jpg в папке $1 (по умолчанию — текущая).
# Подпапки не трогает. Существующий .jpg не перезаписывает — такой файл пропускает.
set -euo pipefail

dir="${1:-.}"
shopt -s nullglob nocaseglob

for src in "$dir"/*.jpeg; do
  dst="${src%.*}.jpg"
  if [[ -e "$dst" ]]; then
    printf 'ПРОПУСК: %s — уже существует %s\n' "$src" "$dst"
    continue
  fi
  mv -- "$src" "$dst"
  printf '%s -> %s\n' "$src" "$dst"
done
```

1. Сохранить как `jpeg2jpg.sh`, затем `chmod +x jpeg2jpg.sh`.
2. Прогон без изменений: заменить в скрипте `mv --` на `echo mv --` и запустить `./jpeg2jpg.sh /путь/к/папке` — печатает, что сделал бы.
3. Настоящий запуск: `./jpeg2jpg.sh /путь/к/папке`.

Проверка результата: `ls /путь/к/папке/*.jpeg` печатает `no matches found` (zsh) или ошибку «No such file» (bash) — значит `.jpeg` не осталось.

Регистр расширения: `nocaseglob` берёт и `.JPEG`, и `.Jpeg`; все становятся `.jpg` в нижнем регистре. Два файла `a.jpeg` и `a.JPEG` в одной папке дают один `a.jpg`: второй уйдёт в ПРОПУСК, не потеряется.