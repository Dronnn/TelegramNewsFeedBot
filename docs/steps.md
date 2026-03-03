# Telegram News Feed Bot — Пошаговый процесс разработки

## BOOTSTRAP — ЧИТАЙ ЭТО ПЕРВЫМ ПРИ КАЖДОМ ЗАПУСКЕ

Этот файл — главный источник правды для процесса разработки.
При каждом новом запуске сессии выполни следующее:

### 1. Восстанови контекст
- Прочитай `docs/plan.md` — там полное описание проекта, архитектура, схема БД, стек
- Прочитай этот файл (`docs/steps.md`) — найди первый незакрытый шаг (без `[x]`)

### 2. Найди текущий шаг
- Ищи первую строку с `- [ ]` — это следующий шаг для выполнения
- Все строки с `- [x]` уже выполнены — не трогай их

### 3. Прочитай контекст фазы
- У каждой фазы есть секция **Контекст** — прочитай её, чтобы понять что уже сделано
- Прочитай файлы, перечисленные в контексте — это твои зависимости

### 4. Выполни ТОЛЬКО один шаг
- Выполни ровно один незакрытый шаг
- Поставь `[x]` в этом файле
- Сделай коммит

### 5. Правила
- На этом Mac **только пишем код**. Ничего не устанавливаем, ничего не запускаем
- Все зависимости — только в venv (но venv создаётся на другой машине)
- Никаких секретов в коде или git. Только в `.env` и `.env.example` с плейсхолдерами
- GitHub-репозиторий публичный

---

## Фаза 0: Инициализация проекта

**Контекст фазы**: Проект пустой. Нужно создать базовые файлы и залить на GitHub.

- [x] **Шаг 001**: Инициализировать git-репозиторий (`git init`)
- [x] **Шаг 002**: Создать `.gitignore` (venv, .env, __pycache__, data/bot.db, docs/, logs/, *.session)
- [x] **Шаг 003**: Создать `.env.example` с плейсхолдерами (без реальных данных) и env файл с нужными данными, но не комитить его чтобы секреты не утекли
- [x] **Шаг 004**: Создать `README.md` — описание проекта, стек, инструкция по настройке
- [x] **Шаг 005**: Создать `docs/plan.md` — план разработки
- [x] **Шаг 006**: Создать `docs/steps.md` — этот файл
- [x] **Шаг 007**: Первый коммит + push в публичный GitHub-репозиторий

---

## Фаза 1: Структура проекта и конфигурация

**Контекст фазы**: Фаза 0 завершена — есть git, README, .gitignore, .env.example, docs/. Нужно создать структуру Python-проекта.
**Прочитай**: `docs/plan.md` секция "Структура проекта"

- [x] **Шаг 008**: Создать `requirements.txt` с четырьмя зависимостями (aiogram, telethon, aiosqlite, python-dotenv)
- [x] **Шаг 009**: Создать структуру директорий: `bot/`, `bot/db/`, `bot/telegram_bot/`, `bot/telegram_bot/handlers/`, `bot/channel_monitor/`, `bot/forwarder/`, `bot/utils/`, `data/`, `tests/`, `scripts/`
- [x] **Шаг 010**: Создать все `__init__.py` файлы (пустые) во всех пакетах
- [x] **Шаг 011**: Коммит "Add project structure and requirements"

---

## Фаза 2: Конфигурация

**Контекст фазы**: Структура директорий создана, requirements.txt есть. Нужно написать модуль загрузки конфигурации.
**Прочитай**: `.env.example`, `docs/plan.md` секция "Конфигурация (.env)"

- [x] **Шаг 012**: Написать `bot/config.py` — dataclass `Config` со всеми полями из .env
- [x] **Шаг 013**: В `bot/config.py` — функция `load_config()` загружает .env через python-dotenv и возвращает Config
- [x] **Шаг 014**: Коммит "Add configuration module"

---

## Фаза 3: Модели данных

**Контекст фазы**: Конфигурация готова (`bot/config.py`). Нужно написать dataclass-модели для всех сущностей.
**Прочитай**: `docs/plan.md` секция "БД: Схема (SQLite)" — там все поля

- [x] **Шаг 015**: Написать `bot/db/models.py` — dataclass `User` (user_id, username, first_name, is_paused, created_at)
- [x] **Шаг 016**: В `bot/db/models.py` — dataclass `Channel` (channel_id, username, title, is_joined, subscriber_count, last_message_id, poll_interval, last_polled_at, created_at)
- [x] **Шаг 017**: В `bot/db/models.py` — dataclass `Subscription` (user_id, channel_id)
- [x] **Шаг 018**: В `bot/db/models.py` — dataclass `CatalogEntry` (channel_username, title, category, tags, language)
- [x] **Шаг 019**: Коммит "Add data models"

---

## Фаза 4: База данных — подключение и схема

