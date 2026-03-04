# Telegram News Feed Bot — План реализации

## КРИТИЧЕСКИЕ ПРАВИЛА РАЗРАБОТКИ

### Машина разработки — ТОЛЬКО для написания кода
- На этом Mac **ничего не устанавливается и не запускается**
- Тут только пишем код, больше ничего
- Запуск и тестирование — на другой машине (сначала старый Mac через SSH, потом Digital Ocean)
- **Никакого мусора** на этом компьютере

### Python-зависимости — ТОЛЬКО в venv
- Все зависимости устанавливаются **исключительно в виртуальное окружение** (`.venv/`)
- `.venv/` добавлен в `.gitignore` — не коммитится
- Системный Python не трогаем, глобально ничего не ставим

### Безопасность секретов
- **Все секреты** (токены, api_id, api_hash, номер телефона) хранятся только в `.env`
- `.env` добавлен в `.gitignore` — **никогда** не попадает в git/GitHub
- В репо только `.env.example` с плейсхолдерами (без реальных данных)
- GitHub-репозиторий **публичный** — никаких секретов не должно утечь

### Документация и файлы
- `README.md` — публичный, идёт на GitHub. Описание проекта, как настроить, как работает
- `docs/plan.md` — план разработки, идёт в репо
- `docs/steps.md` — детальные пошаговые инструкции, идёт в репо
- `logs/` — логи разработки, добавлены в `.gitignore`, **не идут на GitHub**

### Процесс разработки
- Каждый шаг из `docs/steps.md` выполняется **по одному**, в отдельной сессии
- Шаг = атомарная задача (написать один файл, одну функцию, один тест)
- После каждого шага — коммит

---

## Context

В Telegram множество новостных каналов, но они разрозненные — нужно переходить из канала в канал. Бот решает эту проблему: собирает сообщения из разных каналов в одну ленту в чате с ботом.

**Две основные фичи:**
1. **Ручная подписка**: юзер говорит боту какие каналы пересылать — бот пересылает все новые сообщения из них.
2. **Тематическая лента**: юзер выбирает темы из готового списка (~30 тем) — бот автоматически подписывает на все каналы этой темы из каталога.

**Масштаб**: ~1000 пользователей, ~20 каналов на юзера.

---

## Технический стек

| Компонент | Технология | Зачем |
|-----------|-----------|-------|
| Язык | Python 3.11+ | Основной язык |
| UI для юзера | aiogram 3.x (Bot API) | Команды, кнопки, пересылка |
| Чтение каналов | Telethon (Client API / MTProto) | Читать публичные каналы без ограничений |
| БД | SQLite через aiosqlite | Хранение юзеров, подписок, каталога |
| Конфиг | python-dotenv | Загрузка .env |
| Хостинг | VPS, long-running процесс | — |

**Зависимости** (requirements.txt):
```
aiogram>=3.4,<4.0
telethon>=1.34,<2.0
aiosqlite>=0.19,<1.0
python-dotenv>=1.0,<2.0
```

---

## Архитектура

Один Python-процесс, 3 async-компонента:

```
┌──────────────────────────────────────────────────────────┐
│                   main.py (asyncio)                       │
│                                                          │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ aiogram Bot   │  │ Telethon Client│  │  Forwarder   │  │
│  │ (UI для юзера)│  │ (читает каналы)│  │ (пересылает) │  │
│  └───────┬───────┘  └───────┬────────┘  └──────┬───────┘  │
│          └──────────┬───────┴──────────┬────────┘          │
│                  SQLite DB          In-Memory               │
│                 (aiosqlite)          Caches                 │
└──────────────────────────────────────────────────────────┘
```

**Поток данных:**
1. Telethon обнаруживает новое сообщение в канале
2. Ищет подписанных юзеров в БД
3. Кладёт задания в `asyncio.Queue`
4. Forwarder-воркеры вызывают `bot.forward_message()` с rate limit (~25 msg/sec)

