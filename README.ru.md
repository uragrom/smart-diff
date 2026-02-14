# Smart Diff (Git Deep-Diff)

[English](README.md) | **Русский**

CLI-утилита для код-ревью: вместо сырого `git diff` показывает **объяснение намерений изменений** через локальную LLM (Ollama). Удобно для быстрого разбора правок и генерации конкретных сообщений коммитов.

**Пример:** команда `git dd` выводит что-то вроде:

> В этом коммите ты отрефакторил логику авторизации (JWT → серверные сессии) и исправил возможную утечку в `cleanup()`.

## Требования

- Python 3.8+
- [Ollama](https://ollama.com) установлена и запущена
- Модель в Ollama (например `ollama pull llama3` или `ollama pull deepseek-r1`; список: `ollama list`)

## Установка

Из исходников:

```bash
git clone https://github.com/YOUR_USERNAME/smart-diff.git
cd smart-diff
pip install .
```

С GitHub (подставь свой репозиторий):

```bash
pip install git+https://github.com/YOUR_USERNAME/smart-diff.git
```

## Использование как `git dd`

Чтобы вызывать утилиту как **git dd**, добавь алиас:

```bash
git config --global alias.dd '!smart-diff'
```

После этого:

```bash
git dd                  # разбор текущих изменений; если их нет — последний коммит
git dd --staged         # только staged
git dd -r HEAD          # разбор последнего коммита
git dd -m deepseek-r1   # своя модель
```

## Команды

| Команда | Описание |
|--------|----------|
| `smart-diff` | Анализ текущих изменений (или последнего коммита при чистой копии) |
| `smart-diff --staged` / `-s` | Только проиндексированные изменения |
| `smart-diff --ref HEAD` / `-r HEAD~1` | Разбор указанного коммита |
| `smart-diff --commit-msg` | Сгенерировать **конкретное** сообщение коммита (что сделано, без общих фраз) |
| `smart-diff -m <модель>` | Модель (переопределяет конфиг) |
| `smart-diff -l ru` / `--lang en` | Язык вывода и ответа LLM: `en`, `ru`, `auto` |
| `smart-diff config set model deepseek-r1` | Задать модель по умолчанию |
| `smart-diff config set lang ru` | Задать язык по умолчанию (`en`, `ru`, `auto`) |
| `smart-diff config show` | Показать текущие модель и язык (и путь к конфигу) |

## Фишки

- **Игнорирование мусора** — автоматически исключаются `package-lock.json`, `poetry.lock`, `yarn.lock`, `node_modules/` и т.п.
- **Обрезка больших диффов** — при большом объёме diff умно обрезается с сохранением хвоста.
- **Модель и язык по умолчанию** — `smart-diff config set model deepseek-r1`, `smart-diff config set lang ru`; просмотр: `smart-diff config show`.
- **Разные модели** — по умолчанию из конфига или `llama3`; для кода можно `codestral` или `deepseek-r1`. Список: `ollama list`.
- **Язык** — `-l en` / `-l ru` / `-l auto`; влияет на подсказки в терминале и ответ LLM.
- **Pre-commit hook** — подстановка сообщения коммита от ИИ при `git commit`:

```bash
cp hooks/prepare-commit-msg.example .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

При следующем `git commit` сообщение будет сгенерировано по staged-изменениям.

## Пример вывода

```
Модель: llama3. Анализ изменений...
╭────────────────── Smart Diff — разбор изменений ──────────────────╮
│ **Краткое резюме**                                                │
│ Рефакторинг аутентификации: переход с JWT на сессии.              │
│                                                                   │
│ **Ключевые изменения**                                            │
│ - Замена JWT на серверные сессии в `auth.py`                      │
│ - Удаление передачи токена в заголовках в `api.py`                │
│                                                                   │
│ **Потенциальные риски**                                           │
│ Не обнаружено.                                                    │
╰───────────────────────────────────────────────────────────────────╯
```

## Разработка

```bash
pip install -e ".[dev]"
ruff check src
```

## Лицензия

MIT — см. [LICENSE](LICENSE).
