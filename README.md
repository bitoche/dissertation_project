## Структура проекта

## Запуск проекта
### `deprecated` Запуск без DOCKER
1. `make init` -- cоздать окружение
2. `make run` -- устанавливает зависимости и запускает проект
3. `make clean` -- удаляет окружение

### `default` Запуск через docker 
1. `docker compose build` в корне проекта
2. `docker compose up -d` в корне проекта