**Гибридный мониторинг каналов:**
- Популярные каналы (>=3 подписчика бота) -> Telethon **подписывается** (join) -> реалтайм через event handler
- Редкие каналы (<3) -> Telethon **поллит** каждые 2-5 мин через `get_messages()` без join
- Лимит join ~500 каналов не проблема — большинство каналов будут общими

---

## БД: Схема (SQLite)

```sql
CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    is_paused     INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE channels (
    channel_id       INTEGER PRIMARY KEY,
    username         TEXT,
    title            TEXT,
    is_joined        INTEGER DEFAULT 0,
    subscriber_count INTEGER DEFAULT 0,
    last_message_id  INTEGER DEFAULT 0,
    poll_interval    INTEGER DEFAULT 120,
    last_polled_at   TEXT,
    created_at       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE subscriptions (
    user_id    INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, channel_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE
);

CREATE TABLE user_topics (
    user_id  INTEGER NOT NULL,
    topic_id TEXT NOT NULL,
    PRIMARY KEY (user_id, topic_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE catalog (
    channel_username TEXT NOT NULL,
    title            TEXT NOT NULL,
    category         TEXT NOT NULL,
    tags             TEXT,
    language         TEXT DEFAULT 'ru',
    PRIMARY KEY (channel_username, category)
);

CREATE TABLE forwarded_messages (
    channel_id   INTEGER NOT NULL,
    message_id   INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    forwarded_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (channel_id, message_id, user_id)
);
```

---

## Команды бота

| Команда | Действие |
|---------|----------|
| `/start` | Приветствие + инструкция |
| `/add @channel` | Подписаться на конкретный канал |
| `/remove @channel` | Отписаться от канала |
| `/list` | Список подписок с кнопками [Удалить] |
| `/topics` | Список ~30 тем с кнопками. Тап = подписка на все каналы темы |
| `/mytopics` | Выбранные темы с кнопками [Отписаться] |
| `/pause` | Поставить ленту на паузу |
| `/resume` | Возобновить ленту |
| `/help` | Справка |

---

## Каталог тем

Файл `data/channel_catalog.json` — содержит ~30 тем, каждая с набором каналов:

```json
{
  "topics": [
    {
      "id": "cars",
      "name": "Автомобили",
      "emoji": "cars-emoji",
      "channels": [
        {"username": "auto_news", "title": "Авто Новости"},
        {"username": "car_review", "title": "Обзоры авто"}
      ]
    },
    {
      "id": "tech",
      "name": "Технологии",
      "emoji": "tech-emoji",
      "channels": [...]
    }
  ]
}
```

При `/topics` юзер видит кнопки: `[Автомобили] [Технологии] [Спорт] ...`
Тап -> бот подписывает на все каналы этой темы из каталога.

---

## Структура проекта

```
TelegramNewsFeedBot/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── docs/
│   ├── plan.md                   <- план разработки
│   └── steps.md                  <- пошаговые инструкции
├── data/
│   ├── channel_catalog.json      <- каталог каналов по темам
│   └── bot.db                    <- SQLite (создаётся при запуске, в .gitignore)
├── bot/
│   ├── __init__.py
│   ├── main.py                   <- точка входа
│   ├── config.py                 <- настройки из .env
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py           <- подключение, миграции
│   │   ├── models.py             <- dataclasses
│   │   └── queries.py            <- все SQL-запросы
│   ├── telegram_bot/
│   │   ├── __init__.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── start.py          <- /start, /help
│   │   │   ├── channels.py       <- /add, /remove, /list
│   │   │   ├── topics.py         <- /topics, /mytopics
│   │   │   └── settings.py       <- /pause, /resume
│   │   ├── keyboards.py          <- inline-клавиатуры
│   │   ├── callbacks.py          <- обработка нажатий кнопок
│   │   └── middlewares.py        <- авторегистрация юзера
│   ├── channel_monitor/
│   │   ├── __init__.py
│   │   ├── client.py             <- Telethon клиент + авторизация
│   │   ├── event_handler.py      <- реалтайм для joined каналов
│   │   ├── poller.py             <- поллинг для остальных
│   │   ├── manager.py            <- логика join/leave, resolve канала
│   │   └── searcher.py           <- поиск каналов через Telegram API
│   ├── forwarder/
│   │   ├── __init__.py
│   │   ├── pipeline.py           <- очередь, воркеры, дедупликация
│   │   └── rate_limiter.py       <- token bucket
│   └── utils/
│       ├── __init__.py
│       └── logging.py            <- настройка логирования
├── tests/
│   ├── __init__.py
│   ├── test_callbacks.py
│   ├── test_channels_handler.py
│   ├── test_client.py
│   ├── test_event_handler.py
│   ├── test_handler_wiring.py
│   ├── test_manager.py
│   ├── test_pipeline.py
│   ├── test_poller.py
│   ├── test_queries.py
│   ├── test_rate_limiter.py
│   ├── test_searcher.py
│   ├── test_seed_catalog.py
│   └── test_settings.py
└── scripts/
    └── seed_catalog.py           <- загрузка каталога из JSON в БД
```

