import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.types import reply_keyboard

import asyncio  

from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import os
from copy import deepcopy
from urllib.parse import urljoin

from style_transfer import *
from gan import transfer
from config import *


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

photo_buffer = {}

class InfoAboutUser:
    def __init__(self):
        # default settigs
        self.settings = {'num_epochs': 50,
                         'imsize'    : 256}
        self.photos = []

    def set_default_settings(self):
        self.settings = {'num_epochs': 50,
                         'imsize'    : 256}



start_kb = InlineKeyboardMarkup()
start_kb.add( InlineKeyboardButton('Перенос одного стиля (NST)',
                                    callback_data='1_st') )
start_kb.add( InlineKeyboardButton('Перенос двух стилей (NST)',
                                    callback_data='2_st') )
start_kb.add( InlineKeyboardButton('Перекрасить лошадь в зебру (GAN)',
                                    callback_data='horse2zebra'))
start_kb.add( InlineKeyboardButton('Стилизация под Ван Гога (GAN)',
                                    callback_data='vangogh'))
start_kb.add( InlineKeyboardButton('Стилизация под Моне (GAN)',
                                    callback_data='monet'))


settings1_kb = InlineKeyboardMarkup()
settings1_kb.add( InlineKeyboardButton('Стандартные',
                                        callback_data='default') )
settings1_kb.add( InlineKeyboardButton('Расширенные',
                                        callback_data='castom') )
settings1_kb.add( InlineKeyboardButton('Назад',
                                        callback_data='main_menu') )

settings2_st_kb = InlineKeyboardMarkup()
settings2_st_kb.add( InlineKeyboardButton('Кол-во эпох',
                                        callback_data='num_epochs') )
settings2_st_kb.add( InlineKeyboardButton('Размер картинки',
                                        callback_data='imsize') )
settings2_st_kb.add( InlineKeyboardButton('Далее',
                                        callback_data='next') )
settings2_st_kb.add( InlineKeyboardButton('Назад',
                                        callback_data='1_st') )

settings2_gan_kb = InlineKeyboardMarkup()
settings2_gan_kb.add( InlineKeyboardButton('Размер картинки',
                                        callback_data='imsize') )
settings2_gan_kb.add( InlineKeyboardButton('Далее',
                                        callback_data='next') )
settings2_gan_kb.add( InlineKeyboardButton('Назад',
                                        callback_data='horse2zebra') )


# some of these settings isn`t available because of my GPU memory
num_epochs_kb = InlineKeyboardMarkup()
num_epochs_kb.add( InlineKeyboardButton('25', callback_data='num_epochs_25'))
num_epochs_kb.add( InlineKeyboardButton('50', callback_data='num_epochs_50'))
num_epochs_kb.add( InlineKeyboardButton('100', callback_data='num_epochs_100'))
num_epochs_kb.add( InlineKeyboardButton('200', callback_data='num_epochs_200'))
num_epochs_kb.add( InlineKeyboardButton('300', callback_data='num_epochs_300')) 
num_epochs_kb.add( InlineKeyboardButton('400', callback_data='num_epochs_400'))
num_epochs_kb.add( InlineKeyboardButton('Назад', callback_data='castom'))

# some of these settings isn`t available because of my GPU memory
imsize_kb = InlineKeyboardMarkup()
imsize_kb.add( InlineKeyboardButton('64 пикселя', callback_data='imsize_64'))
imsize_kb.add( InlineKeyboardButton('128 пикселей', callback_data='imsize_128'))
imsize_kb.add( InlineKeyboardButton('256 пикселей', callback_data='imsize_256'))
imsize_kb.add( InlineKeyboardButton('512 пикселей', callback_data='imsize_512'))
# imsize_kb.add( InlineKeyboardButton('1024 пикселя', callback_data='imsize_1024'))
imsize_kb.add( InlineKeyboardButton('Назад', callback_data='castom'))

cancel_kb = InlineKeyboardMarkup()
cancel_kb.add( InlineKeyboardButton('Отмена', callback_data='main_menu'))



# start
@dp.message_handler(commands=['start'])
async def send_welcome(message):
    sticker = open('./welcome_sticker.jpg', 'rb')
    await bot.send_sticker(message.chat.id, sticker)

    await bot.send_message(message.chat.id,
        f"Привет, {message.from_user.first_name}!\nЯ Style transfer бот. " +
        "Я умею переносить стиль с картинки на картинку. " +
        "Вот что я могу:", reply_markup=start_kb)

    # to remove reply keyboard
    # await bot.send_message(message.chat.id, "text", reply_markup = reply_keyboard.ReplyKeyboardRemove())

    photo_buffer[message.chat.id] = InfoAboutUser()


