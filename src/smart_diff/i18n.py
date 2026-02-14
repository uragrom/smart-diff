"""UI message strings by language (en, ru)."""

MESSAGES = {
    "en": {
        "error_prefix": "Error:",
        "no_changes": "No changes. Use --staged for index or change files. For last commit: smart-diff --ref HEAD",
        "analyzing_last": "No local changes — analyzing last commit (HEAD).",
        "model_label": "Model: {model}. Analyzing changes...",
        "commit_msg_generating": "Model: {model}. Generating commit message...",
        "commit_written": "Message written to {path}",
        "suggested_commit": "Suggested commit message",
        "analysis_title": "Smart Diff — change analysis",
        "ollama_connect": "Could not connect to Ollama. Start Ollama (https://ollama.com/download) and try again.",
        "ollama_model_not_found": "Model '{model}' not found in Ollama. Install: ollama pull {model}\nOr set an installed model: smart-diff -m <name>. List: ollama list",
        "ollama_hint": "Hint: ollama list — list models, ollama pull {model} — install.",
        "config_model_set": "Default model set to: {model}",
        "config_lang_set": "Default language set to: {lang}",
        "config_show": "model = {model}\nlang = {lang}",
        "config_path": "Config file: {path}",
        "html_report_written": "HTML report written to {path}",
        "html_report_written_prefix": "HTML report written to ",
    },
    "ru": {
        "error_prefix": "Ошибка:",
        "no_changes": "Нет изменений. Используй --staged для индекса или измени файлы. Для последнего коммита: smart-diff --ref HEAD",
        "analyzing_last": "Нет текущих изменений — анализирую последний коммит (HEAD).",
        "model_label": "Модель: {model}. Анализ изменений...",
        "commit_msg_generating": "Модель: {model}. Генерация сообщения коммита...",
        "commit_written": "Сообщение записано в {path}",
        "suggested_commit": "Предложенное сообщение коммита",
        "analysis_title": "Smart Diff — разбор изменений",
        "ollama_connect": "Не удалось подключиться к Ollama. Запусти Ollama (https://ollama.com/download) и повтори команду.",
        "ollama_model_not_found": "Модель '{model}' не найдена в Ollama. Установи: ollama pull {model}\nЛибо укажи модель: smart-diff -m <имя>. Список: ollama list",
        "ollama_hint": "Подсказка: ollama list — список моделей, ollama pull {model} — установка.",
        "config_model_set": "Модель по умолчанию: {model}",
        "config_lang_set": "Язык по умолчанию: {lang}",
        "config_show": "model = {model}\nlang = {lang}",
        "config_path": "Файл конфига: {path}",
        "html_report_written": "HTML-отчёт записан в {path}",
        "html_report_written_prefix": "HTML-отчёт записан в ",
    },
}


def t(key: str, locale: str, **fmt: str) -> str:
    """Get message for key and locale; format with fmt kwargs. Falls back to en."""
    d = MESSAGES.get(locale, MESSAGES["en"])
    msg = d.get(key, MESSAGES["en"].get(key, key))
    return msg.format(**fmt) if fmt else msg
