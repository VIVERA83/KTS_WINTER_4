# KTS_WINTER_4

Что? Где? Когда?

Пояснение к проекту.

__Приложение разбито на 5 компонента__

- [bot](bot)
- [game_service](game_service)
- [vk_api](vk_api)
- postgres
- rabbitmq

# Простой Запуск
  ```commandline
  docker-compose up --build 
  ```
  Обратите внимание, что необходимо создать файл [.env](.env_example) и добавить VK__TOKEN и VK__GROUP_ID. И так же
  добавте несколько вопросов для игры, это можно сделать swagger ссылка  на swagger примерно такого вида http://0.0.0.0:8002 

# [vk_api](vk_api)

Отвечает за взаимодействие с социальной сетью ```В КОНТАКТЕ```. Обменивается сообщениями с социальной сетью.
Сообщения полученный из социальной сети кладет в RabbitMQ, так же сообщения для социальной сети берет с брокера.

Запуск:

- Как отдельный сервис через Docker:
    - Монтируем образ
  ```commandline
  docker build -f dockerfile_vk_api -t vk_api .
  ```
    - Запускаем
  ```commandline
  docker run --rm --name example_vk_api -p 8001:8001 -e VK__TOKEN="TOKEN" -e VK__GROUP_ID="210493394" -e RABBITMQ__USER="user" -e RABBITMQ__PASSWORD="password" vk_api
  ```

# [game_service](game_service)

Сервис отвечает за хранение и выдачу данных по игровому процессу. Реализованы 4 модели:

- __User__ : информация по игроку
- GameSession : Информация по игровой сессии, капитан, участники команды
- Round: Результаты раунда, кто давал ответ, какой ответ, и верный ли был дан ответ, номер раунда
- Question: Список вопросов

Запуск:

- Как отдельный сервис через Docker:
    - Монтируем образ
  ```commandline
  docker build -f dockerfile_game_service -t game_service .
  ```
    - Запускаем
  ```commandline
  docker run --rm --name test_game_service -p 8002:8002 -e POSTGRES__DB="kts" -e POSTGRES__USER="kts_user" -e POSTGRES__PASSWORD="kts_pass" game_service
  ```
  Обратите внимание, что при первом запуске, требуется сделать миграцию:
  
     - Заходим в контейнер
       ```commandline
       docker exec -it test_game_service bash
       ```
     - Делаем миграцию
       ```commandline
       alembic upgrade head
       ```

# [bot](bot)

Сердце приложения.

- Асинхронный подход.
- Реализованы механизмы взаимодействия нескольких пользователей друг с другом в рамках одного бота.
- Нет жесткой привязки к определенной социальной сети, инструменты сети используются только для визуализации диалога с
  пользователем
- есть потенциал настройки бота для объединения пользователей из разных социальных сетей для общения
  (то есть пользователь из VK сможет общаться с пользователем из telegram) 

Запуск:

- Как отдельный сервис через Docker:
    - Монтируем образ
  ```commandline
  docker build -f dockerfile_bot -t bot .
  ```
    - Запускаем
  ```commandline
  docker run --rm --name example_bot -p 8003:8003 -e RABBITMQ__USER="user" -e RABBITMQ__PASSWORD="password" bot
  ```

