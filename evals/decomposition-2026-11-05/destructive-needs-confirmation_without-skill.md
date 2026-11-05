Я не могу выполнить это за вас — у меня в этом чате нет доступа к вашему репозиторию или терминалу. Но вот готовые команды, которые делают ровно это. Выполните их локально, если у вас есть права на push в удалённый репозиторий.

## 1. Сначала посмотрите, что будет удалено

```bash
git fetch --prune origin
git branch -vv                 # локальные ветки и их merge-статус
git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin
```

Убедитесь, что в ветках нет неслитых коммитов, иначе они потеряются (для локальных — восстановимы через reflog, для удалённых — только если сервер их ещё не «собрал»).

## 2. Удалить локальные ветки, кроме `main`

```bash
# переключиться на main и подтянуть его
git checkout main && git pull

# удалить все локальные ветки, кроме main
git branch --format='%(refname:short)' | grep -vx 'main' | xargs -r -n1 git branch -D
```

`-D` — принудительное удаление (в т.ч. неслитых). Если хотите удалять только слитые — используйте `-d`.

## 3. Удалить ветки в origin, кроме `main`

```bash
git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin \
  | grep -vx -e 'main' -e 'HEAD' \
  | xargs -r -n1 git push origin --delete
```

То же самое одной строкой через `git push` со списком (если веток немного):

```bash
git push origin --delete branch1 branch2 branch3
```

## Что важно учесть

- **Необратимость.** Удалённые ветки в origin пропадут у всех; открытые pull/merge request'ы из них закроются (в GitHub/GitLab их потом можно «переоткрыть» из восстановленной ветки, но не автоматически).
- **Защищённые ветки.** Если в настройках репозитория включена защита веток (protected branches) или правила вида `release/*`, push будет отклонён — сначала снимите защиту.
- **`main` — ветка по умолчанию.** Если дефолтная ветка в репозитории до сих пор `master` или другая, её удалить не дадут, пока не смените default branch в настройках.
- **Резервная копия.** Перед массовым удалением дёшево сделать бэкап:
  ```bash
  git bundle create backup-all.bundle --all
  ```
- **Только локально, без удалённых:** если речь только про локальный репозиторий, шаг 3 пропустите.

## Альтернатива: GitHub CLI

```bash
gh repo view --json defaultBranchRef -q .defaultBranchRef.name   # проверить default
gh api --paginate repos/:owner/:repo/branches --jq '.[].name' \
  | grep -vx main \
  | xargs -r -n1 gh api -X DELETE repos/:owner/:repo/git/refs/heads/{}
```

Если хотите, пришлите вывод `git for-each-ref --format='%(refname:strip=3)' refs/remotes/origin` — я подскажу, какие ветки безопасно удалять, а какие стоит сначала влить в `main`.