**Контекст фазы**: Модели готовы (`bot/db/models.py`). Нужно написать класс Database для подключения к SQLite и создания таблиц.
**Прочитай**: `bot/db/models.py`, `docs/plan.md` секция "БД: Схема (SQLite)" — SQL для всех таблиц

- [x] **Шаг 020**: Написать `bot/db/database.py` — класс `Database` с `__init__(self, db_path: str)`
- [x] **Шаг 021**: В `Database` — async метод `connect()`: открыть aiosqlite соединение, включить WAL mode, foreign keys
- [x] **Шаг 022**: В `Database` — async метод `close()`: закрыть соединение
- [x] **Шаг 023**: В `Database` — async метод `init_schema()`: выполнить CREATE TABLE IF NOT EXISTS для таблицы `users`
- [x] **Шаг 024**: В `init_schema()` — CREATE TABLE для `channels`
- [x] **Шаг 025**: В `init_schema()` — CREATE TABLE для `subscriptions`
- [x] **Шаг 026**: В `init_schema()` — CREATE TABLE для `user_topics`
- [x] **Шаг 027**: В `init_schema()` — CREATE TABLE для `catalog`
- [x] **Шаг 028**: В `init_schema()` — CREATE TABLE для `forwarded_messages` + индекс по forwarded_at
- [x] **Шаг 029**: Коммит "Add database connection and schema"

---

## Фаза 5: База данных — запросы для пользователей

**Контекст фазы**: Database класс готов (`bot/db/database.py`), модели готовы (`bot/db/models.py`). Пишем SQL-запросы для работы с юзерами.
**Прочитай**: `bot/db/database.py`, `bot/db/models.py`

- [x] **Шаг 030**: Написать `bot/db/queries.py` — async функция `add_user(db, user_id, username, first_name)` — INSERT OR IGNORE
- [x] **Шаг 031**: В `queries.py` — async функция `get_user(db, user_id)` — SELECT, возвращает User или None
- [x] **Шаг 032**: В `queries.py` — async функция `set_user_paused(db, user_id, is_paused)` — UPDATE
- [x] **Шаг 033**: В `queries.py` — async функция `get_active_subscribers(db, channel_id)` — SELECT user_id WHERE is_paused=0
- [x] **Шаг 034**: Коммит "Add user queries"

---

## Фаза 6: База данных — запросы для каналов

**Контекст фазы**: User-запросы готовы в `bot/db/queries.py`. Добавляем запросы для каналов.
**Прочитай**: `bot/db/queries.py` (то что уже написано), `bot/db/models.py`

- [x] **Шаг 035**: В `queries.py` — async функция `add_channel(db, channel_id, username, title)` — INSERT OR IGNORE
- [x] **Шаг 036**: В `queries.py` — async функция `get_channel(db, channel_id)` — SELECT, возвращает Channel или None
- [x] **Шаг 037**: В `queries.py` — async функция `get_channel_by_username(db, username)` — SELECT WHERE username=?
- [x] **Шаг 038**: В `queries.py` — async функция `update_channel_last_message(db, channel_id, message_id)` — UPDATE last_message_id
- [x] **Шаг 039**: В `queries.py` — async функция `update_channel_polled(db, channel_id)` — UPDATE last_polled_at
- [x] **Шаг 040**: В `queries.py` — async функция `set_channel_joined(db, channel_id, is_joined)` — UPDATE
- [x] **Шаг 041**: В `queries.py` — async функция `get_channels_to_poll(db)` — SELECT WHERE is_joined=0 AND subscriber_count>0
- [x] **Шаг 042**: В `queries.py` — async функция `get_joined_channel_ids(db)` — SELECT channel_id WHERE is_joined=1
- [x] **Шаг 043**: Коммит "Add channel queries"

---

## Фаза 7: База данных — запросы для подписок

**Контекст фазы**: Запросы для users и channels готовы в `bot/db/queries.py`. Добавляем запросы для подписок (связь user-channel).
**Прочитай**: `bot/db/queries.py`

- [x] **Шаг 044**: В `queries.py` — async функция `subscribe(db, user_id, channel_id)` — INSERT OR IGNORE + UPDATE subscriber_count +1
- [x] **Шаг 045**: В `queries.py` — async функция `unsubscribe(db, user_id, channel_id)` — DELETE + UPDATE subscriber_count -1
- [x] **Шаг 046**: В `queries.py` — async функция `get_user_subscriptions(db, user_id)` — SELECT с JOIN на channels, возвращает список Channel
- [x] **Шаг 047**: В `queries.py` — async функция `get_channel_subscriber_count(db, channel_id)` — SELECT subscriber_count
- [x] **Шаг 048**: Коммит "Add subscription queries"

---

## Фаза 8: База данных — запросы для тем и каталога

**Контекст фазы**: Запросы для users, channels, subscriptions готовы. Добавляем запросы для тем и каталога каналов.
**Прочитай**: `bot/db/queries.py`, `docs/plan.md` секция "Каталог тем"

