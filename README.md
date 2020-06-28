# Style_transfer_telegram_bot
Этот бот для телеграмма переносит стиль с одних фотографий на другие.

## Режимы работы бота

У бота есть 3 режима работы:
- Простой перенос стиля с одного изображения на другое (NST)
- Двойной перенос стиля с двух изображений на третье (NST)
- Перекрашивание лошадей в зебр (GAN)

### Простой перенос стиля с одного изображения на другое
В данном режиме бот переносит стиль с первого изображения на второй с заданными настройками.

Данный режим использует технологию Neural style transfer.

Для этого режима возможны 2 дополнительные настройки:
- Количество эпох (влияет на степень переноса изображения)
  - 25 эпох
  - 50 эпох
  - 100 эпох
  - 200 эпох
  - 300 эпох
  - 400 эпох
- Размер выходного изображения
  - 64х64 пикселя
  - 128х128 пикселей
  - 256х256 пикселей
  - 512х512 пикселей
  
Возможные результаты работы данного режима бота:

Изначальное изображение    |  Переносимый стиль        |  Итоговое изображение
:-------------------------:|:-------------------------:|:-------------------------:
<img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/corgi.jpg" height="250" width="250">  |  <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/style_1.jpg" height="250" width="181">  |   <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/corgi_st_1.jpeg" height="250"  width="250">


### Двойной перенос стиля с двух изображений на третье
В данном режиме бот переносит первый стиль на левую половину фото, второй стиль -- на правую.

Данный режим использует технологию Neural style transfer.

Для этого режима возможны 2 дополнительные настройки:
- Количество эпох (влияет на степень переноса изображения)
  - 25 эпох
  - 50 эпох
  - 100 эпох
  - 200 эпох
  - 300 эпох
  - 400 эпох
- Размер выходного изображения
  - 64х64 пикселя
  - 128х128 пикселей
  - 256х256 пикселей
  - 512х512 пикселей
  
Возможные результаты работы данного режима бота:
  
Изначальное изображение    |  Первый переносимый стиль |  Второй переносимый стиль |  Итоговое изображение
:-------------------------:|:-------------------------:|:-------------------------:|:-------------------------:
<img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/corgi.jpg" height="160" width="160">  |  <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/style_2.jpg" height="160" width="160">  |   <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/style_1.jpg" height="160" width="116">  |  <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/corgi_st_2.jpeg" height="160" width="160">

  
### Перекрашивание лошадей в зебр
В данном режиме бот раскрашивает лошадей на фото в полоски так, чтобы они были похожи на зебр, используя предобученную генеративную сеть из этого проекта: https://github.com/junyanz/pytorch-CycleGAN-and-pix2pix.

Данный режим использует технологию Generative adversarial networks.

Для этого режима возможна 1 дополнительная настройка:
- Размер выходного изображения
  - 64х64 пикселя
  - 128х128 пикселей
  - 256х256 пикселей
  - 512х512 пикселей
  
Возможные результаты работы данного режима боты:

Изначальное изображение    |  Итоговое изображение
:-------------------------:|:-------------------------:
<img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/horse_1.jpg" height="250" width="375">  |  <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/zebra_1.jpeg" height="250"  width="250">
<img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/horse_2.jpg" height="250" width="378">  |  <img src="https://github.com/alresin/Style_transfer_telegram_bot/blob/master/images/zebra_2.jpeg" height="250"  width="250">


## Информация по запуску бота.
Для запуска данного бота у себя необходимо добавить в основной каталог файл `config.py` со следующим содержанием:
```Python
  API_TOKEN = '<YOUR TOKEN>'

  DEBUG_ID = `<YOUR_DEBUG_ID>`
  
  GET_DEBUG_INFO = True

  LOGGING = True

  LOGGING_GAN = False
```

Где:
- `<YOUR TOKEN>` -- токен вашего бота, который можно получить у официального бота сервиса Telegram для создания собственных ботов: @BotFather,
- `<YOUR_DEBUG_ID>` -- id человека, которому будут приходить сообщения в телеграмм об ошибках,
- GET_DEBUG_INFO -- будет ли на указанный выше id отправляться информация об ошибках (если поставить `False`, чтобы не указывать id в строке выше),
- LOGGING -- будет ли выводится в консоль информация о том, какие действия сейчас совершает бот,
- LOGGING_GAN -- будет выводится вся информация о GAN сети, при каждом ее запуске.

_____

По всем вопросам обращаться в телеграм: @alresing