---

## Конфигурация (.env)

```
BOT_TOKEN=...                 # от @BotFather
TELEGRAM_API_ID=...           # от my.telegram.org
TELEGRAM_API_HASH=...         # от my.telegram.org
TELEGRAM_PHONE=...            # номер сервисного аккаунта
SESSION_NAME=newsfeed_service
DB_PATH=data/bot.db
CATALOG_PATH=data/channel_catalog.json
JOIN_THRESHOLD=3
POLL_INTERVAL_DEFAULT=120
FORWARD_RATE_LIMIT=25
FORWARD_WORKERS=3
LOG_LEVEL=INFO
```

---

## Обработка edge cases

| Ситуация | Обработка |
|----------|----------|
| Юзер заблокировал бота | forward_message -> TelegramForbiddenError -> is_paused=1 |
| Канал стал приватным | ChannelPrivateError -> уведомить юзеров -> удалить через 7 дней |
| Перезапуск бота | Догнать по last_message_id через get_messages(min_id=...) |
| Дубли подписок | PRIMARY KEY (user_id, channel_id) -> INSERT OR IGNORE |
| Rate limit Telegram | RetryAfter -> подождать -> повторить. Очередь гарантирует: ничего не потеряется |
| Приватный канал в /add | Telethon не может прочитать -> сообщить юзеру, что поддерживаются только публичные |
| Массовая пересылка | 500 юзеров x 1 сообщение = 500 заданий. При 25 msg/sec = ~20 секунд. Приемлемо. |

---

## Предварительные требования

Перед началом реализации нужно подготовить (на тестовой машине):
1. **Python 3.11+** — проверить наличие
2. **Telegram Bot** — создать через @BotFather, получить токен
3. **Telegram API credentials** — зарегистрировать приложение на my.telegram.org, получить api_id и api_hash
4. **Сервисный аккаунт** — отдельный номер телефона для Telethon (не личный аккаунт)

---

## Верификация

### Автоматическая (тесты пишутся здесь, запускаются на другой машине):
- `pytest tests/` — unit-тесты для БД, rate limiter, дедупликации, логики подписок

### Ручная (в Telegram на тестовой машине):
1. Запустить бота -> отправить /start -> получить ответ
2. /add @test_channel -> /list -> увидеть канал -> /remove
3. /add @channel -> дождаться нового поста в канале -> получить пересылку
4. /topics -> выбрать тему -> /mytopics -> увидеть подписку -> получать посты
5. Перезапустить бота -> убедиться что пропущенные посты догнаны

**Напоминание**: на этом Mac ничего не запускаем. Только пишем код и коммитим.

---

## Phase 16: /topics и /mytopics хендлеры

### Шаги

- [x] Step 098: Создать `bot/telegram_bot/handlers/topics.py` с хендлером `/topics`
- [x] Step 099: Обновить `callbacks.py` — при подписке на тему также подписывать на все каналы темы из каталога
- [x] Step 100: Добавить хендлер `/mytopics` в `topics.py`
- [x] Step 101: Обновить `callbacks.py` — при отписке от темы также отписывать от всех каналов темы
- [x] Зарегистрировать topics router в `handlers/__init__.py`
- [x] Добавить query `get_catalog_categories` в `queries.py`