- [x] **Шаг 049**: В `queries.py` — async функция `add_user_topic(db, user_id, topic_id)` — INSERT OR IGNORE
- [x] **Шаг 050**: В `queries.py` — async функция `remove_user_topic(db, user_id, topic_id)` — DELETE
- [x] **Шаг 051**: В `queries.py` — async функция `get_user_topics(db, user_id)` — SELECT topic_id
- [x] **Шаг 052**: В `queries.py` — async функция `search_catalog(db, category)` — SELECT WHERE category=?
- [x] **Шаг 053**: В `queries.py` — async функция `seed_catalog(db, entries)` — batch INSERT для загрузки каталога
- [x] **Шаг 054**: Коммит "Add topic and catalog queries"

---

## Фаза 9: База данных — запросы для дедупликации

**Контекст фазы**: Все основные запросы готовы. Добавляем запросы для таблицы forwarded_messages (предотвращение повторной пересылки).
**Прочитай**: `bot/db/queries.py`

- [ ] **Шаг 055**: В `queries.py` — async функция `is_forwarded(db, channel_id, message_id, user_id)` — SELECT EXISTS
- [ ] **Шаг 056**: В `queries.py` — async функция `mark_forwarded(db, channel_id, message_id, user_id)` — INSERT
- [ ] **Шаг 057**: В `queries.py` — async функция `cleanup_old_forwarded(db, days=7)` — DELETE WHERE forwarded_at < ?
- [ ] **Шаг 058**: Коммит "Add dedup queries"

---

## Фаза 10: Unit-тесты для БД

**Контекст фазы**: Весь слой БД готов (`bot/db/database.py`, `bot/db/models.py`, `bot/db/queries.py`). Пишем тесты для всех запросов.
**Прочитай**: `bot/db/queries.py`, `bot/db/database.py`, `bot/db/models.py`

- [ ] **Шаг 059**: Создать `tests/conftest.py` — pytest fixture для in-memory SQLite Database (async)
- [ ] **Шаг 060**: Написать `tests/test_queries.py` — тест `test_add_and_get_user`: добавить юзера, получить его обратно
- [ ] **Шаг 061**: Тест `test_add_user_duplicate`: повторный INSERT не падает
- [ ] **Шаг 062**: Тест `test_set_user_paused`: пауза/resume
- [ ] **Шаг 063**: Тест `test_add_channel_and_get`: добавить канал, получить
- [ ] **Шаг 064**: Тест `test_subscribe_and_unsubscribe`: подписка/отписка, проверить subscriber_count
- [ ] **Шаг 065**: Тест `test_get_user_subscriptions`: список подписок юзера
- [ ] **Шаг 066**: Тест `test_get_active_subscribers`: только не-paused юзеры
- [ ] **Шаг 067**: Тест `test_is_forwarded_and_mark`: дедупликация
- [ ] **Шаг 068**: Тест `test_cleanup_old_forwarded`: удаление старых записей
- [ ] **Шаг 069**: Тест `test_seed_catalog`: загрузка каталога
- [ ] **Шаг 070**: Тест `test_search_catalog`: поиск по категории
- [ ] **Шаг 071**: Тест `test_user_topics`: добавление/удаление/получение тем
- [ ] **Шаг 072**: Добавить `pytest` и `pytest-asyncio` в `requirements.txt` (dev-секция)
- [ ] **Шаг 073**: Коммит "Add database unit tests"

---

## Фаза 11: Утилиты

**Контекст фазы**: БД слой + тесты готовы. Пишем вспомогательные утилиты.
**Прочитай**: ничего специального, простой модуль

- [ ] **Шаг 074**: Написать `bot/utils/logging.py` — функция `setup_logging(level)`: настройка logging с форматом `[%(asctime)s] %(name)s %(levelname)s: %(message)s`
- [ ] **Шаг 075**: Коммит "Add logging utility"

---

## Фаза 12: aiogram-бот — скелет

**Контекст фазы**: БД и утилиты готовы. Начинаем писать Telegram-бот на aiogram. Middleware для авторегистрации юзеров + базовые команды /start, /help.
**Прочитай**: `bot/db/queries.py` (функция add_user), `bot/config.py`, `docs/plan.md` секция "Команды бота"

- [ ] **Шаг 076**: Написать `bot/telegram_bot/middlewares.py` — класс `UserRegistrationMiddleware`: на каждое сообщение проверять и регистрировать юзера в БД
- [ ] **Шаг 077**: Написать `bot/telegram_bot/handlers/start.py` — handler для `/start`: приветственное сообщение с кратким описанием бота
- [ ] **Шаг 078**: В `handlers/start.py` — handler для `/help`: список всех команд с описанием
- [ ] **Шаг 079**: Написать `bot/telegram_bot/handlers/__init__.py` — функция `register_all_handlers(router)` подключает все обработчики
- [ ] **Шаг 080**: Коммит "Add bot skeleton with /start and /help"