# help
@dp.message_handler(commands=['help'])
async def send_help(message):

    await bot.send_message(message.chat.id,
        "Вот что я могу:", reply_markup=start_kb)


# main menu
@dp.callback_query_handler(lambda c: c.data == 'main_menu')
async def main_menu(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Вот что я могу:")
    await callback_query.message.edit_reply_markup(reply_markup=start_kb)


# style transfer 1 style
@dp.callback_query_handler(lambda c: c.data == '1_st')
async def st_1_style(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Выбери настройки для переноса стиля:")
    await callback_query.message.edit_reply_markup(reply_markup = settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()

    photo_buffer[callback_query.from_user.id].st_type = 1


# style transfer 2 styles
@dp.callback_query_handler(lambda c: c.data == '2_st')
async def st_2_style(callback_query):
    await bot.answer_callback_query(callback_query.id)

    await callback_query.message.edit_text(
        "Первый стиль будет перенесен на левую половину картинки, второй -- на правую. " +
        "Выбери настройки для переноса стиля:")
    await callback_query.message.edit_reply_markup(reply_markup = settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()
    
    photo_buffer[callback_query.from_user.id].st_type = 2


# horse2zebra
@dp.callback_query_handler(lambda c: c.data == 'horse2zebra')
async def horse2zebra(callback_query):
    await bot.answer_callback_query(callback_query.id)

    await callback_query.message.edit_text(
        "Лошадь на твоей картинке будет перекрашена в зебру. " +
        "Выбери настройки для переноса стиля:")
    await callback_query.message.edit_reply_markup(reply_markup = settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()

    photo_buffer[callback_query.from_user.id].st_type = 'horse2zebra'


# vangogh
@dp.callback_query_handler(lambda c: c.data == 'vangogh')
async def vangogh(callback_query):
    await bot.answer_callback_query(callback_query.id)

    await callback_query.message.edit_text(
        "Твоя картинка будет стилизована под стиль Ван Гога. " +
        "Выбери настройки для переноса стиля:")
    await callback_query.message.edit_reply_markup(reply_markup = settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()

    photo_buffer[callback_query.from_user.id].st_type = 'vangogh'


# monet
@dp.callback_query_handler(lambda c: c.data == 'monet')
async def winter2summer(callback_query):
    await bot.answer_callback_query(callback_query.id)

    await callback_query.message.edit_text(
        "Твоя картинка будет стилизована под стиль Моне. " +
        "Выбери настройки для переноса стиля:")
    await callback_query.message.edit_reply_markup(reply_markup = settings1_kb)

    if callback_query.from_user.id not in photo_buffer:
        photo_buffer[callback_query.from_user.id] = InfoAboutUser()

    photo_buffer[callback_query.from_user.id].st_type = 'monet'


# default settings
@dp.callback_query_handler(lambda c: c.data == 'default')
async def default_set(callback_query):
    if MODE == 'EASY':
        await bot.send_message(callback_query.from_user.id, 
            "В данный момент бот работает в упрощенном режиме, для получения полного функционала бота " +
            "свяжитесь с создателем бота с целью перевести бота в нормальный режим работы. " + 
            "Пока можете ознакомится с меню или посетить страницу на github: " +
            "https://github.com/alresin/Style_transfer_telegram_bot")

        await bot.send_message(callback_query.from_user.id,
            "Что будем делать дальше?", reply_markup=start_kb)

        await callback_query.message.edit_reply_markup(reply_markup=cancel_kb)
            
        del photo_buffer[callback_query.from_user.id]


    elif MODE == 'NORMAL':
        await bot.answer_callback_query(callback_query.id)

        if photo_buffer[callback_query.from_user.id].st_type == 1:
            await callback_query.message.edit_text(
                "Пришли мне картинку, стиль с которой нужно перенести. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 2

        elif photo_buffer[callback_query.from_user.id].st_type == 2:
            await callback_query.message.edit_text(
                "Пришли мне картинку, стиль с которой нужно перенести на левую часть изображения. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")
            
            photo_buffer[callback_query.from_user.id].need_photos = 3

        elif photo_buffer[callback_query.from_user.id].st_type == 'horse2zebra':
            await callback_query.message.edit_text(
                "Пришли мне фотографию лошади, и я перекрашу ее в зебру. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 1

        elif photo_buffer[callback_query.from_user.id].st_type == 'vangogh':
            await callback_query.message.edit_text(
                "Пришли мне фотографию, и я добавлю на нее стиль Ван Гога. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 1

        elif photo_buffer[callback_query.from_user.id].st_type == 'monet':
            await callback_query.message.edit_text(
                "Пришли мне фотографию, и я добавлю на нее стиль Моне. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 1
        
        await callback_query.message.edit_reply_markup(reply_markup=cancel_kb)

        photo_buffer[callback_query.from_user.id].set_default_settings()


# castom settings
@dp.callback_query_handler(lambda c: c.data == 'castom')
async def castom_set(callback_query):
    await bot.answer_callback_query(callback_query.id)

    if photo_buffer[callback_query.from_user.id].st_type in ['horse2zebra', 'vangogh', 'monet']:
        await callback_query.message.edit_text(
            "Текущие настройки:" + 
            "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
            " пикселей\n\nВыбери настройки для изменения:")
        await callback_query.message.edit_reply_markup(reply_markup=settings2_gan_kb)

    else:
        await callback_query.message.edit_text(
            "Текущие настройки:" + 
            "\nКоличество эпох: " + str(photo_buffer[callback_query.from_user.id].settings['num_epochs']) +
            "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
            " пикселей\n\nВыбери настройки для изменения:")
        await callback_query.message.edit_reply_markup(reply_markup=settings2_st_kb)


# epochs number
@dp.callback_query_handler(lambda c: c.data == 'num_epochs')
async def set_num_epochs(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text(
        "Текущие настройки:" + 
        "\nКоличество эпох: " + str(photo_buffer[callback_query.from_user.id].settings['num_epochs']) +
        "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
        " пикселей\n\nВыбери количество эпох:")
    await callback_query.message.edit_reply_markup(reply_markup=num_epochs_kb)


# image size
@dp.callback_query_handler(lambda c: c.data == 'imsize')
async def set_num_epochs(callback_query):
    await bot.answer_callback_query(callback_query.id)

    if photo_buffer[callback_query.from_user.id].st_type in ['horse2zebra', 'vangogh', 'monet']:
        await callback_query.message.edit_text(
            "Текущие настройки:" + 
            "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
            " пикселей\n\nВыбери размер изображения:")

    else:
        await callback_query.message.edit_text(
            "Текущие настройки:" + 
            "\nКоличество эпох: " + str(photo_buffer[callback_query.from_user.id].settings['num_epochs']) +
            "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
            " пикселей\n\nВыбери размер изображения:")

    await callback_query.message.edit_reply_markup(reply_markup=imsize_kb)


# load images
@dp.callback_query_handler(lambda c: c.data == 'next')
async def load_images(callback_query):
    if MODE == 'EASY':
        await bot.send_message(callback_query.from_user.id, 
            "В данный момент бот работает в упрощенном режиме, для получения полного функционала бота " +
            "свяжитесь с создателем бота с целью перевести бота в нормальный режим работы. " + 
            "Пока можете ознакомится с меню или посетить страницу на github: " +
            "https://github.com/alresin/Style_transfer_telegram_bot")

        await bot.send_message(callback_query.from_user.id,
            "Что будем делать дальше?", reply_markup=start_kb)

        await callback_query.message.edit_reply_markup(reply_markup=cancel_kb)
            
        del photo_buffer[callback_query.from_user.id]


    elif MODE == 'NORMAL':
        if photo_buffer[callback_query.from_user.id].st_type == 1:
            await callback_query.message.edit_text(
                "Пришли мне картинку, стиль с которой нужно перенeсти. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 2

        elif photo_buffer[callback_query.from_user.id].st_type == 2:
            await callback_query.message.edit_text(
                "Пришли мне картинку, стиль с которой нужно перенeсти на левую часть изображения. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 3

        elif photo_buffer[callback_query.from_user.id].st_type == 'horse2zebra':
            await callback_query.message.edit_text(
                "Пришли мне фотографию лошади, и я перекрашу ее в зебру. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 1

        elif photo_buffer[callback_query.from_user.id].st_type == 'vangogh':
            await callback_query.message.edit_text(
                "Пришли мне фотографию, и я добавлю на нее стиль Ван Гога. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 1

        elif photo_buffer[callback_query.from_user.id].st_type == 'monet':
            await callback_query.message.edit_text(
                "Пришли мне фотографию, и я добавлю на нее стиль Моне. " +
                "Очень настоятельно рекомендую для хорошего качества присылать изображение как документ.")

            photo_buffer[callback_query.from_user.id].need_photos = 1
        
        await callback_query.message.edit_reply_markup(reply_markup=cancel_kb)


# changing epochs number
@dp.callback_query_handler(lambda c: c.data[:11] == 'num_epochs_')
async def change_num_epochs(callback_query):
    await bot.answer_callback_query(callback_query.id)
    photo_buffer[callback_query.from_user.id].settings['num_epochs'] = int(callback_query.data[11:])

    await callback_query.message.edit_text(
        "Текущие настройки:" + 
        "\nКоличество эпох: " + str(photo_buffer[callback_query.from_user.id].settings['num_epochs']) +
        "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
        " пикселей\n\nВыбери настройки для изменения:")
    await callback_query.message.edit_reply_markup(reply_markup=settings2_st_kb)


# changing image size
@dp.callback_query_handler(lambda c: c.data[:7] == 'imsize_')
async def change_imsize(callback_query):
    await bot.answer_callback_query(callback_query.id)
    photo_buffer[callback_query.from_user.id].settings['imsize'] = int(callback_query.data[7:])

    if photo_buffer[callback_query.from_user.id].st_type in ['horse2zebra', 'vangogh', 'monet']:
        await callback_query.message.edit_text(
            "Текущие настройки:" + 
            "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
            " пикселей\n\nВыбери настройки для изменения:")
        await callback_query.message.edit_reply_markup(reply_markup=settings2_gan_kb)

    else:
        await callback_query.message.edit_text(
            "Текущие настройки:" + 
            "\nКоличество эпох: " + str(photo_buffer[callback_query.from_user.id].settings['num_epochs']) +
            "\nРазмер изображения: " + str(photo_buffer[callback_query.from_user.id].settings['imsize']) +
            " пикселей\n\nВыбери настройки для изменения:")
        await callback_query.message.edit_reply_markup(reply_markup=settings2_st_kb)


# getting image
@dp.message_handler(content_types=['photo', 'document'])
async def get_image(message):
    if MODE == 'EASY':
        await bot.send_message(message.chat.id, 
            "В данный момент бот работает в упрощенном режиме, для получения полного функционала бота " +
            "свяжитесь с создателем бота с целью перевести бота в нормальный режим работы. " + 
            "Пока можете ознакомится с меню или посетить страницу на github: " +
            "https://github.com/alresin/Style_transfer_telegram_bot")

        await bot.send_message(message.chat.id,
            "Что будем делать дальше?", reply_markup=start_kb)
            
        if message.chat.id in photo_buffer:
            del photo_buffer[message.chat.id]


    elif MODE == 'NORMAL':
        if message.content_type == 'photo':
            img = message.photo[-1]

        else:
            img = message.document
            if img.mime_type[:5] != 'image':
                await bot.send_message(message.chat.id,
                    "Загрузи, пожалуйста, файл в формате изображения.",
                    reply_markup=start_kb)
                return

        file_info = await bot.get_file(img.file_id)
        photo = await bot.download_file(file_info.file_path)

        if message.chat.id not in photo_buffer:
            await bot.send_message(message.chat.id,
                "Сначала выбери тип style transef`a.", reply_markup=start_kb)
            return

        if not hasattr(photo_buffer[message.chat.id], 'need_photos' ):
            await bot.send_message(message.chat.id,
                "Сначала выбери настройки style transef`a.", reply_markup=settings1_kb)
            return

        photo_buffer[message.chat.id].photos.append(photo)

        # single style transfer
        if photo_buffer[message.chat.id].st_type == 1:
            if photo_buffer[message.chat.id].need_photos == 2:
                photo_buffer[message.chat.id].need_photos = 1

                await bot.send_message(message.chat.id,
                    "Отлично, теперь пришли мне картинку, на которую нужно перенести этот стиль. " +
                    "Для лучшего качества изображения лучше загружать как документ.",
                    reply_markup=cancel_kb)

            elif photo_buffer[message.chat.id].need_photos == 1:
                await bot.send_message(message.chat.id, "Начинаю обрабатывать...")

                # for debug
                log(photo_buffer[message.chat.id])

                try:
                    output = await style_transfer(Simple_style_transfer, photo_buffer[message.chat.id],
                        *photo_buffer[message.chat.id].photos)

                    await bot.send_document(message.chat.id, deepcopy(output))
                    await bot.send_photo(message.chat.id, output)

                except RuntimeError as err:
                    if str(err)[:19] == 'CUDA out of memory.':
                        await bot.send_message(message.chat.id,
                            "Произошла ошибка. У меня не хватает памяти, чтобы осуществить это действие. " +
                            "Чтобы избежать этого попробуй уменьшить размер изображения или количество эпох " +
                            "в расширенных настройках.")
                        
                    else:
                        if GET_DEBUG_INFO:
                            await bot.send_message(DEBUG_ID, "Произошла ошибка: " + str(err))
                            await bot.send_message(message.chat.id,
                                "Произошла ошибка. Сообщение об ошибке отправлено создателю бота.")

                        else:
                            await bot.send_message(message.chat.id,
                                    "Произошла ошибка.")

                except Exception as err:
                    if GET_DEBUG_INFO:
                        await bot.send_message(message.chat.id,
                                "Произошла ошибка. Сообщение об ошибке отправлено создателю бота.")
                        await bot.send_message(DEBUG_ID, "Произошла ошибка: " + str(err))

                    else:
                        await bot.send_message(message.chat.id,
                                "Произошла ошибка.")

                await bot.send_message(message.chat.id,
                    "Что будем делать дальше?", reply_markup=start_kb)
            
                del photo_buffer[message.chat.id]

        # double style transfer
        elif photo_buffer[message.chat.id].st_type == 2:
            if photo_buffer[message.chat.id].need_photos == 3:
                photo_buffer[message.chat.id].need_photos = 2

                await bot.send_message(message.chat.id,
                    "Отлично, теперь пришли мне картинку, стиль с которой " + 
                    "нужно перенести на правую часть изображения. " +
                    "Для лучшего качества изображения лучше загружать как документ.",
                    reply_markup=cancel_kb)
        
            elif photo_buffer[message.chat.id].need_photos == 2:
                photo_buffer[message.chat.id].need_photos = 1

                await bot.send_message(message.chat.id,
                    "Отлично, теперь пришли мне картинку, на которую нужно перенести эти стили. " +
                    "Для лучшего качества изображения лучше загружать как документ.",
                    reply_markup=cancel_kb)

            elif photo_buffer[message.chat.id].need_photos == 1:
                await bot.send_message(message.chat.id, "Начинаю обрабатывать...")

                # for debug
                log(photo_buffer[message.chat.id])

                try:
                    output = await style_transfer(Double_style_transfer, photo_buffer[message.chat.id],
                                                *photo_buffer[message.chat.id].photos)

                    await bot.send_document(message.chat.id, deepcopy(output))
                    await bot.send_photo(message.chat.id, output)

                except RuntimeError as err:
                    if str(err)[:19] == 'CUDA out of memory.':
                        await bot.send_message(message.chat.id,
                            "Произошла ошибка. У меня не хватает памяти, чтобы осуществить это действие. " +
                            "Чтобы избежать этого попробуй уменьшить размер изображения или количество эпох " +
                            "в расширенных настройках.")

                    else:
                        if GET_DEBUG_INFO:
                            await bot.send_message(DEBUG_ID, "Произошла ошибка: " + str(err))
                            await bot.send_message(message.chat.id,
                                "Произошла ошибка. Сообщение об ошибке отправлено создателю бота.")

                        else:
                            await bot.send_message(message.chat.id,
                                    "Произошла ошибка.")

                except Exception as err:
                    if GET_DEBUG_INFO:
                        await bot.send_message(DEBUG_ID, "Произошла ошибка: " + str(err))
                        await bot.send_message(message.chat.id,
                                "Произошла ошибка. Сообщение об ошибке отправлено создателю бота.")

                    else:
                        await bot.send_message(message.chat.id,
                                "Произошла ошибка.")


                await bot.send_message(message.chat.id,
                    "Что будем делать дальше?", reply_markup=start_kb)

                del photo_buffer[message.chat.id]

        # GAN horse2zebra or vangogh or monet
        elif photo_buffer[message.chat.id].st_type in ['horse2zebra', 'vangogh', 'monet'] and \
            photo_buffer[message.chat.id].need_photos == 1:
            await bot.send_message(message.chat.id, "Начинаю обрабатывать...")

            # for debug
            log(photo_buffer[message.chat.id])

            output = gan_transfer(photo_buffer[message.chat.id],
                                        photo_buffer[message.chat.id].photos[0])

            await bot.send_document(message.chat.id, deepcopy(output))
            await bot.send_photo(message.chat.id, output)

            '''
            try:
                
                
            except RuntimeError as err:
                    if str(err)[:19] == 'CUDA out of memory.':
                        await bot.send_message(message.chat.id,
                            "Произошла ошибка. У меня не хватает памяти, чтобы осуществить это действие. " +
                            "Чтобы избежать этого попробуй уменьшить размер изображения " +
                            "в расширенных настройках.")
                        
                    else:
                        if GET_DEBUG_INFO:
                            await bot.send_message(DEBUG_ID, "Произошла ошибка: " + str(err))
                            await bot.send_message(message.chat.id,
                                "Произошла ошибка. Сообщение об ошибке отправлено создателю бота.")

                        else:
                            await bot.send_message(message.chat.id,
                                    "Произошла ошибка.")

            except Exception as err:
                await bot.send_message(message.chat.id,
                            "Произошла ошибка. Сообщение об ошибке отправлено создателю бота.")

                if GET_DEBUG_INFO:
                    await bot.send_message(DEBUG_ID, "Произошла ошибка: " + str(err))
            '''


            await bot.send_message(message.chat.id,
                    "Что будем делать дальше?", reply_markup=start_kb)

            del photo_buffer[message.chat.id]


# text error
@dp.message_handler(content_types=['text'])
async def get_text(message):
    
    # for debug
    '''
    for i in photo_buffer:
        print(photo_buffer[i].st_type)
        print(photo_buffer[i].need_photos)
        print()
    '''

    await bot.send_message(message.chat.id,
        "Я тебя не понимаю. Вот что я могу:", reply_markup=start_kb)


async def on_startup(dispatcher):
    logging.warning('Starting...')

    await bot.set_webhook(webhook_url)


async def on_shutdown(dispatcher):
    logging.warning('Shutting down...')
    logging.warning('Bye!')


########################################################
# STYLE TRANSFER PART


async def style_transfer(st_class, user,*imgs):
    st = st_class(*imgs,
            imsize = user.settings['imsize'],
            num_steps = user.settings['num_epochs'],
            style_weight=100000, content_weight=1)

    output = await st.transfer()

    return tensor2img(output)
    

def gan_transfer(user, img):
    output = transfer(img,
            style = user.st_type,
            imsize = user.settings['imsize'],
            logging = LOGGING_GAN)

    return tensor2img(output.add(1).div(2))


def tensor2img(t):
    output = np.rollaxis(t.cpu().detach().numpy()[0], 0, 3)
    output = Image.fromarray(np.uint8(output * 255))

    bio = BytesIO()
    bio.name = 'result.jpeg'
    output.save(bio, 'JPEG')
    bio.seek(0)

    return bio


def log(user):
    if LOGGING:
        print()
        print('type:', user.st_type)
        if user.st_type == 1 or user.st_type == 2:
            print('settings:', user.settings)
            print('Epochs:')
        else:
            print('settings: imsize:', user.settings['imsize'])


def draw_img(img):
    plt.imshow(np.rollaxis(img.cpu().detach()[0].numpy(), 0, 3))
    plt.show()


def draw_photo(*photos):
    for photo in photos:
        img = np.array(Image.open(photo))
        plt.imshow(img)
        plt.show()


if __name__ == '__main__':
    if CONNECTION_TYPE == 'POLLING':
        executor.start_polling(dp, skip_updates=True)

    elif CONNECTION_TYPE == 'WEBHOOKS':
        # webhook setting
        webhook_path = f'/webhook/{API_TOKEN}'
        webhook_url  = urljoin(WEBHOOK_HOST, webhook_path)

        # webserver setting
        webapp_host = '0.0.0.0'
        webapp_port = int(os.environ.get('PORT', WEBAPP_PORT))

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=webhook_path,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=webapp_host,
            port=webapp_port)

    else:
        print("Invalid 'CONNECTION_TYPE'")