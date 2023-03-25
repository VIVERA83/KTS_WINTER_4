# KTS_WINTER_4
Что? Где? Когда?

Пояснение к проекту.

__Приложение разбито на 5 компонента__
   - [bot](bot) 
   - [game_service](game_service)
   - [vk_api](vk_api) 
   - postgres
   - rabbitmq

# [vk_api](vk_api)
Отвечает за взаимодействие с социальной сетью ```В КОНТАКТЕ```. Обменивается сообщениями с социальной сетью. 
Сообщения полученный из социальной сети кладет в RabbitMQ, так же сообщения для социальной сети берет с брокера.
# [game_service](game_service)
Сервис отвечает за хранение и выдачу данных по игровому процессу. Реализованы 4 модели:
   - __User__ : информация по игроку 
   - GameSession : Информация по игровой сессии, капитан, участники команды
   - Round: Результаты раунда, кто давал ответ, какой ответ, и верный ли был дан ответ, номер раунда
   - Question: Список вопросов
# [bot](bot) 
Сердце приложения. 
   - Асинхронный подход.
   - Реализованы механизмы взаимодействия нескольких пользователей друг с другом в рамках одного бота.
   - Нет жесткой привязки к определенной социальной сети, инструменты сети используются только для визуализации диалога с пользователем
   - есть потенциал настройки бота для объединения пользователей из разных социальных сетей для общения 
(то есть пользователь из VK сможет общаться с пользователем из telegram) 