---

## Фаза 13: aiogram-бот — клавиатуры

**Контекст фазы**: Скелет бота готов (start, help, middleware). Пишем inline-клавиатуры для всех интерактивных элементов.
**Прочитай**: `bot/telegram_bot/handlers/start.py`, `docs/plan.md` секция "Команды бота"

- [ ] **Шаг 081**: Написать `bot/telegram_bot/keyboards.py` — функция `channel_list_keyboard(channels)`: inline-кнопки с каналами и кнопкой [Удалить]
- [ ] **Шаг 082**: В `keyboards.py` — функция `topics_keyboard(topics, user_topics)`: inline-кнопки со всеми темами, отмечены выбранные
- [ ] **Шаг 083**: В `keyboards.py` — функция `my_topics_keyboard(user_topics)`: inline-кнопки с выбранными темами и кнопкой [Отписаться]
- [ ] **Шаг 084**: В `keyboards.py` — функция `confirm_keyboard()`: кнопки [Да] [Нет] для подтверждений
- [ ] **Шаг 085**: Коммит "Add inline keyboards"

---

## Фаза 14: aiogram-бот — команды каналов

**Контекст фазы**: Клавиатуры готовы (`bot/telegram_bot/keyboards.py`). Пишем handlers для /add, /remove, /list. Пока resolve_channel будет заглушкой.
**Прочитай**: `bot/telegram_bot/keyboards.py`, `bot/db/queries.py` (subscribe, unsubscribe, get_user_subscriptions)

- [ ] **Шаг 086**: Написать `bot/telegram_bot/handlers/channels.py` — handler для `/add`: парсит аргумент @channel или t.me/channel
- [ ] **Шаг 087**: В handler `/add` — валидация: проверить что аргумент передан, вернуть ошибку если нет
- [ ] **Шаг 088**: В handler `/add` — вызвать `manager.resolve_channel()` для получения channel_id и title (заглушка пока)
- [ ] **Шаг 089**: В handler `/add` — вызвать `queries.add_channel()` и `queries.subscribe()`, ответить юзеру
- [ ] **Шаг 090**: В `handlers/channels.py` — handler для `/remove`: парсит @channel, вызывает `queries.unsubscribe()`
- [ ] **Шаг 091**: В handler `/remove` — проверить что юзер подписан, вернуть ошибку если нет
- [ ] **Шаг 092**: В `handlers/channels.py` — handler для `/list`: получить подписки юзера, показать с inline-кнопками
- [ ] **Шаг 093**: Коммит "Add /add, /remove, /list handlers"

---

## Фаза 15: aiogram-бот — callback-обработчики

**Контекст фазы**: Handlers и keyboards готовы. Пишем обработчики нажатий inline-кнопок.
**Прочитай**: `bot/telegram_bot/keyboards.py`, `bot/telegram_bot/handlers/channels.py`, `bot/db/queries.py`

- [ ] **Шаг 094**: Написать `bot/telegram_bot/callbacks.py` — handler для callback `remove_channel:{channel_id}`: отписать юзера, обновить сообщение
- [ ] **Шаг 095**: В `callbacks.py` — handler для callback `subscribe_topic:{topic_id}`: подписать на тему
- [ ] **Шаг 096**: В `callbacks.py` — handler для callback `unsubscribe_topic:{topic_id}`: отписать от темы
- [ ] **Шаг 097**: Коммит "Add callback handlers for inline buttons"

---

## Фаза 16: aiogram-бот — команды тем

**Контекст фазы**: Callback-обработчики готовы. Пишем handlers для /topics и /mytopics. Юзер выбирает тему — бот подписывает на все каналы этой темы.
**Прочитай**: `bot/telegram_bot/callbacks.py`, `bot/telegram_bot/keyboards.py`, `bot/db/queries.py` (search_catalog, add_user_topic, get_user_topics)

- [ ] **Шаг 098**: Написать `bot/telegram_bot/handlers/topics.py` — handler для `/topics`: показать все темы из каталога с inline-кнопками
- [ ] **Шаг 099**: В handler `/topics` — при нажатии на тему: подписать юзера на все каналы этой темы из каталога
- [ ] **Шаг 100**: В `handlers/topics.py` — handler для `/mytopics`: показать выбранные темы с кнопками [Отписаться]
- [ ] **Шаг 101**: В handler `/mytopics` — при отписке от темы: отписать от всех каналов этой темы
- [ ] **Шаг 102**: Коммит "Add /topics and /mytopics handlers"

---

## Фаза 17: aiogram-бот — pause/resume

**Контекст фазы**: Все основные команды бота готовы. Добавляем /pause и /resume.
**Прочитай**: `bot/db/queries.py` (set_user_paused)

