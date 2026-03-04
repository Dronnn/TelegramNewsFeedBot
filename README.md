<div align="center">

# Telegram News Feed Bot

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Telegram Bot API](https://img.shields.io/badge/Telegram_Bot_API-aiogram_3-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Telethon](https://img.shields.io/badge/Telethon-Userbot_API-blue?style=for-the-badge)

**Агрегатор новостей из Telegram-каналов в единую персональную ленту.**

Подписывайтесь на каналы и темы — бот собирает посты и пересылает их вам в одном чате.
Никаких алгоритмов ранжирования, только хронологическая лента.

</div>

---

## Возможности

| | Функция | Описание |
|---|---------|----------|
| :newspaper: | **Ручная подписка** | Добавляйте любые публичные Telegram-каналы и получайте их посты в одном месте |
| :bookmark_tabs: | **Тематическая лента** | Подписывайтесь на темы (~30 категорий: технологии, наука, спорт и др.) — бот автоматически подберёт каналы |
| :pause_button: | **Пауза / Возобновление** | Приостановите ленту и возобновите в любой момент |
| :no_entry_sign: | **Дедупликация** | Каждое сообщение пересылается только один раз |
| :zap: | **Гибридный мониторинг** | Популярные каналы — реалтайм, остальные — периодический опрос |

---

## Стек технологий

| Компонент                  | Технология         |
|----------------------------|--------------------|
| Язык                       | Python 3.11+       |
| Bot API                    | aiogram 3.x        |
| Userbot / парсинг каналов  | Telethon           |
| База данных                | SQLite + aiosqlite |
| Конфигурация               | python-dotenv      |

---

## Быстрый старт

### Предварительные требования

1. **Python 3.11+**
2. **Telegram Bot** — создать через [@BotFather](https://t.me/BotFather), получить токен
3. **Telegram API credentials** — зарегистрировать приложение на [my.telegram.org](https://my.telegram.org), получить `api_id` и `api_hash`
4. **Сервисный аккаунт** — отдельный номер телефона для Telethon (не личный аккаунт)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/Dronnn/TelegramNewsFeedBot.git
cd TelegramNewsFeedBot

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate    # Linux / macOS
# venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt
```

### Настройка

```bash
cp .env.example .env
```

Заполните `.env` реальными значениями — описание каждой переменной см. в разделе [Конфигурация](#конфигурация).

### Загрузка каталога каналов

```bash
python scripts/seed_catalog.py
```

Загружает темы и каналы из `data/channel_catalog.json` в базу данных.

### Запуск

```bash
python -m bot.main
```

> При первом запуске Telethon запросит код подтверждения для сервисного аккаунта.

---

## Docker

В репозитории есть готовые `Dockerfile` и `docker-compose.yml`.

```bash
# 1. Подготовить конфигурацию
cp .env.example .env
# Заполнить .env реальными значениями

# 2. Первый запуск — интерактивный (авторизация Telethon)
docker compose run --rm bot

# 3. После успешной авторизации — запуск в фоне
docker compose up -d
```

| Каталог    | Назначение                | Монтирование   |
|------------|---------------------------|----------------|
| `runtime/` | SQLite-база данных        | Docker volume  |
| `state/`   | Telethon session-файл     | Docker volume  |

Оба каталога переживают перезапуск контейнера.

---

## Команды бота

| Команда              | Описание                                                                                          |
|----------------------|---------------------------------------------------------------------------------------------------|
| `/start`             | Приветствие и регистрация. Показывает описание бота и доступные команды                           |
| `/help`              | Справка по всем командам                                                                          |
| `/add <канал>`       | Подписаться на канал (`@username` или `t.me/channel`). Бот начнёт пересылать новые сообщения      |
| `/remove <канал>`    | Отписаться от канала (`@username` или `t.me/channel`)                                             |
| `/list`              | Список подписок с inline-кнопками для быстрого удаления                                           |
| `/topics`            | Доступные темы из каталога (~30 категорий). Нажатие подписывает на все каналы темы                 |
| `/mytopics`          | Управление подписками на темы с кнопками для отписки                                              |
| `/pause`             | Приостановить ленту (подписки сохраняются)                                                        |
| `/resume`            | Возобновить ленту после паузы                                                                     |

---

## Архитектура

Один Python-процесс с тремя async-компонентами:

```
┌─────────────────────────────────────────────────────────────────┐
│                        main.py (asyncio)                        │
│                                                                 │
│  ┌──────────────────┐  ┌───────────────────┐  ┌──────────────┐ │
│  │   aiogram Bot     │  │  Telethon Client   │  │   Forwarder  │ │
│  │  (UI для юзера)   │  │ (читает каналы)    │  │ (пересылка)  │ │
│  └────────┬─────────┘  └────────┬───────────┘  └──────┬───────┘ │
│           │                     │                      │        │
│           └─────────┬───────────┴──────────────┬───────┘        │
│                     │                          │                │
│              ┌──────┴──────┐           ┌───────┴───────┐        │
│              │  SQLite DB  │           │  asyncio      │        │
│              │ (aiosqlite) │           │    Queue      │        │
│              └─────────────┘           └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Поток данных

1. **Telethon** обнаруживает новое сообщение в отслеживаемом канале
2. Система находит подписанных пользователей в БД
3. Задания на пересылку помещаются в `asyncio.Queue`
4. **Forwarder-воркеры** извлекают задания и вызывают `bot.forward_message()` с rate limit (~25 msg/sec)
5. Перед пересылкой проверяется **дедупликация** — каждое сообщение пересылается пользователю только один раз

### Гибридный мониторинг каналов

| Тип       | Условие                     | Метод                                       |
|-----------|-----------------------------|---------------------------------------------|
| Реалтайм  | >= 3 подписчиков бота       | Telethon join + event handler               |
| Поллинг   | < 3 подписчиков бота        | Периодический опрос через `get_messages()`  |

Порог переключения настраивается через `JOIN_THRESHOLD` в `.env`.

### Обработка ошибок

| Ситуация                     | Обработка                                                                       |
|------------------------------|---------------------------------------------------------------------------------|
| Юзер заблокировал бота       | `TelegramForbiddenError` — лента ставится на паузу                              |
| Канал стал приватным         | `ChannelPrivateError` — подписчики уведомляются                                 |
| Rate limit Telegram          | `RetryAfter` — ожидание и повтор; очередь гарантирует: ничего не потеряется     |
| Ошибка пересылки             | Максимум 3 попытки, затем задание отбрасывается с логированием                  |
| Перезапуск бота              | Догоняет пропущенные посты по `last_message_id` через `get_messages(min_id=…)`  |

---

## Конфигурация

Все настройки хранятся в файле `.env` (скопировать из `.env.example`):

| Переменная               | Описание                                  | По умолчанию / Пример        |
|--------------------------|-------------------------------------------|-------------------------------|
| `BOT_TOKEN`              | Токен бота от @BotFather                  | —                             |
| `TELEGRAM_API_ID`        | API ID от my.telegram.org                 | —                             |
| `TELEGRAM_API_HASH`      | API Hash от my.telegram.org               | —                             |
| `TELEGRAM_PHONE`         | Номер телефона сервисного аккаунта        | `+1234567890`                 |
| `SESSION_NAME`           | Имя/путь файла сессии Telethon            | `state/newsfeed_service`      |
| `DB_PATH`                | Путь к файлу SQLite                       | `runtime/bot.db`              |
| `CATALOG_PATH`           | Путь к каталогу каналов                   | `data/channel_catalog.json`   |
| `JOIN_THRESHOLD`         | Мин. подписчиков для join канала           | `3`                           |
| `POLL_INTERVAL_DEFAULT`  | Интервал поллинга (секунды)               | `120`                         |
| `FORWARD_RATE_LIMIT`     | Лимит пересылки (msg/sec)                 | `25`                          |
| `FORWARD_WORKERS`        | Количество воркеров пересылки             | `3`                           |
| `LOG_LEVEL`              | Уровень логирования                       | `INFO`                        |

---

## Структура проекта

```
TelegramNewsFeedBot/
│
├── bot/
│   ├── main.py                        # Точка входа
│   ├── config.py                      # Загрузка конфигурации из .env
│   │
│   ├── db/
│   │   ├── database.py                # Подключение к SQLite, миграции
│   │   ├── models.py                  # Dataclass-модели
│   │   └── queries.py                 # SQL-запросы
│   │
│   ├── telegram_bot/
│   │   ├── handlers/
│   │   │   ├── start.py               # /start, /help
│   │   │   ├── channels.py            # /add, /remove, /list
│   │   │   ├── topics.py              # /topics, /mytopics
│   │   │   └── settings.py            # /pause, /resume
│   │   ├── keyboards.py               # Inline-клавиатуры
│   │   ├── callbacks.py               # Обработка нажатий кнопок
│   │   └── middlewares.py             # Автоматическая регистрация
│   │
│   ├── channel_monitor/
│   │   ├── client.py                  # Telethon-клиент
│   │   ├── event_handler.py           # Реалтайм для joined каналов
│   │   ├── poller.py                  # Поллинг для остальных
│   │   ├── manager.py                 # Логика join/leave каналов
│   │   └── searcher.py               # Поиск каналов
│   │
│   └── forwarder/
│       ├── pipeline.py                # Очередь + воркеры + дедупликация
│       └── rate_limiter.py            # Token bucket rate limiter
│
├── data/
│   └── channel_catalog.json           # Каталог каналов по темам
│
├── scripts/
│   └── seed_catalog.py                # Загрузка каталога в БД
│
├── runtime/                           # SQLite (Docker volume)
├── state/                             # Telethon session (Docker volume)
├── tests/                             # Unit-тесты
├── docs/                              # Документация и планы
│
├── Dockerfile
├── docker-compose.yml
├── .env.example                       # Шаблон конфигурации
├── requirements.txt                   # Python-зависимости
└── README.md
```

---

## Тестирование

```bash
# Запуск всех тестов
pytest tests/ -v

# Запуск конкретного файла
pytest tests/test_queries.py -v
```

---

## Лицензия

Распространяется под лицензией [MIT](LICENSE).

Автор: **Andreas Maier**
