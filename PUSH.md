# Как залить на GitHub

Три способа. Выбери один.

---

## Вариант A. Через веб-интерфейс (без терминала)

1. Зайди на https://github.com/new
2. **Repository name:** `i-have-autism`
3. **Description:** `Literal, explicit output and exacting code for your coding agent.`
4. Тип: **Public**. Галочки README/gitignore/license — **не ставь** (файлы уже есть).
5. Нажми **Create repository**.
6. На странице пустого репо нажми **uploading an existing file**.
7. Распакуй архив `i-have-autism.zip` и перетащи **содержимое** папки `i-have-autism/` в окно браузера.
   Важно: тащи то, что внутри папки (включая скрытые `.claude-plugin`, `.codex-plugin`, `.agents`,
   `.opencode`), а не саму папку.
8. **Commit changes**.
9. Затем — подставь свой логин (иначе ссылки в README будут вести в никуда). В терминале, в папке репо:

```bash
./setup.sh <твой-github-логин>
git add -A
git commit -m "fill in username"
git push
```

---

## Вариант B. Через терминал по HTTPS (git уже стоит)

```bash
# 1. распакуй архив
unzip i-have-autism.zip
cd i-have-autism

# 2. подставь свой логин
./setup.sh <твой-github-логин>

# 3. закоммить правку
git add -A
git commit -m "fill in username"

# 4. создай пустой репозиторий на GitHub (без README), затем:
git remote add origin https://github.com/<твой-логин>/i-have-autism.git
git branch -M main
git push -u origin main
```

Если попросит пароль — **введи personal access token, не пароль от аккаунта**. GitHub отключил вход по
паролю. Токен: https://github.com/settings/tokens → Generate new token (classic) → scope `repo`.

---

## Вариант C. Через SSH

```bash
unzip i-have-autism.zip && cd i-have-autism
./setup.sh <твой-github-логин>
git add -A && git commit -m "fill in username"

# если SSH-ключа ещё нет:
ssh-keygen -t ed25519 -C "<твой-email>"
cat ~/.ssh/id_ed25519.pub     # добавь этот ключ: https://github.com/settings/keys

git remote add origin git@github.com:<твой-логин>/i-have-autism.git
git branch -M main
git push -u origin main
```

---

## Проверка после заливки

```bash
git remote -v          # origin ведёт на твой репо
git log --oneline      # 2 коммита
```

И на сайте: открой `https://github.com/<твой-логин>/i-have-autism` — README должен отрисоваться, а в
списке файлов быть видна папка `skills/`.

---

## Заметки

- **Скрытые папки.** `.claude-plugin`, `.codex-plugin`, `.agents`, `.opencode` — это точки в начале имени.
  При заливке через веб-интерфейс их легко потерять: если файловый менеджер скрывает такие папки, включи
  показ скрытых файлов. Через `git push` они уходят сами.
- **`REPLACE_USERNAME`.** В трёх файлах (`README.md`, `INSTALL.md`, `.agents/plugins/marketplace.json`)
  стоит заглушка. `setup.sh` меняет её на твой логин. Без этого команды установки в README не сработают.
- **Лицензия.** MIT, имя автора — `Ougi Oshino`. Если хочешь своё имя или псевдоним — поправь
  `LICENSE` и поле `author` во всех манифестах.
- **Версия.** `0.1.0` в четырёх файлах (`plugin.json`, `.claude-plugin/plugin.json`,
  `.codex-plugin/plugin.json`, `gemini-extension.json`) и в фронтматтере скилла. При правке скилла
  поднимай её везде сразу — иначе клиенты увидят старый набор правил.