- [ ] **Шаг 103**: Написать `bot/telegram_bot/handlers/settings.py` — handler для `/pause`: вызвать set_user_paused(True), ответить юзеру
- [ ] **Шаг 104**: В `handlers/settings.py` — handler для `/resume`: вызвать set_user_paused(False), ответить юзеру
- [ ] **Шаг 105**: Коммит "Add /pause and /resume handlers"

---

## Фаза 18: Telethon-клиент

**Контекст фазы**: Весь aiogram-бот готов (UI). Начинаем писать Telethon-клиент для чтения каналов. Telethon использует MTProto (Client API) — позволяет читать любые публичные каналы.
**Прочитай**: `bot/config.py`, `docs/plan.md` секция "Архитектура"

- [ ] **Шаг 106**: Написать `bot/channel_monitor/client.py` — async функция `create_telethon_client(config)`: создать TelegramClient с api_id, api_hash, session_name
- [ ] **Шаг 107**: В `client.py` — async функция `start_telethon_client(client, phone)`: вызвать client.start(phone=phone)
- [ ] **Шаг 108**: В `client.py` — async функция `resolve_channel(client, channel_ref)`: принимает @username или t.me/... ссылку, возвращает (channel_id, username, title) через client.get_entity()
- [ ] **Шаг 109**: Коммит "Add Telethon client setup"

---

## Фаза 19: Rate limiter

**Контекст фазы**: Telethon-клиент готов. Пишем rate limiter для ограничения скорости пересылки (Telegram Bot API лимит ~30 msg/sec, ставим 25 для запаса).
**Прочитай**: `docs/plan.md` секция "Архитектура" — про rate limit

- [ ] **Шаг 110**: Написать `bot/forwarder/rate_limiter.py` — класс `TokenBucketRateLimiter(rate, burst)`
- [ ] **Шаг 111**: В `TokenBucketRateLimiter` — `__init__`: инициализировать tokens, last_refill, asyncio.Lock
- [ ] **Шаг 112**: В `TokenBucketRateLimiter` — async метод `acquire()`: ждать пока будет доступен токен, с рефилом
- [ ] **Шаг 113**: Коммит "Add token bucket rate limiter"

---

## Фаза 20: Unit-тесты для rate limiter

**Контекст фазы**: Rate limiter готов (`bot/forwarder/rate_limiter.py`). Пишем тесты.
**Прочитай**: `bot/forwarder/rate_limiter.py`

- [ ] **Шаг 114**: Написать `tests/test_rate_limiter.py` — тест `test_acquire_without_wait`: первые N запросов проходят сразу (до burst)
- [ ] **Шаг 115**: Тест `test_acquire_with_wait`: после исчерпания burst, acquire ждёт
- [ ] **Шаг 116**: Тест `test_rate_over_time`: за 1 секунду проходит примерно rate запросов
- [ ] **Шаг 117**: Коммит "Add rate limiter tests"

---

## Фаза 21: Pipeline пересылки

**Контекст фазы**: Rate limiter готов. Пишем основной pipeline: asyncio.Queue + воркеры + дедупликация + обработка ошибок. Это ядро системы пересылки.
**Прочитай**: `bot/forwarder/rate_limiter.py`, `bot/db/queries.py` (is_forwarded, mark_forwarded), `docs/plan.md` секция "Архитектура"

- [ ] **Шаг 118**: Написать `bot/forwarder/pipeline.py` — класс `ForwardingPipeline(bot, db, rate_limiter, num_workers)`
- [ ] **Шаг 119**: В `ForwardingPipeline` — `__init__`: создать asyncio.Queue, сохранить зависимости
- [ ] **Шаг 120**: В `ForwardingPipeline` — async метод `enqueue(channel_id, message_id, user_id)`: положить задание в очередь
- [ ] **Шаг 121**: В `ForwardingPipeline` — async метод `_worker()`: бесконечный цикл — получить задание из очереди, проверить дедупликацию, переслать
- [ ] **Шаг 122**: В `_worker()` — дедупликация: вызвать `queries.is_forwarded()`, пропустить если уже переслано
- [ ] **Шаг 123**: В `_worker()` — вызвать `rate_limiter.acquire()` перед пересылкой
- [ ] **Шаг 124**: В `_worker()` — вызвать `bot.forward_message(chat_id=user_id, from_chat_id=channel_id, message_id=message_id)`
- [ ] **Шаг 125**: В `_worker()` — вызвать `queries.mark_forwarded()` после успешной пересылки
- [ ] **Шаг 126**: В `_worker()` — обработка TelegramForbiddenError: юзер заблокировал бота -> set_user_paused(True)
- [ ] **Шаг 127**: В `_worker()` — обработка TelegramRetryAfter: вернуть задание в очередь, подождать retry_after секунд
- [ ] **Шаг 128**: В `_worker()` — обработка общих ошибок: залогировать, продолжить
- [ ] **Шаг 129**: В `ForwardingPipeline` — async метод `start()`: запустить num_workers воркеров как asyncio.Task
- [ ] **Шаг 130**: В `ForwardingPipeline` — async метод `stop()`: отменить все воркеры, дождаться завершения
- [ ] **Шаг 131**: Коммит "Add forwarding pipeline with dedup and error handling"