---

## Phase: ChannelSearcher Tests

### Шаги

- [x] Step: Создать `tests/test_searcher.py` с тестами `test_search_by_topic_from_catalog` и `test_search_combined_catalog_enough`

---

## Phase 31: Подключение реальных зависимостей к хендлерам

Хендлеры бота переключаются со стабов на реальные вызовы ChannelManager и ChannelSearcher.

### Шаги

- [x] Step 189: Обновить `handlers/channels.py` — `/add` вызывает `channel_manager.resolve_and_add_channel()`
- [x] Step 190: Обновить `/add` — после подписки вызывать `channel_manager.on_subscription_change()`
- [x] Step 191: Обновить `/remove` — после отписки вызывать `channel_manager.on_subscription_change()`
- [x] Step 192: Обновить `handlers/topics.py` — `/topics` загружает реальный список тем из каталога БД
- [x] Step 193: Обновить колбэки тем — при подписке вызывать resolve и subscribe через `channel_manager`
- [x] Подключить `channel_manager` в `bot["channel_manager"]` в `main.py`
- [x] Тесты интеграции

---

## Phase: Error Handling Improvements

Улучшения обработки ошибок в ключевых компонентах.

### Шаги

- [x] Step 196a: poller.py — уведомлять подписчиков при ChannelPrivateError, передать Bot в конструктор
- [x] Step 196b: event_handler.py — проверить (уже корректно, try/except с logger.exception)
- [x] Step 196c: pipeline.py — добавить retry counter (макс. 3 попытки) для general exception
- [x] Step 196d: main.py — signal handling (SIGINT/SIGTERM), robust cleanup с отдельными try/except

---

## Phase: Code Review Fixes (2026-03-03)

Исправление 6 найденных проблем при code review.

### Шаги

- [x] Issue 1: Тесты сломаны после get_peer_id fix — патчить `utils.get_peer_id` в тестах
- [x] Issue 2: Каталог не сидится при запуске — добавить `seed_catalog()` в `main.py`
- [x] Issue 3: Нет хендлера для "noop" callback — добавить `cb_noop` в `callbacks.py`
- [x] Issue 4: `callback.answer()` вызывается слишком поздно — перенести в начало хендлеров
- [x] Issue 5: Сообщения из поллера в обратном порядке — добавить `reversed()` в `poller.py`
- [x] Issue 6: `load_topics` вызывает JSON синхронно при каждом вызове — кешировать в `bot["topics"]`

---

## Phase: Code Review Fixes Round 2 (2026-03-03)

Исправление 5 проблем из code review (Issue A — ложное срабатывание, Issue G — dead code, оставлен как есть).

### Шаги

- [x] Issue A: seed_catalog.py category type mismatch — FALSE POSITIVE (IDs уже строки в JSON)
- [x] Issue B: Callback data parsing crash — обёрнуто в try/except ValueError/IndexError
- [x] Issue C: resolve_channel не проверяет тип entity — добавлена проверка isinstance(entity, Channel)
- [x] Issue D: PRAGMA foreign_keys может сброситься после executescript — повторный PRAGMA после init_schema
- [x] Issue E: Raw SQL в manager.py — вынесено в queries.delete_channel()
- [x] Issue F: Poller limit=20 теряет сообщения — увеличено до 100

---

## Phase: Deploy to DigitalOcean (2026-03-04)

Деплой бота на дроплет DigitalOcean и первый запуск с авторизацией Telethon.

### Шаги

- [x] Step 1: Исправить .env на сервере (пути SESSION_NAME и DB_PATH для Docker volumes)
- [ ] Step 2: Закоммитить все локальные изменения, запушить на GitHub
- [ ] Step 3: Склонировать/обновить код на сервере с GitHub
- [ ] Step 4: Пересобрать Docker-образ на сервере
- [ ] Step 5: Запустить контейнер в интерактивном режиме для Telethon-авторизации
- [ ] Step 6: После успешной авторизации — перезапуск в фоновом режиме (docker compose up -d)
