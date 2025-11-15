### Быстрый старт

1. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```
2. **Настройка переменных окружения** (см. полный список в `notify_service/settings.py`):
   ```bash
   export DJANGO_SETTINGS_MODULE=notify_service.settings
   export SECRET_KEY=замени-на-свой
   export DATABASE_URL=postgres://user:pass@localhost:5432/photopoint
   export CELERY_BROKER_URL=redis://localhost:6379/0
   export CELERY_RESULT_BACKEND=redis://localhost:6379/1
   export TELEGRAM_BOT_TOKEN=твой-токен
   export SMS_PROVIDER_URL=https://sms.provider/api
   export SMS_PROVIDER_TOKEN=secret
   ```
3. **Миграции БД**
   ```bash
   python manage.py migrate
   ```
4. **Запуск dev-сервера**
   ```bash
   python manage.py runserver
   ```
5. **Запуск воркера Celery**
   ```bash
   celery -A notify_service worker -l info
   ```

### Особенности проекта

- API на DRF для создания уведомлений и отслеживания статуса (`/api/notifications/`).
- Celery-диспетчер с адаптерами по каналам и логированием каждой попытки доставки.
- PostgreSQL-модели с JSON-конфигурацией каналов и пользовательских метаданных.
- Расширяемая архитектура — новые каналы добавляются через наследование от `BaseChannel`.

Дополнительные детали по обработке и отказоустойчивости можно найти в комментариях кода.