---

## Фаза 22: Unit-тесты для pipeline

**Контекст фазы**: Pipeline готов (`bot/forwarder/pipeline.py`). Пишем тесты с моками.
**Прочитай**: `bot/forwarder/pipeline.py`, `bot/forwarder/rate_limiter.py`

- [ ] **Шаг 132**: Написать `tests/test_pipeline.py` — mock для bot.forward_message, mock для db
- [ ] **Шаг 133**: Тест `test_enqueue_and_forward`: добавить задание -> воркер пересылает -> mark_forwarded вызван
- [ ] **Шаг 134**: Тест `test_dedup_skip`: если is_forwarded=True -> пропуск, forward_message не вызван
- [ ] **Шаг 135**: Тест `test_user_blocked`: TelegramForbiddenError -> set_user_paused(True)
- [ ] **Шаг 136**: Коммит "Add pipeline tests"

---

## Фаза 23: Channel Manager — логика join/leave

**Контекст фазы**: Pipeline + Telethon-клиент готовы. Пишем ChannelManager — центральный компонент, который решает join или poll для каждого канала.
**Прочитай**: `bot/channel_monitor/client.py`, `bot/db/queries.py` (get_channel_subscriber_count, set_channel_joined), `bot/config.py` (JOIN_THRESHOLD), `docs/plan.md` секция "Гибридный мониторинг каналов"

- [ ] **Шаг 137**: Написать `bot/channel_monitor/manager.py` — класс `ChannelManager(telethon_client, db, config)`
- [ ] **Шаг 138**: В `ChannelManager` — `__init__`: сохранить зависимости, создать `self.joined_channels: set[int]`
- [ ] **Шаг 139**: В `ChannelManager` — async метод `load_joined_channels()`: загрузить из БД в self.joined_channels
- [ ] **Шаг 140**: В `ChannelManager` — async метод `resolve_and_add_channel(channel_ref)`: resolve через Telethon, добавить в БД, вернуть Channel
- [ ] **Шаг 141**: В `ChannelManager` — async метод `on_subscription_change(channel_id)`: пересчитать subscriber_count, решить join/leave
- [ ] **Шаг 142**: В `on_subscription_change` — если count >= JOIN_THRESHOLD и not is_joined: join через Telethon, обновить БД и joined_channels
- [ ] **Шаг 143**: В `on_subscription_change` — если count < JOIN_THRESHOLD и is_joined: leave через Telethon, обновить БД и joined_channels
- [ ] **Шаг 144**: В `on_subscription_change` — если count == 0: удалить канал из БД
- [ ] **Шаг 145**: Коммит "Add channel manager with join/leave logic"

---

## Фаза 24: Unit-тесты для Channel Manager

**Контекст фазы**: ChannelManager готов (`bot/channel_monitor/manager.py`). Пишем тесты с моками Telethon.
**Прочитай**: `bot/channel_monitor/manager.py`

- [ ] **Шаг 146**: Написать `tests/test_manager.py` — mock для Telethon client и DB
- [ ] **Шаг 147**: Тест `test_join_on_threshold`: при subscriber_count >= 3 вызывается JoinChannelRequest
- [ ] **Шаг 148**: Тест `test_leave_on_below_threshold`: при count < 3 вызывается LeaveChannelRequest
- [ ] **Шаг 149**: Тест `test_cleanup_on_zero`: при count == 0 канал удаляется
- [ ] **Шаг 150**: Коммит "Add channel manager tests"

---

## Фаза 25: Event handler — реалтайм для joined каналов

**Контекст фазы**: ChannelManager готов. Пишем обработчик новых сообщений из joined каналов (реалтайм через Telethon events).
**Прочитай**: `bot/channel_monitor/manager.py`, `bot/forwarder/pipeline.py`, `bot/db/queries.py` (get_active_subscribers, update_channel_last_message)

- [ ] **Шаг 151**: Написать `bot/channel_monitor/event_handler.py` — async функция `setup_event_handler(telethon_client, channel_manager, pipeline, db)`
- [ ] **Шаг 152**: В `setup_event_handler` — зарегистрировать обработчик events.NewMessage
- [ ] **Шаг 153**: В обработчике — проверить что event.chat_id в joined_channels
- [ ] **Шаг 154**: В обработчике — обновить last_message_id канала
- [ ] **Шаг 155**: В обработчике — получить active_subscribers, для каждого вызвать pipeline.enqueue()
- [ ] **Шаг 156**: Коммит "Add real-time event handler for joined channels"

