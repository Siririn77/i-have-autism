#!/usr/bin/env bash
# Подставляет твой GitHub-логин во все места с REPLACE_USERNAME.
# Использование: ./setup.sh <твой-github-логин>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Использование: $0 <твой-github-логин>"
  echo "Пример:        $0 serenecodes"
  exit 1
fi

USER="$1"
if ! printf '%s' "$USER" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9-]{0,37}[A-Za-z0-9])?$'; then
  echo "Ошибка: '$USER' не похож на GitHub-логин (латиница, цифры, дефис; не начинается и не кончается дефисом)."
  exit 1
fi

# Подставляем во все текстовые файлы, где стоит заглушка
files=$(grep -rl 'REPLACE_USERNAME' . --exclude-dir=.git 2>/dev/null || true)
if [ -z "$files" ]; then
  echo "Заглушек REPLACE_USERNAME не найдено — возможно, уже подставлено."
else
  for f in $files; do
    sed -i "s/REPLACE_USERNAME/${USER}/g" "$f"
    echo "  обновлён: $f"
  done
fi

echo ""
echo "Готово. Проверка:"
grep -rn "github.com/${USER}/i-have-autism" . --exclude-dir=.git || echo "  (ничего не найдено — проверь вручную)"