---

## Фаза 26: Poller — поллинг для не-joined каналов

**Контекст фазы**: Event handler готов (для joined). Пишем poller для остальных каналов — периодический опрос через get_messages().
**Прочитай**: `bot/channel_monitor/event_handler.py`, `bot/forwarder/pipeline.py`, `bot/db/queries.py` (get_channels_to_poll)

- [ ] **Шаг 157**: Написать `bot/channel_monitor/poller.py` — класс `ChannelPoller(telethon_client, db, pipeline, config)`
- [ ] **Шаг 158**: В `ChannelPoller` — async метод `poll_once(channel)`: вызвать get_messages(min_id=last_message_id, limit=20)
- [ ] **Шаг 159**: В `poll_once` — обработка ChannelPrivateError: канал стал приватным, залогировать
- [ ] **Шаг 160**: В `poll_once` — для каждого нового сообщения: получить subscribers, вызвать pipeline.enqueue()
- [ ] **Шаг 161**: В `poll_once` — обновить last_message_id и last_polled_at
- [ ] **Шаг 162**: В `ChannelPoller` — async метод `run()`: бесконечный цикл — получить каналы для поллинга, опросить каждый с задержкой 0.1с
- [ ] **Шаг 163**: В `run()` — между полными циклами спать 30 секунд
- [ ] **Шаг 164**: Коммит "Add channel poller for non-joined channels"

---

## Фаза 27: Каталог каналов

**Контекст фазы**: Вся система мониторинга готова. Пишем JSON-файл с каталогом каналов по темам и скрипт для загрузки в БД.
**Прочитай**: `docs/plan.md` секция "Каталог тем", `bot/db/queries.py` (seed_catalog)

- [ ] **Шаг 165**: Создать `data/channel_catalog.json` — структура с ~5 темами и 2-3 каналами в каждой (заглушки для начала)
- [ ] **Шаг 166**: Написать `scripts/seed_catalog.py` — скрипт: прочитать JSON, вызвать queries.seed_catalog()
- [ ] **Шаг 167**: Коммит "Add channel catalog seed data and script"

---

## Фаза 28: Searcher — поиск каналов

**Контекст фазы**: Каталог готов. Пишем модуль поиска каналов: сначала по каталогу, если не хватает — через Telegram API.
**Прочитай**: `data/channel_catalog.json`, `bot/db/queries.py` (search_catalog), `bot/channel_monitor/client.py`

- [ ] **Шаг 168**: Написать `bot/channel_monitor/searcher.py` — класс `ChannelSearcher(telethon_client, db)`
- [ ] **Шаг 169**: В `ChannelSearcher` — async метод `search_by_topic(topic_id)`: найти каналы в каталоге по category=topic_id
- [ ] **Шаг 170**: В `ChannelSearcher` — async метод `search_telegram(query, limit=20)`: вызвать contacts.SearchRequest через Telethon, отфильтровать только каналы
- [ ] **Шаг 171**: В `ChannelSearcher` — async метод `search_combined(topic_id, query)`: сначала каталог, если мало результатов — Telegram API
- [ ] **Шаг 172**: Коммит "Add channel searcher"

---

## Фаза 29: Unit-тесты для searcher

**Контекст фазы**: Searcher готов (`bot/channel_monitor/searcher.py`). Пишем тесты.
**Прочитай**: `bot/channel_monitor/searcher.py`

- [ ] **Шаг 173**: Написать `tests/test_searcher.py` — тест `test_search_by_topic_from_catalog`
- [ ] **Шаг 174**: Тест `test_search_combined_catalog_enough`: достаточно результатов из каталога, Telegram API не вызывается
- [ ] **Шаг 175**: Коммит "Add searcher tests"

---

## Фаза 30: main.py — точка входа

**Контекст фазы**: Все компоненты готовы по отдельности. Собираем всё вместе в main.py — точке входа приложения.
**Прочитай**: `bot/config.py`, `bot/db/database.py`, `bot/channel_monitor/client.py`, `bot/channel_monitor/manager.py`, `bot/channel_monitor/event_handler.py`, `bot/channel_monitor/poller.py`, `bot/forwarder/pipeline.py`, `bot/telegram_bot/handlers/__init__.py`

- [ ] **Шаг 176**: Написать `bot/main.py` — async функция `main()`: загрузить config
- [ ] **Шаг 177**: В `main()` — инициализировать Database, вызвать init_schema()
- [ ] **Шаг 178**: В `main()` — создать Telethon client, вызвать start()
- [ ] **Шаг 179**: В `main()` — создать aiogram Bot и Dispatcher
- [ ] **Шаг 180**: В `main()` — зарегистрировать все handlers и middleware
- [ ] **Шаг 181**: В `main()` — создать ChannelManager, загрузить joined_channels
- [ ] **Шаг 182**: В `main()` — создать ForwardingPipeline, запустить воркеры
- [ ] **Шаг 183**: В `main()` — вызвать setup_event_handler()
- [ ] **Шаг 184**: В `main()` — создать ChannelPoller, запустить как asyncio.Task
- [ ] **Шаг 185**: В `main()` — запустить задачу очистки forwarded_messages (раз в час)
- [ ] **Шаг 186**: В `main()` — запустить dp.start_polling(bot) в try/finally с graceful shutdown
- [ ] **Шаг 187**: В `bot/main.py` — блок `if __name__ == "__main__": asyncio.run(main())`
- [ ] **Шаг 188**: Коммит "Add main entry point"

---

## Фаза 31: Интеграция handlers с реальными зависимостями

**Контекст фазы**: main.py собран. Обновляем handlers — заменяем заглушки на реальные вызовы ChannelManager, Searcher и т.д.
**Прочитай**: `bot/telegram_bot/handlers/channels.py`, `bot/telegram_bot/handlers/topics.py`, `bot/channel_monitor/manager.py`, `bot/channel_monitor/searcher.py`

- [ ] **Шаг 189**: Обновить `handlers/channels.py` — `/add` теперь вызывает реальный channel_manager.resolve_and_add_channel()
- [ ] **Шаг 190**: Обновить `/add` — после подписки вызвать channel_manager.on_subscription_change()
- [ ] **Шаг 191**: Обновить `/remove` — после отписки вызвать channel_manager.on_subscription_change()
- [ ] **Шаг 192**: Обновить `handlers/topics.py` — `/topics` загружает реальный список тем из каталога
- [ ] **Шаг 193**: Обновить `/topics` — при подписке на тему вызвать resolve и subscribe для каждого канала
- [ ] **Шаг 194**: Коммит "Wire handlers to real dependencies"

---

## Фаза 32: Обработка ошибок

**Контекст фазы**: Всё работает в happy path. Добавляем обработку ошибок: каналы ушли в приват, юзеры заблокировали бота, graceful shutdown.
**Прочитай**: `docs/plan.md` секция "Обработка edge cases", `bot/channel_monitor/poller.py`, `bot/channel_monitor/event_handler.py`, `bot/forwarder/pipeline.py`, `bot/main.py`

- [ ] **Шаг 195**: В `channel_monitor/poller.py` — обработка ChannelPrivateError: уведомить подписанных юзеров, залогировать
- [ ] **Шаг 196**: В `channel_monitor/event_handler.py` — try/except вокруг основной логики, логирование ошибок
- [ ] **Шаг 197**: В `forwarder/pipeline.py` — максимум 3 ретрая для failed forward, после — drop с логом
- [ ] **Шаг 198**: В `bot/main.py` — graceful shutdown: отменить все задачи, закрыть Telethon, закрыть БД
- [ ] **Шаг 199**: Коммит "Add error handling and graceful shutdown"

---

## Фаза 33: Задача очистки

**Контекст фазы**: Обработка ошибок готова. Добавляем фоновую задачу: раз в час чистить старые записи из forwarded_messages (старше 7 дней).
**Прочитай**: `bot/main.py`, `bot/db/queries.py` (cleanup_old_forwarded)

- [ ] **Шаг 200**: В `bot/main.py` — async функция `cleanup_task(db)`: бесконечный цикл, каждый час вызывает cleanup_old_forwarded(db, days=7)
- [ ] **Шаг 201**: Коммит "Add periodic cleanup task"

---

## Фаза 34: README и финализация

**Контекст фазы**: Весь код готов. Обновляем README.md с полной документацией: установка, запуск, команды, архитектура, конфигурация.
**Прочитай**: текущий `README.md`, `docs/plan.md` — для справки по командам и архитектуре

- [ ] **Шаг 202**: Обновить `README.md` — добавить секцию "Установка и запуск" (venv, pip install, .env, запуск)
- [ ] **Шаг 203**: В `README.md` — секция "Команды бота" с описанием всех команд
- [ ] **Шаг 204**: В `README.md` — секция "Архитектура" с диаграммой
- [ ] **Шаг 205**: В `README.md` — секция "Конфигурация" со списком переменных .env
- [ ] **Шаг 206**: Финальный коммит "Update README with full documentation"

---

## Фаза 35: Заполнение каталога (отдельная задача)

**Контекст фазы**: Бот полностью готов. Расширяем каталог каналов до 30 тем с реальными каналами.
**Прочитай**: `data/channel_catalog.json` — текущая структура

- [ ] **Шаг 207**: Расширить `data/channel_catalog.json` до ~30 тем с реальными каналами
- [ ] **Шаг 208**: Коммит "Expand channel catalog to 30 topics"

---

## Итого: 208 шагов

Каждый шаг — маленькая атомарная задача.
Каждый шаг завершается коммитом.
Каждый шаг можно выполнить в отдельной сессии.
