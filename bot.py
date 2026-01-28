import logging
import json
import os
import random
import string
import asyncio
import aiohttp
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ChatMemberHandler
)
from telegram.constants import ParseMode
import telegram

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8278172960:AAG5qBjn_-60D31T_FPG_O7DI-iHwnYWUDk"
ADMIN_IDS = [1499855064]
CHANNEL_ID = -1003666602450
CHANNEL_USERNAME = "@MineEvoUltra"
CHAT_ID = -1003607029419
CHAT_USERNAME = "@MineEvoUltraChat"
BOT_USERNAME = "@MineEvoUltra_bot"
SUPPORT_USERNAME = "@HomsyAdmin"

# Файлы для хранения данных
DATA_FILE = 'mining_data.json'
PROMOCODES_FILE = 'mining_promocodes.json'
LOG_FILE = 'mining_transactions.log'
SUPPORT_FILE = 'support_tickets.json'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ ДАННЫХ ==========
def load_data():
    """Загрузка данных из файлов"""
    data = {'users': {}, 'promocodes': {}, 'support_tickets': {}, 'events': {}}
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data['users'] = json.load(f)
    
    if os.path.exists(PROMOCODES_FILE):
        with open(PROMOCODES_FILE, 'r', encoding='utf-8') as f:
            data['promocodes'] = json.load(f)
    
    if os.path.exists(SUPPORT_FILE):
        with open(SUPPORT_FILE, 'r', encoding='utf-8') as f:
            data['support_tickets'] = json.load(f)
    
    # Ивенты по умолчанию
    if not data.get('events'):
        data['events'] = {
            'current_event': {
                'name': 'Летний майнинг',
                'description': 'Увеличенный доход от майнинга на 20%',
                'bonus_percent': 20,
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(days=30)).isoformat(),
                'active': True
            },
            'next_event': {
                'name': 'Хэллоуин Хоррор',
                'description': 'Шанс найти редкие видеокарты призраков',
                'start_date': (datetime.now() + timedelta(days=31)).isoformat(),
                'end_date': (datetime.now() + timedelta(days=60)).isoformat(),
                'active': False
            },
            'future_events': [
                {
                    'name': 'Киберпонедельник',
                    'description': 'Скидки на все видеокарты 50%',
                    'start_date': (datetime.now() + timedelta(days=61)).isoformat(),
                    'end_date': (datetime.now() + timedelta(days=90)).isoformat()
                }
            ]
        }
    
    return data

def save_data():
    """Сохранение данных в файлы"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)
    
    with open(PROMOCODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(promocodes, f, indent=2, ensure_ascii=False)
    
    with open(SUPPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(support_tickets, f, indent=2, ensure_ascii=False)

def log_transaction(user_id, username, action, amount, details=""):
    """Логирование транзакций"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | UserID: {user_id} | Username: @{username} | Action: {action} | Amount: {amount} | Details: {details}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    logger.info(log_entry.strip())

# Загрузка данных
data = load_data()
user_data = data['users']
promocodes = data['promocodes']
support_tickets = data.get('support_tickets', {})
events_data = data.get('events', {})

# Словарь для хранения состояний пользователей
user_states = {}
muted_users = {}  # Словарь для замученных пользователей: {user_id: unmute_time}

# ========== ГЕНЕРАЦИЯ ВИДЕОКАРТ (100 на каждую категорию) ==========
GPUS = {}

# Самые слабые (Tier 1) - 100 карт
weak_gpus = [
    ('🟢 NVIDIA GeForce 210', 1, 19, 5, 60, '🟢'),
    ('🟢 ATI Radeon HD 4350', 2, 18, 7, 62, '🟢'),
    ('🟢 NVIDIA GeForce 310', 2, 20, 8, 61, '🟢'),
    ('🟢 Intel HD Graphics', 3, 15, 10, 58, '🟢'),
    ('🟢 ATI Radeon HD 5450', 3, 19, 12, 63, '🟢'),
    ('🟢 NVIDIA GeForce GT 220', 4, 58, 15, 65, '🟢'),
    ('🟢 ATI Radeon HD 6450', 4, 18, 18, 60, '🟢'),
    ('🟢 NVIDIA GeForce GT 430', 5, 49, 20, 66, '🟢'),
    ('🟢 ATI Radeon HD 7470', 5, 20, 22, 62, '🟢'),
    ('🟢 NVIDIA GeForce GT 520', 6, 29, 25, 64, '🟢'),
    ('🟢 ATI Radeon HD 8350', 6, 35, 28, 63, '🟢'),
    ('🟢 NVIDIA GeForce GT 610', 7, 29, 30, 65, '🟢'),
    ('🟢 ATI Radeon HD 8470', 7, 35, 32, 64, '🟢'),
    ('🟢 Intel HD Graphics 2000', 8, 35, 35, 59, '🟢'),
    ('🟢 NVIDIA GeForce GT 620', 8, 49, 38, 66, '🟢'),
    ('🟢 ATI Radeon HD 8570', 9, 50, 40, 65, '🟢'),
    ('🟢 Intel HD Graphics 2500', 9, 35, 42, 60, '🟢'),
    ('🟢 NVIDIA GeForce GT 630', 10, 49, 45, 67, '🟢'),
    ('🟢 ATI Radeon HD 8670', 10, 55, 48, 66, '🟢'),
    ('🟢 Intel HD Graphics 3000', 11, 35, 50, 61, '🟢'),
    ('🟢 NVIDIA GeForce GT 640', 11, 49, 52, 68, '🟢'),
    ('🟢 ATI Radeon HD 8770', 12, 80, 55, 67, '🟢'),
    ('🟢 Intel HD Graphics 4000', 12, 35, 58, 62, '🟢'),
    ('🟢 NVIDIA GeForce GT 730', 13, 49, 60, 69, '🟢'),
    ('🟢 AMD Radeon R5 230', 13, 19, 62, 63, '🟢'),
    ('🟢 Intel HD Graphics 4200', 14, 15, 65, 63, '🟢'),
    ('🟢 NVIDIA GeForce GT 740', 14, 64, 68, 70, '🟢'),
    ('🟢 AMD Radeon R5 235', 15, 30, 70, 64, '🟢'),
    ('🟢 Intel HD Graphics 4400', 15, 15, 72, 64, '🟢'),
    ('🟢 NVIDIA GeForce GT 1030', 16, 30, 75, 71, '🟢'),
    ('🟢 AMD Radeon R5 240', 16, 50, 78, 65, '🟢'),
    ('🟢 Intel HD Graphics 4600', 17, 20, 80, 65, '🟢'),
    ('🟢 NVIDIA GeForce GTX 650', 17, 64, 82, 72, '🟢'),
    ('🟢 AMD Radeon R7 240', 18, 30, 85, 66, '🟢'),
    ('🟢 Intel HD Graphics 5000', 18, 15, 88, 66, '🟢'),
    ('🟢 NVIDIA GeForce GTX 750', 19, 55, 90, 73, '🟢'),
    ('🟢 AMD Radeon R7 250', 19, 50, 92, 67, '🟢'),
    ('🟢 Intel HD Graphics 5100', 20, 15, 95, 67, '🟢'),
    ('🟢 NVIDIA GeForce GTX 750 Ti', 21, 60, 98, 74, '🟢'),
    ('🟢 AMD Radeon R7 250X', 21, 55, 100, 68, '🟢'),
    ('🟢 Intel HD Graphics 5200', 22, 15, 102, 68, '🟢'),
    ('🟢 NVIDIA GeForce GTX 760', 23, 170, 105, 75, '🟢'),
    ('🟢 AMD Radeon R7 260', 23, 95, 108, 69, '🟢'),
    ('🟢 Intel HD Graphics 5300', 24, 15, 110, 69, '🟢'),
    ('🟢 NVIDIA GeForce GTX 770', 25, 230, 115, 76, '🟢'),
    ('🟢 AMD Radeon R7 260X', 25, 115, 118, 70, '🟢'),
    ('🟢 Intel HD Graphics 5500', 26, 15, 120, 70, '🟢'),
    ('🟢 NVIDIA GeForce GTX 780', 27, 250, 125, 77, '🟢'),
    ('🟢 AMD Radeon R9 270', 27, 150, 128, 71, '🟢'),
    ('🟢 Intel HD Graphics 5600', 28, 15, 130, 71, '🟢'),
    ('🟢 NVIDIA GeForce GTX 780 Ti', 29, 250, 135, 78, '🟢'),
    ('🟢 AMD Radeon R9 270X', 29, 180, 138, 72, '🟢'),
    ('🟢 Intel HD Graphics 6000', 30, 15, 140, 72, '🟢'),
    ('🟢 NVIDIA GeForce GTX 950', 31, 90, 145, 79, '🟢'),
    ('🟢 AMD Radeon R9 280', 31, 200, 148, 73, '🟢'),
    ('🟢 Intel HD Graphics 6100', 32, 15, 150, 73, '🟢'),
    ('🟢 NVIDIA GeForce GTX 960', 33, 120, 155, 80, '🟢'),
    ('🟢 AMD Radeon R9 280X', 33, 250, 158, 74, '🟢'),
    ('🟢 Intel HD Graphics 6200', 34, 15, 160, 74, '🟢'),
    ('🟢 NVIDIA GeForce GTX 970', 35, 145, 165, 81, '🟢'),
    ('🟢 AMD Radeon R9 285', 35, 190, 168, 75, '🟢'),
    ('🟢 Intel HD Graphics 6300', 36, 15, 170, 75, '🟢'),
    ('🟢 NVIDIA GeForce GTX 980', 37, 165, 175, 82, '🟢'),
    ('🟢 AMD Radeon R9 290', 37, 275, 178, 76, '🟢'),
    ('🟢 Intel HD Graphics 6400', 38, 15, 180, 76, '🟢'),
    ('🟢 NVIDIA GeForce GTX 980 Ti', 39, 250, 185, 83, '🟢'),
    ('🟢 AMD Radeon R9 290X', 39, 300, 188, 77, '🟢'),
    ('🟢 Intel HD Graphics 6500', 40, 15, 190, 77, '🟢'),
    ('🟢 NVIDIA GeForce GTX Titan', 41, 250, 195, 84, '🟢'),
    ('🟢 AMD Radeon R9 295X2', 41, 500, 198, 78, '🟢'),
    ('🟢 Intel HD Graphics 6600', 42, 15, 200, 78, '🟢'),
    ('🟢 NVIDIA GeForce GTX Titan X', 43, 250, 205, 85, '🟢'),
    ('🟢 AMD Radeon R9 Fury', 43, 275, 208, 79, '🟢'),
    ('🟢 Intel HD Graphics 6700', 44, 15, 210, 79, '🟢'),
    ('🟢 NVIDIA GeForce GTX Titan Z', 45, 375, 215, 86, '🟢'),
    ('🟢 AMD Radeon R9 Fury X', 45, 275, 218, 80, '🟢'),
    ('🟢 Intel HD Graphics 6800', 46, 15, 220, 80, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1050', 47, 75, 225, 87, '🟢'),
    ('🟢 AMD Radeon RX 460', 47, 75, 228, 81, '🟢'),
    ('🟢 Intel HD Graphics 6900', 48, 15, 230, 81, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1050 Ti', 49, 75, 235, 88, '🟢'),
    ('🟢 AMD Radeon RX 470', 49, 120, 238, 82, '🟢'),
    ('🟢 Intel HD Graphics 7000', 50, 15, 240, 82, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1060 3GB', 51, 120, 245, 89, '🟢'),
    ('🟢 AMD Radeon RX 480', 51, 150, 248, 83, '🟢'),
    ('🟢 Intel HD Graphics 7100', 52, 15, 250, 83, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1060 6GB', 53, 120, 255, 90, '🟢'),
    ('🟢 AMD Radeon RX 570', 53, 150, 258, 84, '🟢'),
    ('🟢 Intel HD Graphics 7200', 54, 15, 260, 84, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1070', 55, 150, 265, 91, '🟢'),
    ('🟢 AMD Radeon RX 580', 55, 185, 268, 85, '🟢'),
    ('🟢 Intel HD Graphics 7300', 56, 15, 270, 85, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1070 Ti', 57, 180, 275, 92, '🟢'),
    ('🟢 AMD Radeon RX 590', 57, 225, 278, 86, '🟢'),
    ('🟢 Intel HD Graphics 7400', 58, 15, 280, 86, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1080', 59, 180, 285, 93, '🟢'),
    ('🟢 AMD Radeon RX Vega 56', 59, 210, 288, 87, '🟢'),
    ('🟢 Intel HD Graphics 7500', 60, 15, 290, 87, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1080 Ti', 61, 250, 295, 94, '🟢'),
    ('🟢 AMD Radeon RX Vega 64', 61, 295, 298, 88, '🟢'),
    ('🟢 Intel HD Graphics 7600', 62, 15, 300, 88, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1650', 63, 75, 305, 89, '🟢'),
    ('🟢 AMD Radeon RX 5500 XT', 64, 130, 310, 90, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1650 Super', 65, 100, 315, 91, '🟢'),
    ('🟢 AMD Radeon RX 5600 XT', 66, 150, 320, 92, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1660', 67, 120, 325, 93, '🟢'),
    ('🟢 AMD Radeon RX 5700', 68, 180, 330, 94, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1660 Super', 69, 125, 335, 95, '🟢'),
    ('🟢 AMD Radeon RX 5700 XT', 70, 225, 340, 96, '🟢'),
    ('🟢 NVIDIA GeForce GTX 1660 Ti', 71, 120, 345, 97, '🟢'),
    ('🟢 AMD Radeon RX 6600', 72, 132, 350, 98, '🟢'),
    ('🟢 NVIDIA GeForce RTX 2060', 73, 160, 355, 99, '🟢'),
    ('🟢 AMD Radeon RX 6600 XT', 74, 160, 360, 100, '🟢'),
    ('🟢 NVIDIA GeForce RTX 2060 Super', 75, 175, 365, 101, '🟢'),
    ('🟢 AMD Radeon RX 6700 XT', 76, 230, 370, 102, '🟢'),
    ('🟢 NVIDIA GeForce RTX 2070', 77, 175, 375, 103, '🟢'),
    ('🟢 AMD Radeon RX 6800', 78, 250, 380, 104, '🟢'),
    ('🟢 NVIDIA GeForce RTX 2070 Super', 79, 215, 385, 105, '🟢'),
    ('🟢 AMD Radeon RX 6800 XT', 80, 300, 390, 106, '🟢'),
    ('🟢 NVIDIA GeForce RTX 2080', 81, 215, 395, 107, '🟢'),
    ('🟢 AMD Radeon RX 6900 XT', 82, 300, 400, 108, '🟢'),
    ('🟢 NVIDIA GeForce RTX 2080 Super', 83, 250, 405, 109, '🟢'),
    ('🟢 AMD Radeon RX 6950 XT', 84, 335, 410, 110, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3060', 85, 170, 415, 111, '🟢'),
    ('🟢 AMD Radeon RX 7600', 86, 165, 420, 112, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3060 Ti', 87, 200, 425, 113, '🟢'),
    ('🟢 AMD Radeon RX 7700 XT', 88, 245, 430, 114, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3070', 89, 220, 435, 115, '🟢'),
    ('🟢 AMD Radeon RX 7800 XT', 90, 263, 440, 116, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3070 Ti', 91, 290, 445, 117, '🟢'),
    ('🟢 AMD Radeon RX 7900 GRE', 92, 260, 450, 118, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3080', 93, 320, 455, 119, '🟢'),
    ('🟢 AMD Radeon RX 7900 XT', 94, 315, 460, 120, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3080 Ti', 95, 350, 465, 121, '🟢'),
    ('🟢 AMD Radeon RX 7900 XTX', 96, 355, 470, 122, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3090', 97, 350, 475, 123, '🟢'),
    ('🟢 AMD Radeon PRO W7900', 98, 295, 480, 124, '🟢'),
    ('🟢 NVIDIA GeForce RTX 3090 Ti', 99, 450, 485, 125, '🟢'),
    ('🟢 AMD Radeon RX 7950 X3D', 100, 120, 490, 126, '🟢')
]

# Бюджетные (Tier 2) - 100 карт
budget_gpus = [
    ('📱 NVIDIA GeForce RTX 4070', 96, 200, 495, 127, '📱'),
    ('📱 AMD Radeon RX 8000', 98, 280, 500, 128, '📱'),
    ('📱 NVIDIA GeForce RTX 4070 Super', 100, 220, 505, 129, '📱'),
    ('📱 AMD Radeon RX 8000 XT', 102, 320, 510, 130, '📱'),
    ('📱 NVIDIA GeForce RTX 4070 Ti', 104, 285, 515, 131, '📱'),
    ('📱 AMD Radeon RX 9000', 106, 350, 520, 132, '📱'),
    ('📱 NVIDIA GeForce RTX 4070 Ti Super', 108, 285, 525, 133, '📱'),
    ('📱 AMD Radeon RX 9000 XT', 110, 400, 530, 134, '📱'),
    ('📱 NVIDIA GeForce RTX 4080', 112, 320, 535, 135, '📱'),
    ('📱 AMD Radeon RX 10000', 114, 420, 540, 136, '📱'),
    ('📱 NVIDIA GeForce RTX 4080 Super', 116, 320, 545, 137, '📱'),
    ('📱 AMD Radeon RX 10000 XT', 118, 500, 550, 138, '📱'),
    ('📱 NVIDIA GeForce RTX 4090', 120, 450, 555, 139, '📱'),
    ('📱 AMD Radeon RX 11000', 122, 450, 560, 140, '📱'),
    ('📱 NVIDIA GeForce RTX 4090 D', 124, 425, 565, 141, '📱'),
    ('📱 AMD Radeon RX 11000 XT', 126, 550, 570, 142, '📱'),
    ('📱 NVIDIA GeForce RTX 5090', 128, 500, 575, 143, '📱'),
    ('📱 AMD Radeon RX 12000', 130, 600, 580, 144, '📱'),
    ('📱 NVIDIA TITAN RTX', 132, 280, 585, 145, '📱'),
    ('📱 AMD Radeon PRO WX 9100', 134, 230, 590, 146, '📱'),
    ('📱 NVIDIA RTX A6000', 136, 300, 595, 147, '📱'),
    ('📱 AMD Radeon Pro VII', 138, 250, 600, 148, '📱'),
    ('📱 NVIDIA A100 PCIe', 140, 400, 605, 149, '📱'),
    ('📱 AMD Instinct MI100', 142, 300, 610, 150, '📱'),
    ('📱 NVIDIA H100 PCIe', 144, 350, 615, 151, '📱'),
    ('📱 AMD Instinct MI250X', 146, 560, 620, 152, '📱'),
    ('📱 NVIDIA GH200', 148, 1000, 625, 153, '📱'),
    ('📱 AMD Instinct MI300X', 150, 750, 630, 154, '📱'),
    ('📱 NVIDIA B200', 152, 1200, 635, 155, '📱'),
    ('📱 AMD Instinct MI400X', 154, 800, 640, 156, '📱'),
    ('📱 Intel Arc A380', 156, 75, 645, 157, '📱'),
    ('📱 Intel Arc A580', 158, 175, 650, 158, '📱'),
    ('📱 Intel Arc A750', 160, 225, 655, 159, '📱'),
    ('📱 Intel Arc A770', 162, 225, 660, 160, '📱'),
    ('📱 Intel Arc B580', 164, 250, 665, 161, '📱'),
    ('📱 Intel Arc B750', 166, 300, 670, 162, '📱'),
    ('📱 Intel Arc B770', 168, 350, 675, 163, '📱'),
    ('📱 Intel Arc C580', 170, 400, 680, 164, '📱'),
    ('📱 Intel Arc C750', 172, 450, 685, 165, '📱'),
    ('📱 Intel Arc C770', 174, 500, 690, 166, '📱'),
    ('📱 Intel Battlemage A1', 176, 100, 695, 167, '📱'),
    ('📱 Intel Battlemage A2', 178, 150, 700, 168, '📱'),
    ('📱 Intel Battlemage A3', 180, 200, 705, 169, '📱'),
    ('📱 Intel Battlemage B1', 182, 250, 710, 170, '📱'),
    ('📱 Intel Battlemage B2', 184, 300, 715, 171, '📱'),
    ('📱 Intel Battlemage B3', 186, 350, 720, 172, '📱'),
    ('📱 Intel Battlemage C1', 188, 400, 725, 173, '📱'),
    ('📱 Intel Battlemage C2', 190, 450, 730, 174, '📱'),
    ('📱 Intel Battlemage C3', 192, 500, 735, 175, '📱'),
    ('📱 Intel Celestial A1', 194, 550, 740, 176, '📱'),
    ('📱 Intel Celestial A2', 196, 600, 745, 177, '📱'),
    ('📱 Intel Celestial A3', 198, 650, 750, 178, '📱'),
    ('📱 Intel Celestial B1', 200, 700, 755, 179, '📱'),
    ('📱 Intel Celestial B2', 202, 750, 760, 180, '📱'),
    ('📱 Intel Celestial B3', 204, 800, 765, 181, '📱'),
    ('📱 Intel Druid A1', 206, 850, 770, 182, '📱'),
    ('📱 Intel Druid A2', 208, 900, 775, 183, '📱'),
    ('📱 Intel Druid A3', 210, 950, 780, 184, '📱'),
    ('📱 NVIDIA Tesla V100', 212, 300, 785, 185, '📱'),
    ('📱 NVIDIA Tesla P100', 214, 300, 790, 186, '📱'),
    ('📱 NVIDIA Tesla K80', 216, 300, 795, 187, '📱'),
    ('📱 NVIDIA Quadro RTX 8000', 218, 295, 800, 188, '📱'),
    ('📱 NVIDIA Quadro RTX 6000', 220, 295, 805, 189, '📱'),
    ('📱 NVIDIA Quadro P6000', 222, 250, 810, 190, '📱'),
    ('📱 NVIDIA Quadro P5000', 224, 180, 815, 191, '📱'),
    ('📱 NVIDIA Quadro P4000', 226, 105, 820, 192, '📱'),
    ('📱 NVIDIA Quadro P2000', 228, 75, 825, 193, '📱'),
    ('📱 NVIDIA Quadro P1000', 230, 47, 830, 194, '📱'),
    ('📱 NVIDIA Quadro P620', 232, 40, 835, 195, '📱'),
    ('📱 NVIDIA Quadro P400', 234, 30, 840, 196, '📱'),
    ('📱 AMD Radeon Pro WX 7100', 236, 130, 845, 197, '📱'),
    ('📱 AMD Radeon Pro WX 5100', 238, 75, 850, 198, '📱'),
    ('📱 AMD Radeon Pro WX 4100', 240, 50, 855, 199, '📱'),
    ('📱 AMD Radeon Pro WX 3200', 242, 40, 860, 200, '📱'),
    ('📱 AMD Radeon Pro WX 2100', 244, 35, 865, 201, '📱'),
    ('📱 AMD Radeon Pro WX 1100', 246, 35, 870, 202, '📱'),
    ('📱 AMD Radeon Pro WX 9100', 248, 230, 875, 203, '📱'),
    ('📱 AMD Radeon Pro WX 8100', 250, 200, 880, 204, '📱'),
    ('📱 AMD Radeon Pro WX 7100', 252, 130, 885, 205, '📱'),
    ('📱 AMD Radeon Pro WX 5100', 254, 75, 890, 206, '📱'),
    ('📱 AMD Radeon Pro WX 4100', 256, 50, 895, 207, '📱'),
    ('📱 AMD Radeon Pro WX 3200', 258, 40, 900, 208, '📱'),
    ('📱 AMD Radeon Pro WX 2100', 260, 35, 905, 209, '📱'),
    ('📱 AMD Radeon Pro WX 1100', 262, 35, 910, 210, '📱'),
    ('📱 NVIDIA GeForce RTX 4060', 264, 115, 915, 211, '📱'),
    ('📱 NVIDIA GeForce RTX 4060 Ti', 266, 160, 920, 212, '📱'),
    ('📱 NVIDIA GeForce RTX 4070', 268, 200, 925, 213, '📱'),
    ('📱 NVIDIA GeForce RTX 4070 Ti', 270, 285, 930, 214, '📱'),
    ('📱 NVIDIA GeForce RTX 4080', 272, 320, 935, 215, '📱'),
    ('📱 NVIDIA GeForce RTX 4080 Super', 274, 320, 940, 216, '📱'),
    ('📱 NVIDIA GeForce RTX 4090', 276, 450, 945, 217, '📱'),
    ('📱 AMD Radeon RX 7700', 278, 200, 950, 218, '📱'),
    ('📱 AMD Radeon RX 7800', 280, 250, 955, 219, '📱'),
    ('📱 AMD Radeon RX 7900', 282, 300, 960, 220, '📱'),
    ('📱 AMD Radeon RX 7950', 284, 350, 965, 221, '📱'),
    ('📱 AMD Radeon RX 8000', 286, 400, 970, 222, '📱'),
    ('📱 AMD Radeon RX 8050', 288, 450, 975, 223, '📱'),
    ('📱 AMD Radeon RX 8100', 290, 500, 980, 224, '📱'),
    ('📱 AMD Radeon RX 8150', 292, 550, 985, 225, '📱'),
    ('📱 AMD Radeon RX 8200', 294, 600, 990, 226, '📱'),
    ('📱 AMD Radeon RX 8250', 296, 650, 995, 227, '📱'),
    ('📱 AMD Radeon RX 8300', 298, 700, 1000, 228, '📱')
]

# Средние (Tier 3) - 100 карт
medium_gpus = [
    ('⚡ NVIDIA GeForce RTX 3060 OC', 50, 170, 300, 70, '⚡'),
    ('⚡ AMD Radeon RX 6700 XT OC', 52, 230, 350, 72, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3060 Ti OC', 54, 200, 400, 71, '⚡'),
    ('⚡ AMD Radeon RX 6750 XT', 56, 250, 420, 73, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3070 OC', 58, 220, 450, 72, '⚡'),
    ('⚡ AMD Radeon RX 6800 OC', 60, 250, 480, 74, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3070 Ti OC', 62, 290, 520, 73, '⚡'),
    ('⚡ AMD Radeon RX 6800 XT OC', 64, 300, 550, 75, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3080 OC', 66, 320, 600, 74, '⚡'),
    ('⚡ AMD Radeon RX 6900 XT OC', 68, 300, 650, 76, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3080 Ti OC', 70, 350, 700, 75, '⚡'),
    ('⚡ AMD Radeon RX 6950 XT', 72, 335, 750, 77, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3090 OC', 74, 350, 800, 76, '⚡'),
    ('⚡ AMD Radeon RX 7900 XT', 76, 315, 850, 78, '⚡'),
    ('⚡ NVIDIA GeForce RTX 3090 Ti OC', 78, 450, 900, 77, '⚡'),
    ('⚡ AMD Radeon RX 7900 XTX', 80, 355, 950, 79, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4070 OC', 82, 200, 1000, 78, '⚡'),
    ('⚡ AMD Radeon RX 7950 X3D', 84, 120, 1050, 80, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4070 Ti OC', 86, 285, 1100, 79, '⚡'),
    ('⚡ AMD Radeon RX 8000 OC', 88, 280, 1150, 81, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4070 Ti Super OC', 90, 285, 1200, 80, '⚡'),
    ('⚡ AMD Radeon RX 8000 XT OC', 92, 320, 1250, 82, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4080 OC', 94, 320, 1300, 81, '⚡'),
    ('⚡ AMD Radeon RX 9000 OC', 96, 350, 1350, 83, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4080 Super OC', 98, 320, 1400, 82, '⚡'),
    ('⚡ AMD Radeon RX 9000 XT OC', 100, 400, 1450, 84, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4090 OC', 102, 450, 1500, 83, '⚡'),
    ('⚡ AMD Radeon RX 10000 OC', 104, 420, 1550, 85, '⚡'),
    ('⚡ NVIDIA GeForce RTX 4090 D OC', 106, 425, 1600, 84, '⚡'),
    ('⚡ AMD Radeon RX 10000 XT OC', 108, 500, 1650, 86, '⚡'),
    ('⚡ NVIDIA GeForce RTX 5090 OC', 110, 500, 1700, 85, '⚡'),
    ('⚡ AMD Radeon RX 11000 OC', 112, 450, 1750, 87, '⚡'),
    ('⚡ NVIDIA GeForce RTX 5090 Ti', 114, 550, 1800, 86, '⚡'),
    ('⚡ AMD Radeon RX 11000 XT OC', 116, 550, 1850, 88, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6060', 118, 150, 1900, 87, '⚡'),
    ('⚡ AMD Radeon RX 12000', 120, 500, 1950, 89, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6060 Ti', 122, 180, 2000, 88, '⚡'),
    ('⚡ AMD Radeon RX 12000 XT', 124, 550, 2050, 90, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6070', 126, 220, 2100, 89, '⚡'),
    ('⚡ AMD Radeon RX 13000', 128, 600, 2150, 91, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6070 Ti', 130, 250, 2200, 90, '⚡'),
    ('⚡ AMD Radeon RX 13000 XT', 132, 650, 2250, 92, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6080', 134, 300, 2300, 91, '⚡'),
    ('⚡ AMD Radeon RX 14000', 136, 700, 2350, 93, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6080 Ti', 138, 350, 2400, 92, '⚡'),
    ('⚡ AMD Radeon RX 14000 XT', 140, 750, 2450, 94, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6090', 142, 400, 2500, 93, '⚡'),
    ('⚡ AMD Radeon RX 15000', 144, 800, 2550, 95, '⚡'),
    ('⚡ NVIDIA GeForce RTX 6090 Ti', 146, 450, 2600, 94, '⚡'),
    ('⚡ AMD Radeon RX 15000 XT', 148, 850, 2650, 96, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7060', 150, 160, 2700, 95, '⚡'),
    ('⚡ AMD Radeon RX 16000', 152, 900, 2750, 97, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7060 Ti', 154, 190, 2800, 96, '⚡'),
    ('⚡ AMD Radeon RX 16000 XT', 156, 950, 2850, 98, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7070', 158, 230, 2900, 97, '⚡'),
    ('⚡ AMD Radeon RX 17000', 160, 1000, 2950, 99, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7070 Ti', 162, 270, 3000, 98, '⚡'),
    ('⚡ AMD Radeon RX 17000 XT', 164, 1050, 3050, 100, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7080', 166, 330, 3100, 99, '⚡'),
    ('⚡ AMD Radeon RX 18000', 168, 1100, 3150, 101, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7080 Ti', 170, 380, 3200, 100, '⚡'),
    ('⚡ AMD Radeon RX 18000 XT', 172, 1150, 3250, 102, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7090', 174, 430, 3300, 101, '⚡'),
    ('⚡ AMD Radeon RX 19000', 176, 1200, 3350, 103, '⚡'),
    ('⚡ NVIDIA GeForce RTX 7090 Ti', 178, 480, 3400, 102, '⚡'),
    ('⚡ AMD Radeon RX 19000 XT', 180, 1250, 3450, 104, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8060', 182, 170, 3500, 103, '⚡'),
    ('⚡ AMD Radeon RX 20000', 184, 1300, 3550, 105, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8060 Ti', 186, 200, 3600, 104, '⚡'),
    ('⚡ AMD Radeon RX 20000 XT', 188, 1350, 3650, 106, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8070', 190, 240, 3700, 105, '⚡'),
    ('⚡ AMD Radeon RX 21000', 192, 1400, 3750, 107, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8070 Ti', 194, 290, 3800, 106, '⚡'),
    ('⚡ AMD Radeon RX 21000 XT', 196, 1450, 3850, 108, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8080', 198, 340, 3900, 107, '⚡'),
    ('⚡ AMD Radeon RX 22000', 200, 1500, 3950, 109, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8080 Ti', 202, 390, 4000, 108, '⚡'),
    ('⚡ AMD Radeon RX 22000 XT', 204, 1550, 4050, 110, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8090', 206, 440, 4100, 109, '⚡'),
    ('⚡ AMD Radeon RX 23000', 208, 1600, 4150, 111, '⚡'),
    ('⚡ NVIDIA GeForce RTX 8090 Ti', 210, 490, 4200, 110, '⚡'),
    ('⚡ AMD Radeon RX 23000 XT', 212, 1650, 4250, 112, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9060', 214, 180, 4300, 111, '⚡'),
    ('⚡ AMD Radeon RX 24000', 216, 1700, 4350, 113, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9060 Ti', 218, 210, 4400, 112, '⚡'),
    ('⚡ AMD Radeon RX 24000 XT', 220, 1750, 4450, 114, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9070', 222, 250, 4500, 113, '⚡'),
    ('⚡ AMD Radeon RX 25000', 224, 1800, 4550, 115, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9070 Ti', 226, 310, 4600, 114, '⚡'),
    ('⚡ AMD Radeon RX 25000 XT', 228, 1850, 4650, 116, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9080', 230, 360, 4700, 115, '⚡'),
    ('⚡ AMD Radeon RX 26000', 232, 1900, 4750, 117, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9080 Ti', 234, 410, 4800, 116, '⚡'),
    ('⚡ AMD Radeon RX 26000 XT', 236, 1950, 4850, 118, '⚡'),
    ('⚡ NVIDIA GeForce RTX 9090', 238, 460, 4900, 117, '⚡'),
    ('⚡ AMD Radeon RX 27000', 240, 2000, 4950, 119, '⚡')
]

# Хорошие (Tier 4) - 100 карт
good_gpus = [
    ('💎 NVIDIA GeForce RTX 4080 Super FE', 120, 320, 1200, 80, '💎'),
    ('💎 AMD Radeon RX 7900 XTX OC', 122, 355, 1250, 82, '💎'),
    ('💎 NVIDIA GeForce RTX 4090 FE', 124, 450, 1300, 81, '💎'),
    ('💎 AMD Radeon RX 7950 X3D OC', 126, 120, 1350, 83, '💎'),
    ('💎 NVIDIA GeForce RTX 4090 D FE', 128, 425, 1400, 82, '💎'),
    ('💎 AMD Radeon RX 8000 FE', 130, 280, 1450, 84, '💎'),
    ('💎 NVIDIA GeForce RTX 5090 FE', 132, 500, 1500, 83, '💎'),
    ('💎 AMD Radeon RX 8000 XT FE', 134, 320, 1550, 85, '💎'),
    ('💎 NVIDIA GeForce RTX 5090 Ti', 136, 550, 1600, 84, '💎'),
    ('💎 AMD Radeon RX 9000 FE', 138, 350, 1650, 86, '💎'),
    ('💎 NVIDIA GeForce RTX 6060 FE', 140, 150, 1700, 85, '💎'),
    ('💎 AMD Radeon RX 9000 XT FE', 142, 400, 1750, 87, '💎'),
    ('💎 NVIDIA GeForce RTX 6060 Ti FE', 144, 180, 1800, 86, '💎'),
    ('💎 AMD Radeon RX 10000 FE', 146, 420, 1850, 88, '💎'),
    ('💎 NVIDIA GeForce RTX 6070 FE', 148, 220, 1900, 87, '💎'),
    ('💎 AMD Radeon RX 10000 XT FE', 150, 500, 1950, 89, '💎'),
    ('💎 NVIDIA GeForce RTX 6070 Ti FE', 152, 250, 2000, 88, '💎'),
    ('💎 AMD Radeon RX 11000 FE', 154, 450, 2050, 90, '💎'),
    ('💎 NVIDIA GeForce RTX 6080 FE', 156, 300, 2100, 89, '💎'),
    ('💎 AMD Radeon RX 11000 XT FE', 158, 550, 2150, 91, '💎'),
    ('💎 NVIDIA GeForce RTX 6080 Ti FE', 160, 350, 2200, 90, '💎'),
    ('💎 AMD Radeon RX 12000 FE', 162, 500, 2250, 92, '💎'),
    ('💎 NVIDIA GeForce RTX 6090 FE', 164, 400, 2300, 91, '💎'),
    ('💎 AMD Radeon RX 12000 XT FE', 166, 550, 2350, 93, '💎'),
    ('💎 NVIDIA GeForce RTX 6090 Ti FE', 168, 450, 2400, 92, '💎'),
    ('💎 AMD Radeon RX 13000 FE', 170, 600, 2450, 94, '💎'),
    ('💎 NVIDIA GeForce RTX 7060 FE', 172, 160, 2500, 93, '💎'),
    ('💎 AMD Radeon RX 13000 XT FE', 174, 650, 2550, 95, '💎'),
    ('💎 NVIDIA GeForce RTX 7060 Ti FE', 176, 190, 2600, 94, '💎'),
    ('💎 AMD Radeon RX 14000 FE', 178, 700, 2650, 96, '💎'),
    ('💎 NVIDIA GeForce RTX 7070 FE', 180, 230, 2700, 95, '💎'),
    ('💎 AMD Radeon RX 14000 XT FE', 182, 750, 2750, 97, '💎'),
    ('💎 NVIDIA GeForce RTX 7070 Ti FE', 184, 270, 2800, 96, '💎'),
    ('💎 AMD Radeon RX 15000 FE', 186, 800, 2850, 98, '💎'),
    ('💎 NVIDIA GeForce RTX 7080 FE', 188, 330, 2900, 97, '💎'),
    ('💎 AMD Radeon RX 15000 XT FE', 190, 850, 2950, 99, '💎'),
    ('💎 NVIDIA GeForce RTX 7080 Ti FE', 192, 380, 3000, 98, '💎'),
    ('💎 AMD Radeon RX 16000 FE', 194, 900, 3050, 100, '💎'),
    ('💎 NVIDIA GeForce RTX 7090 FE', 196, 430, 3100, 99, '💎'),
    ('💎 AMD Radeon RX 16000 XT FE', 198, 950, 3150, 101, '💎'),
    ('💎 NVIDIA GeForce RTX 7090 Ti FE', 200, 480, 3200, 100, '💎'),
    ('💎 AMD Radeon RX 17000 FE', 202, 1000, 3250, 102, '💎'),
    ('💎 NVIDIA GeForce RTX 8060 FE', 204, 170, 3300, 101, '💎'),
    ('💎 AMD Radeon RX 17000 XT FE', 206, 1050, 3350, 103, '💎'),
    ('💎 NVIDIA GeForce RTX 8060 Ti FE', 208, 200, 3400, 102, '💎'),
    ('💎 AMD Radeon RX 18000 FE', 210, 1100, 3450, 104, '💎'),
    ('💎 NVIDIA GeForce RTX 8070 FE', 212, 240, 3500, 103, '💎'),
    ('💎 AMD Radeon RX 18000 XT FE', 214, 1150, 3550, 105, '💎'),
    ('💎 NVIDIA GeForce RTX 8070 Ti FE', 216, 290, 3600, 104, '💎'),
    ('💎 AMD Radeon RX 19000 FE', 218, 1200, 3650, 106, '💎'),
    ('💎 NVIDIA GeForce RTX 8080 FE', 220, 340, 3700, 105, '💎'),
    ('💎 AMD Radeon RX 19000 XT FE', 222, 1250, 3750, 107, '💎'),
    ('💎 NVIDIA GeForce RTX 8080 Ti FE', 224, 390, 3800, 106, '💎'),
    ('💎 AMD Radeon RX 20000 FE', 226, 1300, 3850, 108, '💎'),
    ('💎 NVIDIA GeForce RTX 8090 FE', 228, 440, 3900, 107, '💎'),
    ('💎 AMD Radeon RX 20000 XT FE', 230, 1350, 3950, 109, '💎'),
    ('💎 NVIDIA GeForce RTX 8090 Ti FE', 232, 490, 4000, 108, '💎'),
    ('💎 AMD Radeon RX 21000 FE', 234, 1400, 4050, 110, '💎'),
    ('💎 NVIDIA GeForce RTX 9060 FE', 236, 180, 4100, 109, '💎'),
    ('💎 AMD Radeon RX 21000 XT FE', 238, 1450, 4150, 111, '💎'),
    ('💎 NVIDIA GeForce RTX 9060 Ti FE', 240, 210, 4200, 110, '💎'),
    ('💎 AMD Radeon RX 22000 FE', 242, 1500, 4250, 112, '💎'),
    ('💎 NVIDIA GeForce RTX 9070 FE', 244, 250, 4300, 111, '💎'),
    ('💎 AMD Radeon RX 22000 XT FE', 246, 1550, 4350, 113, '💎'),
    ('💎 NVIDIA GeForce RTX 9070 Ti FE', 248, 310, 4400, 112, '💎'),
    ('💎 AMD Radeon RX 23000 FE', 250, 1600, 4450, 114, '💎'),
    ('💎 NVIDIA GeForce RTX 9080 FE', 252, 360, 4500, 113, '💎'),
    ('💎 AMD Radeon RX 23000 XT FE', 254, 1650, 4550, 115, '💎'),
    ('💎 NVIDIA GeForce RTX 9080 Ti FE', 256, 410, 4600, 114, '💎'),
    ('💎 AMD Radeon RX 24000 FE', 258, 1700, 4650, 116, '💎'),
    ('💎 NVIDIA GeForce RTX 9090 FE', 260, 460, 4700, 115, '💎'),
    ('💎 AMD Radeon RX 24000 XT FE', 262, 1750, 4750, 117, '💎'),
    ('💎 NVIDIA GeForce RTX 10060 FE', 264, 190, 4800, 116, '💎'),
    ('💎 AMD Radeon RX 25000 FE', 266, 1800, 4850, 118, '💎'),
    ('💎 NVIDIA GeForce RTX 10060 Ti FE', 268, 220, 4900, 117, '💎'),
    ('💎 AMD Radeon RX 25000 XT FE', 270, 1850, 4950, 119, '💎'),
    ('💎 NVIDIA GeForce RTX 10070 FE', 272, 260, 5000, 118, '💎'),
    ('💎 AMD Radeon RX 26000 FE', 274, 1900, 5050, 120, '💎'),
    ('💎 NVIDIA GeForce RTX 10070 Ti FE', 276, 330, 5100, 119, '💎'),
    ('💎 AMD Radeon RX 26000 XT FE', 278, 1950, 5150, 121, '💎'),
    ('💎 NVIDIA GeForce RTX 10080 FE', 280, 370, 5200, 120, '💎'),
    ('💎 AMD Radeon RX 27000 FE', 282, 2000, 5250, 122, '💎'),
    ('💎 NVIDIA GeForce RTX 10080 Ti FE', 284, 420, 5300, 121, '💎'),
    ('💎 AMD Radeon RX 27000 XT FE', 286, 2050, 5350, 123, '💎'),
    ('💎 NVIDIA GeForce RTX 10090 FE', 288, 470, 5400, 122, '💎'),
    ('💎 AMD Radeon RX 28000 FE', 290, 2100, 5450, 124, '💎'),
    ('💎 NVIDIA GeForce RTX 10090 Ti FE', 292, 520, 5500, 123, '💎'),
    ('💎 AMD Radeon RX 28000 XT FE', 294, 2150, 5550, 125, '💎'),
    ('💎 NVIDIA GeForce RTX 11060 FE', 296, 200, 5600, 124, '💎'),
    ('💎 AMD Radeon RX 29000 FE', 298, 2200, 5650, 126, '💎')
]

# Мощные (Tier 5) - 100 карт
powerful_gpus = [
    ('🔥 NVIDIA TITAN RTX OC', 140, 280, 1200, 75, '🔥'),
    ('🔥 AMD Radeon Pro VII OC', 142, 250, 1250, 76, '🔥'),
    ('🔥 NVIDIA RTX A6000 OC', 144, 300, 1300, 74, '🔥'),
    ('🔥 AMD Radeon PRO W7900 OC', 146, 295, 1350, 77, '🔥'),
    ('🔥 NVIDIA A100 PCIe OC', 148, 400, 1400, 75, '🔥'),
    ('🔥 AMD Instinct MI100 OC', 150, 300, 1450, 78, '🔥'),
    ('🔥 NVIDIA H100 PCIe OC', 152, 350, 1500, 76, '🔥'),
    ('🔥 AMD Instinct MI250X OC', 154, 560, 1550, 79, '🔥'),
    ('🔥 NVIDIA GH200 OC', 156, 1000, 1600, 77, '🔥'),
    ('🔥 AMD Instinct MI300X OC', 158, 750, 1650, 80, '🔥'),
    ('🔥 NVIDIA B200 OC', 160, 1200, 1700, 78, '🔥'),
    ('🔥 AMD Instinct MI400X OC', 162, 800, 1750, 81, '🔥'),
    ('🔥 NVIDIA H200', 164, 700, 1800, 79, '🔥'),
    ('🔥 AMD Instinct MI500X', 166, 900, 1850, 82, '🔥'),
    ('🔥 NVIDIA GB200', 168, 1500, 1900, 80, '🔥'),
    ('🔥 AMD Instinct MI600X', 170, 1000, 1950, 83, '🔥'),
    ('🔥 NVIDIA Tesla V100S', 172, 250, 2000, 81, '🔥'),
    ('🔥 AMD Radeon Instinct MI8', 174, 180, 2050, 84, '🔥'),
    ('🔥 NVIDIA Tesla P40', 176, 250, 2100, 82, '🔥'),
    ('🔥 AMD Radeon Instinct MI25', 178, 300, 2150, 85, '🔥'),
    ('🔥 NVIDIA Tesla M60', 180, 300, 2200, 83, '🔥'),
    ('🔥 AMD Radeon Instinct MI6', 182, 150, 2250, 86, '🔥'),
    ('🔥 NVIDIA Tesla K40', 184, 235, 2300, 84, '🔥'),
    ('🔥 AMD Radeon Instinct MI60', 186, 300, 2350, 87, '🔥'),
    ('🔥 NVIDIA Tesla M40', 188, 250, 2400, 85, '🔥'),
    ('🔥 AMD Radeon Instinct MI50', 190, 300, 2450, 88, '🔥'),
    ('🔥 NVIDIA Tesla P100 NVLink', 192, 300, 2500, 86, '🔥'),
    ('🔥 AMD Radeon Instinct MI100', 194, 300, 2550, 89, '🔥'),
    ('🔥 NVIDIA Tesla V100 NVLink', 196, 300, 2600, 87, '🔥'),
    ('🔥 AMD Radeon Instinct MI250', 198, 560, 2650, 90, '🔥'),
    ('🔥 NVIDIA Tesla A100 NVLink', 200, 400, 2700, 88, '🔥'),
    ('🔥 AMD Radeon Instinct MI300', 202, 750, 2750, 91, '🔥'),
    ('🔥 NVIDIA Tesla H100 NVLink', 204, 350, 2800, 89, '🔥'),
    ('🔥 AMD Radeon Instinct MI400', 206, 800, 2850, 92, '🔥'),
    ('🔥 NVIDIA Tesla B200 NVLink', 208, 1200, 2900, 90, '🔥'),
    ('🔥 AMD Radeon Instinct MI500', 210, 900, 2950, 93, '🔥'),
    ('🔥 NVIDIA Quadro GV100', 212, 250, 3000, 91, '🔥'),
    ('🔥 AMD Radeon Pro WX 9100', 214, 230, 3050, 94, '🔥'),
    ('🔥 NVIDIA Quadro RTX 8000', 216, 295, 3100, 92, '🔥'),
    ('🔥 AMD Radeon Pro WX 8200', 218, 230, 3150, 95, '🔥'),
    ('🔥 NVIDIA Quadro RTX 6000', 220, 295, 3200, 93, '🔥'),
    ('🔥 AMD Radeon Pro WX 7100', 222, 130, 3250, 96, '🔥'),
    ('🔥 NVIDIA Quadro RTX 5000', 224, 265, 3300, 94, '🔥'),
    ('🔥 AMD Radeon Pro WX 5100', 226, 75, 3350, 97, '🔥'),
    ('🔥 NVIDIA Quadro RTX 4000', 228, 160, 3400, 95, '🔥'),
    ('🔥 AMD Radeon Pro WX 4100', 230, 50, 3450, 98, '🔥'),
    ('🔥 NVIDIA Quadro P6000', 232, 250, 3500, 96, '🔥'),
    ('🔥 AMD Radeon Pro WX 3200', 234, 40, 3550, 99, '🔥'),
    ('🔥 NVIDIA Quadro P5000', 236, 180, 3600, 97, '🔥'),
    ('🔥 AMD Radeon Pro WX 2100', 238, 35, 3650, 100, '🔥'),
    ('🔥 NVIDIA Quadro P4000', 240, 105, 3700, 98, '🔥'),
    ('🔥 AMD Radeon Pro WX 1100', 242, 35, 3750, 101, '🔥'),
    ('🔥 NVIDIA Quadro P2000', 244, 75, 3800, 99, '🔥'),
    ('🔥 AMD FirePro W9100', 246, 275, 3850, 102, '🔥'),
    ('🔥 NVIDIA Quadro P1000', 248, 47, 3900, 100, '🔥'),
    ('🔥 AMD FirePro W9000', 250, 274, 3950, 103, '🔥'),
    ('🔥 NVIDIA Quadro P620', 252, 40, 4000, 101, '🔥'),
    ('🔥 AMD FirePro W8100', 254, 220, 4050, 104, '🔥'),
    ('🔥 NVIDIA Quadro P400', 256, 30, 4100, 102, '🔥'),
    ('🔥 AMD FirePro W8000', 258, 150, 4150, 105, '🔥'),
    ('🔥 NVIDIA Quadro M6000', 260, 250, 4200, 103, '🔥'),
    ('🔥 AMD FirePro W7000', 262, 150, 4250, 106, '🔥'),
    ('🔥 NVIDIA Quadro M5000', 264, 150, 4300, 104, '🔥'),
    ('🔥 AMD FirePro W5100', 266, 75, 4350, 107, '🔥'),
    ('🔥 NVIDIA Quadro M4000', 268, 120, 4400, 105, '🔥'),
    ('🔥 AMD FirePro W5000', 270, 150, 4450, 108, '🔥'),
    ('🔥 NVIDIA Quadro M2000', 272, 75, 4500, 106, '🔥'),
    ('🔥 AMD FirePro W4100', 274, 50, 4550, 109, '🔥'),
    ('🔥 NVIDIA Quadro K6000', 276, 225, 4600, 107, '🔥'),
    ('🔥 AMD FirePro W2100', 278, 26, 4650, 110, '🔥'),
    ('🔥 NVIDIA Quadro K5200', 280, 150, 4700, 108, '🔥'),
    ('🔥 AMD FirePro W7000', 282, 150, 4750, 111, '🔥'),
    ('🔥 NVIDIA Quadro K5000', 284, 122, 4800, 109, '🔥'),
    ('🔥 AMD FirePro W5000', 286, 150, 4850, 112, '🔥'),
    ('🔥 NVIDIA Quadro K4200', 288, 107, 4900, 110, '🔥'),
    ('🔥 AMD FirePro W4100', 290, 50, 4950, 113, '🔥'),
    ('🔥 NVIDIA Quadro K4000', 292, 80, 5000, 111, '🔥'),
    ('🔥 AMD FirePro W2100', 294, 26, 5050, 114, '🔥'),
    ('🔥 NVIDIA Quadro K2000', 296, 51, 5100, 112, '🔥'),
    ('🔥 AMD FirePro V7900', 298, 150, 5150, 115, '🔥'),
    ('🔥 NVIDIA Quadro K2000D', 300, 51, 5200, 113, '🔥'),
    ('🔥 AMD FirePro V5900', 302, 75, 5250, 116, '🔥'),
    ('🔥 NVIDIA Quadro K1200', 304, 45, 5300, 114, '🔥'),
    ('🔥 AMD FirePro V4900', 306, 75, 5350, 117, '🔥'),
    ('🔥 NVIDIA Quadro K620', 308, 41, 5400, 115, '🔥'),
    ('🔥 AMD FirePro V3900', 310, 50, 5450, 118, '🔥'),
    ('🔥 NVIDIA Quadro K420', 312, 41, 5500, 116, '🔥'),
    ('🔥 AMD FirePro V3800', 314, 42, 5550, 119, '🔥'),
    ('🔥 NVIDIA Quadro K2200', 316, 68, 5600, 117, '🔥'),
    ('🔥 AMD FirePro V3750', 318, 36, 5650, 120, '🔥'),
    ('🔥 NVIDIA Quadro K2200M', 320, 55, 5700, 118, '🔥'),
    ('🔥 AMD FirePro V3700', 322, 26, 5750, 121, '🔥'),
    ('🔥 NVIDIA Quadro K2100M', 324, 55, 5800, 119, '🔥'),
    ('🔥 AMD FirePro V3600', 326, 26, 5850, 122, '🔥'),
    ('🔥 NVIDIA Quadro K1100M', 328, 45, 5900, 120, '🔥'),
    ('🔥 AMD FirePro V3500', 330, 26, 5950, 123, '🔥'),
    ('🔥 NVIDIA Quadro K1000M', 332, 45, 6000, 121, '🔥'),
    ('🔥 AMD FirePro V3400', 334, 26, 6050, 124, '🔥'),
    ('🔥 NVIDIA Quadro K610M', 336, 30, 6100, 122, '🔥'),
    ('🔥 AMD FirePro V3300', 338, 26, 6150, 125, '🔥'),
    ('🔥 NVIDIA Quadro K510M', 340, 30, 6200, 123, '🔥'),
    ('🔥 AMD FirePro V3200', 342, 26, 6250, 126, '🔥')
]

# Топовые (Tier 6) - 100 карт
top_gpus = [
    ('🚀 NVIDIA GeForce RTX 4090 Ti', 250, 600, 2500, 85, '🚀'),
    ('🚀 AMD Radeon RX 7950 XTX', 255, 400, 2600, 86, '🚀'),
    ('🚀 NVIDIA GeForce RTX 5090 X', 260, 650, 2700, 84, '🚀'),
    ('🚀 AMD Radeon RX 9000 XTX', 265, 450, 2800, 87, '🚀'),
    ('🚀 NVIDIA GeForce RTX 5090 Ti X', 270, 700, 2900, 85, '🚀'),
    ('🚀 AMD Radeon RX 10000 XTX', 275, 500, 3000, 88, '🚀'),
    ('🚀 NVIDIA GeForce RTX 6090 X', 280, 750, 3100, 86, '🚀'),
    ('🚀 AMD Radeon RX 11000 XTX', 285, 550, 3200, 89, '🚀'),
    ('🚀 NVIDIA GeForce RTX 6090 Ti X', 290, 800, 3300, 87, '🚀'),
    ('🚀 AMD Radeon RX 12000 XTX', 295, 600, 3400, 90, '🚀'),
    ('🚀 NVIDIA GeForce RTX 7090 X', 300, 850, 3500, 88, '🚀'),
    ('🚀 AMD Radeon RX 13000 XTX', 305, 650, 3600, 91, '🚀'),
    ('🚀 NVIDIA GeForce RTX 7090 Ti X', 310, 900, 3700, 89, '🚀'),
    ('🚀 AMD Radeon RX 14000 XTX', 315, 700, 3800, 92, '🚀'),
    ('🚀 NVIDIA GeForce RTX 8090 X', 320, 950, 3900, 90, '🚀'),
    ('🚀 AMD Radeon RX 15000 XTX', 325, 750, 4000, 93, '🚀'),
    ('🚀 NVIDIA GeForce RTX 8090 Ti X', 330, 1000, 4100, 91, '🚀'),
    ('🚀 AMD Radeon RX 16000 XTX', 335, 800, 4200, 94, '🚀'),
    ('🚀 NVIDIA GeForce RTX 9090 X', 340, 1050, 4300, 92, '🚀'),
    ('🚀 AMD Radeon RX 17000 XTX', 345, 850, 4400, 95, '🚀'),
    ('🚀 NVIDIA GeForce RTX 9090 Ti X', 350, 1100, 4500, 93, '🚀'),
    ('🚀 AMD Radeon RX 18000 XTX', 355, 900, 4600, 96, '🚀'),
    ('🚀 NVIDIA GeForce RTX 10090 X', 360, 1150, 4700, 94, '🚀'),
    ('🚀 AMD Radeon RX 19000 XTX', 365, 950, 4800, 97, '🚀'),
    ('🚀 NVIDIA GeForce RTX 10090 Ti X', 370, 1200, 4900, 95, '🚀'),
    ('🚀 AMD Radeon RX 20000 XTX', 375, 1000, 5000, 98, '🚀'),
    ('🚀 NVIDIA GeForce RTX 11090 X', 380, 1250, 5100, 96, '🚀'),
    ('🚀 AMD Radeon RX 21000 XTX', 385, 1050, 5200, 99, '🚀'),
    ('🚀 NVIDIA GeForce RTX 11090 Ti X', 390, 1300, 5300, 97, '🚀'),
    ('🚀 AMD Radeon RX 22000 XTX', 395, 1100, 5400, 100, '🚀'),
    ('🚀 NVIDIA GeForce RTX 12090 X', 400, 1350, 5500, 98, '🚀'),
    ('🚀 AMD Radeon RX 23000 XTX', 405, 1150, 5600, 101, '🚀'),
    ('🚀 NVIDIA GeForce RTX 12090 Ti X', 410, 1400, 5700, 99, '🚀'),
    ('🚀 AMD Radeon RX 24000 XTX', 415, 1200, 5800, 102, '🚀'),
    ('🚀 NVIDIA GeForce RTX 13090 X', 420, 1450, 5900, 100, '🚀'),
    ('🚀 AMD Radeon RX 25000 XTX', 425, 1250, 6000, 103, '🚀'),
    ('🚀 NVIDIA GeForce RTX 13090 Ti X', 430, 1500, 6100, 101, '🚀'),
    ('🚀 AMD Radeon RX 26000 XTX', 435, 1300, 6200, 104, '🚀'),
    ('🚀 NVIDIA GeForce RTX 14090 X', 440, 1550, 6300, 102, '🚀'),
    ('🚀 AMD Radeon RX 27000 XTX', 445, 1350, 6400, 105, '🚀'),
    ('🚀 NVIDIA GeForce RTX 14090 Ti X', 450, 1600, 6500, 103, '🚀'),
    ('🚀 AMD Radeon RX 28000 XTX', 455, 1400, 6600, 106, '🚀'),
    ('🚀 NVIDIA GeForce RTX 15090 X', 460, 1650, 6700, 104, '🚀'),
    ('🚀 AMD Radeon RX 29000 XTX', 465, 1450, 6800, 107, '🚀'),
    ('🚀 NVIDIA GeForce RTX 15090 Ti X', 470, 1700, 6900, 105, '🚀'),
    ('🚀 AMD Radeon RX 30000 XTX', 475, 1500, 7000, 108, '🚀'),
    ('🚀 NVIDIA GeForce RTX 16090 X', 480, 1750, 7100, 106, '🚀'),
    ('🚀 AMD Radeon RX 31000 XTX', 485, 1550, 7200, 109, '🚀'),
    ('🚀 NVIDIA GeForce RTX 16090 Ti X', 490, 1800, 7300, 107, '🚀'),
    ('🚀 AMD Radeon RX 32000 XTX', 495, 1600, 7400, 110, '🚀'),
    ('🚀 NVIDIA GeForce RTX 17090 X', 500, 1850, 7500, 108, '🚀'),
    ('🚀 AMD Radeon RX 33000 XTX', 505, 1650, 7600, 111, '🚀'),
    ('🚀 NVIDIA GeForce RTX 17090 Ti X', 510, 1900, 7700, 109, '🚀'),
    ('🚀 AMD Radeon RX 34000 XTX', 515, 1700, 7800, 112, '🚀'),
    ('🚀 NVIDIA GeForce RTX 18090 X', 520, 1950, 7900, 110, '🚀'),
    ('🚀 AMD Radeon RX 35000 XTX', 525, 1750, 8000, 113, '🚀'),
    ('🚀 NVIDIA GeForce RTX 18090 Ti X', 530, 2000, 8100, 111, '🚀'),
    ('🚀 AMD Radeon RX 36000 XTX', 535, 1800, 8200, 114, '🚀'),
    ('🚀 NVIDIA GeForce RTX 19090 X', 540, 2050, 8300, 112, '🚀'),
    ('🚀 AMD Radeon RX 37000 XTX', 545, 1850, 8400, 115, '🚀'),
    ('🚀 NVIDIA GeForce RTX 19090 Ti X', 550, 2100, 8500, 113, '🚀'),
    ('🚀 AMD Radeon RX 38000 XTX', 555, 1900, 8600, 116, '🚀'),
    ('🚀 NVIDIA GeForce RTX 20090 X', 560, 2150, 8700, 114, '🚀'),
    ('🚀 AMD Radeon RX 39000 XTX', 565, 1950, 8800, 117, '🚀'),
    ('🚀 NVIDIA GeForce RTX 20090 Ti X', 570, 2200, 8900, 115, '🚀'),
    ('🚀 AMD Radeon RX 40000 XTX', 575, 2000, 9000, 118, '🚀'),
    ('🚀 NVIDIA GeForce RTX 21090 X', 580, 2250, 9100, 116, '🚀'),
    ('🚀 AMD Radeon RX 41000 XTX', 585, 2050, 9200, 119, '🚀'),
    ('🚀 NVIDIA GeForce RTX 21090 Ti X', 590, 2300, 9300, 117, '🚀'),
    ('🚀 AMD Radeon RX 42000 XTX', 595, 2100, 9400, 120, '🚀'),
    ('🚀 NVIDIA GeForce RTX 22090 X', 600, 2350, 9500, 118, '🚀'),
    ('🚀 AMD Radeon RX 43000 XTX', 605, 2150, 9600, 121, '🚀'),
    ('🚀 NVIDIA GeForce RTX 22090 Ti X', 610, 2400, 9700, 119, '🚀'),
    ('🚀 AMD Radeon RX 44000 XTX', 615, 2200, 9800, 122, '🚀'),
    ('🚀 NVIDIA GeForce RTX 23090 X', 620, 2450, 9900, 120, '🚀'),
    ('🚀 AMD Radeon RX 45000 XTX', 625, 2250, 10000, 123, '🚀'),
    ('🚀 NVIDIA GeForce RTX 23090 Ti X', 630, 2500, 10100, 121, '🚀'),
    ('🚀 AMD Radeon RX 46000 XTX', 635, 2300, 10200, 124, '🚀'),
    ('🚀 NVIDIA GeForce RTX 24090 X', 640, 2550, 10300, 122, '🚀'),
    ('🚀 AMD Radeon RX 47000 XTX', 645, 2350, 10400, 125, '🚀'),
    ('🚀 NVIDIA GeForce RTX 24090 Ti X', 650, 2600, 10500, 123, '🚀'),
    ('🚀 AMD Radeon RX 48000 XTX', 655, 2400, 10600, 126, '🚀'),
    ('🚀 NVIDIA GeForce RTX 25090 X', 660, 2650, 10700, 124, '🚀'),
    ('🚀 AMD Radeon RX 49000 XTX', 665, 2450, 10800, 127, '🚀'),
    ('🚀 NVIDIA GeForce RTX 25090 Ti X', 670, 2700, 10900, 125, '🚀'),
    ('🚀 AMD Radeon RX 50000 XTX', 675, 2500, 11000, 128, '🚀'),
    ('🚀 NVIDIA GeForce RTX 26090 X', 680, 2750, 11100, 126, '🚀'),
    ('🚀 AMD Radeon RX 51000 XTX', 685, 2550, 11200, 129, '🚀'),
    ('🚀 NVIDIA GeForce RTX 26090 Ti X', 690, 2800, 11300, 127, '🚀'),
    ('🚀 AMD Radeon RX 52000 XTX', 695, 2600, 11400, 130, '🚀'),
    ('🚀 NVIDIA GeForce RTX 27090 X', 700, 2850, 11500, 128, '🚀'),
    ('🚀 AMD Radeon RX 53000 XTX', 705, 2650, 11600, 131, '🚀'),
    ('🚀 NVIDIA GeForce RTX 27090 Ti X', 710, 2900, 11700, 129, '🚀'),
    ('🚀 AMD Radeon RX 54000 XTX', 715, 2700, 11800, 132, '🚀'),
    ('🚀 NVIDIA GeForce RTX 28090 X', 720, 2950, 11900, 130, '🚀'),
    ('🚀 AMD Radeon RX 55000 XTX', 725, 2750, 12000, 133, '🚀'),
    ('🚀 NVIDIA GeForce RTX 28090 Ti X', 730, 3000, 12100, 131, '🚀'),
    ('🚀 AMD Radeon RX 56000 XTX', 735, 2800, 12200, 134, '🚀')
]

# Заполняем словарь GPUS
tier_index = 0
for tier, gpu_list in enumerate([weak_gpus, budget_gpus, medium_gpus, good_gpus, powerful_gpus, top_gpus], 1):
    for i, (name, hashrate, power, cost, temp, icon) in enumerate(gpu_list):
        gpu_id = f"tier{tier}_gpu{i}"
        GPUS[gpu_id] = {
            'name': name,
            'hashrate': hashrate,
            'power': power,
            'cost': cost,
            'temp': temp,
            'icon': icon,
            'tier': tier
        }

# ========== УСЛУГИ ==========
SERVICES = {
    'booster_temp': {'name': '❄️ Бустер охлаждения', 'rub_price': 25, 'usd_price': 0.30, 'duration': 24, 'effect': 'temp_reduce', 'amount': 15},
    'booster_energy': {'name': '⚡ Бустер энергии', 'rub_price': 25, 'usd_price': 0.30, 'duration': 24, 'effect': 'energy_reduce', 'amount': 20},
    'booster_combo': {'name': '🚀 Комбо-бустер', 'rub_price': 50, 'usd_price': 0.60, 'duration': 24, 'effect': 'combo', 'amount': 30},
    'status_beginner': {'name': '⚜️ Начинающий майнер', 'rub_price': 99, 'usd_price': 1.20, 'bonus': 'hashrate_10', 'permanent': True},
    'status_coin': {'name': '⚜️ Монетный майнер', 'rub_price': 199, 'usd_price': 2.40, 'bonus': 'hashrate_25', 'permanent': True},
    'status_dollar': {'name': '⚜️ Долларовый майнер', 'rub_price': 349, 'usd_price': 4.20, 'bonus': 'hashrate_50', 'permanent': True},
    'status_gold': {'name': '⚜️ Золотой майнер', 'rub_price': 499, 'usd_price': 6.00, 'bonus': 'hashrate_75', 'permanent': True},
    'status_diamond': {'name': '💎 Алмазный майнер', 'rub_price': 649, 'usd_price': 7.80, 'bonus': 'hashrate_100', 'permanent': True},
    'status_sapphire': {'name': '💠 Сапфировый майнер', 'rub_price': 1299, 'usd_price': 15.60, 'bonus': 'hashrate_200', 'permanent': True},
}

# ========== УЛУЧШЕНИЯ (50 уровней кулеров и блоков питания) ==========
UPGRADES = {}

# Кулеры (50 уровней)
cooler_brands = ['Deepcool', 'Corsair', 'Noctua', 'be quiet!', 'Cooler Master', 'NZXT', 'Arctic', 'Thermaltake', 'Lian Li', 'Fractal Design']
for i in range(1, 51):
    brand = cooler_brands[(i-1) % len(cooler_brands)]
    level = (i-1) // 5 + 1
    model = f"{brand} Cooler Level {i}"
    price = 50 * i
    effect = f"max_temp_+{(i*2)}"
    UPGRADES[f'cooling_{i}'] = {'name': f'❄️ {model}', 'price': price, 'effect': effect, 'type': 'cooling'}

# Блоки питания (50 уровней)
psu_brands = ['Corsair', 'Seasonic', 'EVGA', 'be quiet!', 'Thermaltake', 'Cooler Master', 'FSP', 'Super Flower', 'XPG', 'Gigabyte']
for i in range(1, 51):
    brand = psu_brands[(i-1) % len(psu_brands)]
    wattage = 500 + (i * 100)
    price = 100 * i
    effect = f"max_energy_+{wattage}"
    UPGRADES[f'energy_{i}'] = {'name': f'⚡ {brand} {wattage}W PSU', 'price': price, 'effect': effect, 'type': 'energy'}

# Водяное охлаждение (10 уровней)
water_cooling = [
    ('🌊 Deepcool Castle 240EX', 50000, 'water_cooling_1', 'max_temp_+100'),
    ('🌊 Corsair H100i RGB', 100000, 'water_cooling_2', 'max_temp_+200'),
    ('🌊 NZXT Kraken X53', 150000, 'water_cooling_3', 'max_temp_+300'),
    ('🌊 Arctic Liquid Freezer II', 200000, 'water_cooling_4', 'max_temp_+400'),
    ('🌊 Cooler Master MasterLiquid', 250000, 'water_cooling_5', 'max_temp_+500'),
    ('🌊 Lian Li Galahad', 300000, 'water_cooling_6', 'max_temp_+600'),
    ('🌊 EK-AIO Basic', 350000, 'water_cooling_7', 'max_temp_+700'),
    ('🌊 Alphacool Eisbaer', 400000, 'water_cooling_8', 'max_temp_+800'),
    ('🌊 Thermaltake Pacific', 450000, 'water_cooling_9', 'max_temp_+900'),
    ('🌊 Custom Water Loop', 500000, 'water_cooling_10', 'max_temp_+1000')
]

for name, price, upgrade_id, effect in water_cooling:
    UPGRADES[upgrade_id] = {'name': name, 'price': price, 'effect': effect, 'type': 'water_cooling'}

# Слоты фермы
UPGRADES['farm_1'] = {'name': '🏭 Слот фермы Level 1', 'price': 200, 'effect': 'max_gpus_+1', 'type': 'farm'}
UPGRADES['farm_2'] = {'name': '🏭 Слот фермы Level 2', 'price': 400, 'effect': 'max_gpus_+2', 'type': 'farm'}
UPGRADES['farm_3'] = {'name': '🏭 Слот фермы Level 3', 'price': 800, 'effect': 'max_gpus_+5', 'type': 'farm'}
UPGRADES['farm_4'] = {'name': '🏭 Слот фермы Level 4', 'price': 1600, 'effect': 'max_gpus_+10', 'type': 'farm'}
UPGRADES['farm_5'] = {'name': '🏭 Слот фермы Level 5', 'price': 3200, 'effect': 'max_gpus_+20', 'type': 'farm'}

# ========== ЗАЩИТА ФЕРМЫ ==========
PROTECTION_PLANS = {
    '1h': {'name': '🛡️ Защита 1 час', 'price': 100, 'duration': 1, 'price_type': 'balance'},
    '8h': {'name': '🛡️ Защита 8 часов', 'price': 500, 'duration': 8, 'price_type': 'balance'},
    '24h': {'name': '🛡️ Защита 24 часа', 'price': 15, 'duration': 24, 'price_type': 'stars'}
}

# ========== ФУНКЦИИ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========
def get_user_data(user_id, username=""):
    """Получение или создание данных пользователя"""
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            'username': username or f"user_{user_id}",
            'balance': 5.0,
            'total_mined': 0,
            'total_earned': 5,
            'energy': 1500,
            'max_energy': 1500,
            'temperature': 30,
            'max_temperature': 100,
            'hashrate': 5,
            'gpus': {},
            'active_gpus': 0,
            'max_gpus': 1,
            'upgrades': {},
            'farm_protection': None,
            'protection_plans': {},
            'purchased_services': {},
            'active_boosters': {},
            'last_mining': datetime.now().isoformat(),
            'referrals': [],
            'referrals_subscribed': [],  # НОВОЕ: рефералы, которые подписались
            'ref_earned': 0,
            'ref_rub_earned': 0,  # НОВОЕ: заработано рублей на рефералах
            'rub_balance': 0,     # НОВОЕ: баланс рублей
            'achievements': [],
            'registered': datetime.now().isoformat(),
            'total_electricity_cost': 0,
            'total_cooling_cost': 0,
            'pvp_attacks_today': 0,
            'pvp_attacks_date': datetime.now().strftime("%Y-%m-%d"),
            'pvp_defended': 0,
            'pvp_success': 0,
            'pvp_total_stolen': 0,
            'last_attacked': None,
            'attack_cooldown': None,
            'total_gpu_wear': 0,
            'last_repair_cost': 0,
            'skins': {},
            'active_skin': None,
            'secret_skins': {},
            'secret_boosters': {},
            'secret_statuses': {},
            'promocodes_used': [],
            'mining_time_minutes': 0,
            'stars_balance': 0,
            'last_energy_buy': None,
            'referrer': None  # НОВОЕ: кто пригласил этого пользователя
        }
        save_data()
    
    return user_data[str(user_id)]

def update_user(user_id, updates):
    """Обновление данных пользователя"""
    user_data[str(user_id)].update(updates)
    save_data()
    
async def deactivate_weaker_gpus(user_id, new_gpu_id):
    """Деактивирует более слабые видеокарты при покупке новой"""
    user_info = get_user_data(user_id)
    new_gpu_info = GPUS[new_gpu_id]
    
    if not user_info.get('gpus'):
        return
    
    # Находим все видеокарты с меньшим хешрейтом
    weaker_gpus = []
    for gpu_id, gpu_data in user_info['gpus'].items():
        if gpu_id in GPUS:
            gpu_info = GPUS[gpu_id]
            if (gpu_info['hashrate'] < new_gpu_info['hashrate'] and 
                gpu_data.get('active', True)):  # Проверяем активна ли карта
                weaker_gpus.append((gpu_id, gpu_data))
    
    # Деактивируем более слабые карты
    for gpu_id, gpu_data in weaker_gpus:
        user_info['gpus'][gpu_id]['active'] = False
    
    # Сохраняем изменения
    update_user(user_id, {'gpus': user_info['gpus']})
    
    return weaker_gpus

# ========== ПРОВЕРКА ПОДПИСКИ (КАНАЛ И ЧАТ) ==========
async def check_subscriptions(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на канал и чат"""
    try:
        # Проверка канала
        channel_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        channel_subscribed = channel_member.status in ['member', 'administrator', 'creator']
        
        # Проверка чата
        chat_member = await context.bot.get_chat_member(chat_id=CHAT_ID, user_id=user_id)
        chat_subscribed = chat_member.status in ['member', 'administrator', 'creator']
        
        return channel_subscribed and chat_subscribed
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str = None):
    """Требует подписку и показывает сообщение"""
    user_id = update.effective_user.id
    
    is_subscribed = await check_subscriptions(user_id, context)
    if is_subscribed:
        await check_and_reward_subscription_bonus(user_id, context)
        return True
    
    try:
        channel_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        channel_subscribed = channel_member.status in ['member', 'administrator', 'creator']
    except:
        channel_subscribed = False
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHAT_ID, user_id=user_id)
        chat_subscribed = chat_member.status in ['member', 'administrator', 'creator']
    except:
        chat_subscribed = False
    
    missing = []
    if not channel_subscribed:
        missing.append(f"📢 Канал: {CHANNEL_USERNAME}")
    if not chat_subscribed:
        missing.append(f"💬 Чат: {CHAT_USERNAME}")
    
    text = message_text or f"""
⚠️ Для использования бота необходимо подписаться!

Не подписаны:
{chr(10).join(missing)}

Пожалуйста:
1. Нажмите на кнопки ниже, чтобы перейти
2. Подпишитесь на канал и чат
3. Нажмите кнопку "✅ Я подписался"

🎁 Бонус: 
• Реферер получит 0.50₽ когда вы подпишетесь!
• Вы сможете зарабатывать рубли, приглашая друзей

💰 Вывод рублей: от 50₽ на карты российских банков
"""
    
    keyboard = []
    if not channel_subscribed:
        keyboard.append([InlineKeyboardButton("📢 Перейти в канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")])
    if not chat_subscribed:
        keyboard.append([InlineKeyboardButton("💬 Перейти в чат", url=f"https://t.me/{CHAT_USERNAME[1:]}")])
    keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data='check_subscription')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])
    
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Ошибка в require_subscription: {e}")
    
    return False
    
# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = [
        [InlineKeyboardButton("⛏️ Майнить", callback_data='mine'),
         InlineKeyboardButton("❄️ Остудить", callback_data='cool_farm')],
        [InlineKeyboardButton("🔄 Обновить", callback_data='refresh_stats'),
         InlineKeyboardButton("🖥 Мои GPU", callback_data='my_gpus')],
        [InlineKeyboardButton("🗡 Атаковать", callback_data='pvp_menu'),
         InlineKeyboardButton("🛡 Защита", callback_data='protection_menu')],
        [InlineKeyboardButton("🔧 Ремонт", callback_data='repair_gpus'),
         InlineKeyboardButton("🛒 Магазин GPU", callback_data='gpu_shop')],
        [InlineKeyboardButton("⚙️ Улучшения", callback_data='upgrades'),
         InlineKeyboardButton("⚡️ Энергия", callback_data='energy')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats'),
         InlineKeyboardButton("🏆 Топы", callback_data='tops')],
        [InlineKeyboardButton("👥 Рефералы", callback_data='referrals'),
         InlineKeyboardButton("🎁 Промокод", callback_data='promo')],
        [InlineKeyboardButton("🛒 Услуги", callback_data='services'),
         InlineKeyboardButton("💰 Вывести", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data='support'),
         InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Клавиатура админа"""
    keyboard = [
        [InlineKeyboardButton("💰 Выдать баланс", callback_data='admin_give_balance'),
         InlineKeyboardButton("🎁 Создать промокод", callback_data='admin_create_promo')],
        [InlineKeyboardButton("🛡️ Выдать защиту", callback_data='admin_give_protection'),
         InlineKeyboardButton("👥 Список пользователей", callback_data='admin_users')],
        [InlineKeyboardButton("🎨 Выдать скины/бустеры/статусы", callback_data='admin_give_items')],
        [InlineKeyboardButton("🔒 Выдать секретные предметы", callback_data='admin_give_secret_items')],
        [InlineKeyboardButton("🎫 Создать секретный промокод", callback_data='admin_create_secret_promo')],
        [InlineKeyboardButton("🎪 Управление ивентами", callback_data='admin_events')],
        [InlineKeyboardButton("💰 Обнулить ₽ баланс", callback_data='admin_clear_rub'),  # ← НОВАЯ КНОПКА
         InlineKeyboardButton("📊 Статистика бота", callback_data='admin_stats')],
        [InlineKeyboardButton("⚙️ Настройки бота", callback_data='admin_settings'),
         InlineKeyboardButton("🆘 Тикеты поддержки", callback_data='admin_tickets')],
        [InlineKeyboardButton("🔙 В главное меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_gpu_shop_keyboard():
    """Магазин GPU с категориями"""
    keyboard = [
        [InlineKeyboardButton("🟢 Самые слабые (1-100)", callback_data='gpu_tier_1'),
         InlineKeyboardButton("📱 Бюджетные (101-200)", callback_data='gpu_tier_2')],
        [InlineKeyboardButton("⚡ Средние (201-300)", callback_data='gpu_tier_3'),
         InlineKeyboardButton("💎 Хорошие (301-400)", callback_data='gpu_tier_4')],
        [InlineKeyboardButton("🔥 Мощные (401-500)", callback_data='gpu_tier_5'),
         InlineKeyboardButton("🚀 Топовые (501-600)", callback_data='gpu_tier_6')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_gpu_tier_keyboard(tier, page=0):
    """Клавиатура для конкретного тира видеокарт с пагинацией"""
    items_per_page = 10
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    
    keyboard = []
    
    # Фильтруем видеокарты по тиру
    tier_gpus = [(gpu_id, gpu_info) for gpu_id, gpu_info in GPUS.items() if gpu_info['tier'] == int(tier)]
    tier_gpus.sort(key=lambda x: x[1]['cost'])
    
    # Получаем видеокарты для текущей страницы
    for gpu_id, gpu_info in tier_gpus[start_idx:end_idx]:
        keyboard.append([InlineKeyboardButton(
            f"{gpu_info['icon']} {gpu_info['name']} - {gpu_info['cost']}$",
            callback_data=f'buy_gpu_{gpu_id}'
        )])
    
    # Добавляем кнопки пагинации
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'gpu_tier_{tier}_{page-1}'))
    
    navigation_buttons.append(InlineKeyboardButton(f"Страница {page+1}", callback_data='noop'))
    
    if end_idx < len(tier_gpus):
        navigation_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'gpu_tier_{tier}_{page+1}'))
    
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='gpu_shop')])
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard():
    """Клавиатура поддержки"""
    keyboard = [
        [InlineKeyboardButton("📝 Создать тикет", callback_data='create_ticket')],
        [InlineKeyboardButton("📋 Мои тикеты", callback_data='my_tickets')],
        [InlineKeyboardButton("💬 Написать менеджеру", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_services_keyboard():
    """Клавиатура раздела Услуги"""
    keyboard = [
        [InlineKeyboardButton("🚀 Бустеры", callback_data='services_boosters')],
        [InlineKeyboardButton("⚜️ Статусы", callback_data='services_statuses')],
        [InlineKeyboardButton("🎨 Скины", callback_data='services_skins')],
        [InlineKeyboardButton("🛡️ Защита фермы", callback_data='protection_menu')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_boosters_keyboard():
    """Клавиатура бустеров"""
    keyboard = []
    for service_id, service in SERVICES.items():
        if 'booster' in service_id:
            keyboard.append([InlineKeyboardButton(
                f"{service['name']} - {service['usd_price']}$",
                callback_data=f'buy_service_{service_id}'
            )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='services')])
    return InlineKeyboardMarkup(keyboard)

def get_statuses_keyboard():
    """Клавиатура статусов"""
    keyboard = []
    for service_id, service in SERVICES.items():
        if 'status' in service_id:
            keyboard.append([InlineKeyboardButton(
                f"{service['name']} - {service['usd_price']}$",
                callback_data=f'buy_service_{service_id}'
            )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='services')])
    return InlineKeyboardMarkup(keyboard)

def get_tops_keyboard():
    """Клавиатура топов"""
    keyboard = [
        [InlineKeyboardButton("💰 Топ по балансу", callback_data='top_balance'),
         InlineKeyboardButton("👥 Топ по приглашениям", callback_data='top_referrals')],
        [InlineKeyboardButton("⛏️ Топ по хешрейту", callback_data='top_hashrate'),
         InlineKeyboardButton("🖥️ Топ по GPU", callback_data='top_gpus')],
        [InlineKeyboardButton("🏆 Топ по PvP", callback_data='top_pvp'),
         InlineKeyboardButton("📈 Топ по доходу", callback_data='top_earned')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Клавиатура с кнопкой Назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]]
    return InlineKeyboardMarkup(keyboard)

def get_energy_keyboard():
    """Клавиатура энергии"""
    keyboard = [
        [InlineKeyboardButton("⚡ Купить энергию (Telegram Stars)", callback_data='buy_energy_stars')],
        [InlineKeyboardButton("⚙️ Улучшить блок питания", callback_data='upgrades')],
        [InlineKeyboardButton("🚀 Бустер энергии", callback_data='services_boosters')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    # Сначала проверяем подписку
    if not await check_subscriptions(user_id, context):
        await require_subscription(update, context)
        return
    
    # Остальной код
    args = context.args
    ref_code = None
    if args and args[0].startswith('ref'):
        ref_code = args[0][3:]
    
    user_info = get_user_data(user_id, user.username or user.first_name)
    
    if ref_code and ref_code.isdigit() and ref_code != str(user_id):
        ref_user_id = int(ref_code)
        if str(ref_user_id) in user_data:
            if user_id not in user_data[str(ref_user_id)].get('referrals', []):
                # Добавляем в рефералы
                user_data[str(ref_user_id)]['referrals'].append(user_id)
                user_data[str(ref_user_id)]['balance'] += 50
                user_data[str(ref_user_id)]['ref_earned'] = user_data[str(ref_user_id)].get('ref_earned', 0) + 50
                
                # Дарим бонус новичку
                user_info['balance'] += 25
                
                # Сохраняем кто пригласил
                user_info['referrer'] = ref_user_id
                
                save_data()
                
                log_transaction(ref_user_id, user_data[str(ref_user_id)]['username'], "REF_BONUS", 50, f"За приглашение {user_id}")
                log_transaction(user_id, user_info['username'], "REF_BONUS", 25, f"От реферера {ref_user_id}")
                
                await check_and_reward_subscription_bonus(user_id, context)
    
    welcome_text = f"""
🎮 Добро пожаловать в Mine Evo Ultra, {user.first_name}!

⚡️ Ваш стартовый пакет:
💰 Баланс: {user_info['balance']:.2f} $
🇷🇺 Баланс в рублях: {user_info.get('rub_balance', 0):.2f} ₽
⛏️ Хешрейт: {user_info['hashrate']:.1f} MH/s
🖥 GPU: {user_info['active_gpus']}/{user_info['max_gpus']}

📊 Реферальная ссылка:
https://t.me/{BOT_USERNAME[1:]}?start=ref{user_id}

👥 Приглашайте друзей и получайте:
• 25$ вам за каждого приглашенного
• 50$ вашему рефереру
• 5% от их дохода навсегда!
• 0.50₽ за каждого реферала, который подпишется на каналы

💎 Подпишитесь на каналы:
📢 Канал: {CHANNEL_USERNAME}
💬 Чат: {CHAT_USERNAME}

💰 Вывод рублей:
• Минимальная сумма: 50₽
• На карты российских банков
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

async def check_and_reward_subscription_bonus(user_id, context):
    """Проверяет подписки и начисляет 0.50₽ рефереру"""
    try:
        user_info = get_user_data(user_id)
        
        # Проверяем подписки
        is_subscribed = await check_subscriptions(user_id, context)
        
        if is_subscribed and user_info.get('referrer'):
            referrer_id = user_info['referrer']
            referrer_info = get_user_data(referrer_id)
            
            # Проверяем, не начисляли ли уже бонус
            if user_id not in referrer_info.get('referrals_subscribed', []):
                # Начисляем 0.50₽
                referrer_info['rub_balance'] = referrer_info.get('rub_balance', 0) + 0.50
                referrer_info['ref_rub_earned'] = referrer_info.get('ref_rub_earned', 0) + 0.50
                
                # Добавляем в список награжденных
                if 'referrals_subscribed' not in referrer_info:
                    referrer_info['referrals_subscribed'] = []
                referrer_info['referrals_subscribed'].append(user_id)
                
                # Сохраняем
                update_user(referrer_id, {
                    'rub_balance': referrer_info['rub_balance'],
                    'ref_rub_earned': referrer_info['ref_rub_earned'],
                    'referrals_subscribed': referrer_info['referrals_subscribed']
                })
                
                # Логируем
                log_transaction(referrer_id, referrer_info['username'], "REF_SUB_BONUS", 0.50, 
                              f"Реферал {user_id} подписался на каналы")
                
                # Уведомляем реферера
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 *Получена награда!*\n\n"
                             f"Ваш реферал @{user_info['username']} подписался на каналы!\n"
                             f"💰 Начислено: *0.50₽*\n"
                             f"💎 Общий рублевый баланс: *{referrer_info['rub_balance']:.2f}₽*",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
                
                return True
        
        return False
    except Exception as e:
        logger.error(f"Ошибка при начислении бонуса за подписку: {e}")
        return False
            
# ========== МАЙНИНГ ==========
async def mine_crypto(query, user_id, context: ContextTypes.DEFAULT_TYPE):
    """Процесс майнинга"""
    user_info = get_user_data(user_id)
    
    if user_info['energy'] <= 0:
        await query.edit_message_text(
            "⚡ *Закончилась энергия!*\n\n"
            "Для продолжения майнинга:\n"
            "1. Подождите восстановления энергии\n"
            "2. Купите энергию через Telegram Stars\n"
            "3. Улучшите блок питания",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_energy_keyboard()
        )
        return
    
    if user_info['temperature'] >= user_info['max_temperature']:
        await query.edit_message_text(
            "🔥 *Перегрев!*\n\n"
            "Для продолжения майнинга:\n"
            "1. Остудите ферму\n"
            "2. Купите улучшенное охлаждение\n"
            "3. Подождите пока ферма остынет",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    
    if user_info['active_gpus'] == 0:
        await query.edit_message_text(
            "🖥️ *Нет видеокарт для майнинга!*\n\n"
            "Купите видеокарты в магазине.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    
        # ========== НА ЭТУ НОВУЮ ПРОВЕРКУ ==========
    # Новая проверка (только активные видеокарты):
    active_gpus_count = 0
    for gpu_id, gpu_data in user_info.get('gpus', {}).items():
        if gpu_data.get('active', True):  # Проверяем только активные карты
            active_gpus_count += 1
    
    if active_gpus_count == 0:
        await query.edit_message_text(
            "🖥️ *Нет активных видеокарт для майнинга!*\n\n"
            "Активируйте видеокарты в меню 'Мои GPU' или купите новые.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    # ========== КОНЕЦ ЗАМЕНЫ ==========
    
    # Повышенный износ (увеличен в 2 раза)
    energy_cost = min(200, user_info['hashrate'] * 0.2)
    user_info['energy'] = max(0, user_info['energy'] - energy_cost)
    
    temp_increase = user_info['hashrate'] * 0.1  # Увеличен нагрев
    user_info['temperature'] = min(user_info['max_temperature'], user_info['temperature'] + temp_increase)
    
    base_income = user_info['hashrate'] * 0.01
    multiplier = 1.0
    
    # Бонус от текущего ивента
    current_event = events_data.get('current_event', {})
    if current_event.get('active', False):
        event_end = datetime.fromisoformat(current_event.get('end_date', datetime.now().isoformat()))
        if event_end > datetime.now():
            multiplier *= (1 + current_event.get('bonus_percent', 0) / 100)
    
    temp_penalty = 1.0
    if user_info['temperature'] > 80:
        temp_penalty = 0.7  # Усиленный штраф
    elif user_info['temperature'] > 90:
        temp_penalty = 0.4  # Усиленный штраф
    
    income = base_income * multiplier * temp_penalty
    electricity_cost = user_info['hashrate'] * 0.01  # Увеличены расходы
    cooling_cost = max(0, user_info['temperature'] - 50) * 0.005  # Увеличены расходы
    net_income = income - electricity_cost - cooling_cost
    
    if net_income < 0:
        net_income = 0
    
    user_info['balance'] += net_income
    user_info['total_mined'] += net_income
    user_info['total_earned'] += net_income
    user_info['total_electricity_cost'] += electricity_cost
    user_info['total_cooling_cost'] += cooling_cost
    user_info['last_mining'] = datetime.now().isoformat()
    user_info['mining_time_minutes'] = user_info.get('mining_time_minutes', 0) + 5
    
    # Усиленный износ видеокарт (увеличен в 2 раза)
    wear_amount, broken_gpus = await apply_gpu_wear(user_info, 600)  # Увеличен износ
    
    # Обновляем хешрейт с учетом износа (только активные карты)
    total_hashrate = 5
    for gpu_id, gpu_data in user_info.get('gpus', {}).items():
        if gpu_id in GPUS and gpu_data.get('active', True):
            count = gpu_data.get('count', 0)
            durability = gpu_data.get('durability', 100)
            efficiency = durability / 100
            total_hashrate += GPUS[gpu_id]['hashrate'] * count * efficiency

    user_info['hashrate'] = total_hashrate

    
    update_user(user_id, {
        'balance': user_info['balance'],
        'energy': user_info['energy'],
        'temperature': user_info['temperature'],
        'total_mined': user_info['total_mined'],
        'total_earned': user_info['total_earned'],
        'total_electricity_cost': user_info['total_electricity_cost'],
        'total_cooling_cost': user_info['total_cooling_cost'],
        'last_mining': user_info['last_mining'],
        'hashrate': user_info['hashrate'],
        'gpus': user_info.get('gpus', {}),
        'mining_time_minutes': user_info['mining_time_minutes']
    })
    
    log_transaction(user_id, user_info['username'], "MINING", net_income, 
                   f"Хешрейт: {user_info['hashrate']:.1f} MH/s, Износ: {wear_amount:.2f}%")
    
    text = f"""
⛏️ *Майнинг запущен!*

💰 Добыто: *+{net_income:.4f}* $
⚡ Энергия: *-{energy_cost:.1f}* кВт
🌡️ Температура: *+{temp_increase:.1f}°C*
🔧 Износ: *-{wear_amount:.2f}%*

📈 *Состояние фермы:*
⚡ Энергия: *{user_info['energy']:.0f}/{user_info['max_energy']}* кВт
🌡️ Температура: *{user_info['temperature']:.1f}°C*
🖥️ Активных GPU: *{active_gpus_count}*

💰 Общий баланс: *{user_info['balance']:.2f}* $
"""
    
    if broken_gpus:
        text += f"\n⚠️ *Сломались видеокарты:*"
        for gpu_id, count in broken_gpus:
            gpu_name = GPUS.get(gpu_id, {}).get('name', 'Неизвестная')
            text += f"\n• {gpu_name} ×{count}"
    
    # Добавляем информацию об активном ивенте
    if current_event.get('active', False):
        event_end = datetime.fromisoformat(current_event['end_date'])
        days_left = (event_end - datetime.now()).days
        text += f"\n\n🎪 *Активный ивент:* {current_event['name']}"
        text += f"\n📊 Бонус: +{current_event.get('bonus_percent', 0)}% к доходу"
        text += f"\n⏱️ Осталось: {days_left} дней"
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== ИЗНОС ВИДЕОКАРТ (УСИЛЕННЫЙ) ==========
async def apply_gpu_wear(user_info, mining_time_seconds=600):
    """Применяет износ к видеокартам (только к активным)"""
    if not user_info.get('gpus'):
        return 0, []
    
    wear_amount = 0
    broken_gpus = []
    
    for gpu_id, gpu_data in user_info['gpus'].items():
        if gpu_id not in GPUS:
            continue
            
        # ПРОВЕРКА НА АКТИВНОСТЬ - ЭТО ОСНОВНОЕ ИЗМЕНЕНИЕ
        if not gpu_data.get('active', True):  # По умолчанию True для обратной совместимости
            continue  # Пропускаем неактивные карты
            
        count = gpu_data.get('count', 0)
        durability = gpu_data.get('durability', 100)
        
        if count > 0 and durability > 0:
            base_wear = 0.04  # Увеличен базовый износ в 2 раза
            wear_per_sec = base_wear / 3600
            total_wear = wear_per_sec * mining_time_seconds
            
            wear_factor = random.uniform(0.9, 1.3)  # Увеличен фактор износа
            actual_wear = total_wear * wear_factor * count
            
            new_durability = max(0, durability - actual_wear)
            user_info['gpus'][gpu_id]['durability'] = new_durability
            wear_amount += actual_wear
            
            # Увеличен шанс поломки
            if new_durability < 15 and random.random() < 0.15:
                broken_count = min(count, random.randint(1, max(1, count // 2)))
                user_info['gpus'][gpu_id]['count'] -= broken_count
                broken_gpus.append((gpu_id, broken_count))
                
                # Уменьшаем счетчик активных карт ТОЛЬКО если карта была активной
                if user_info['gpus'][gpu_id].get('active', True):
                    user_info['active_gpus'] -= broken_count
    
    user_info['total_gpu_wear'] += wear_amount
    return wear_amount, broken_gpus

async def repair_gpus(query, user_id):
    """Ремонт всех видеокарт"""
    user_info = get_user_data(user_id)
    
    if not user_info.get('gpus'):
        await query.edit_message_text(
            "❌ У вас нет видеокарт для ремонта!",
            reply_markup=get_back_keyboard()
        )
        return
    
    total_repair_cost = 0
    for gpu_id, gpu_data in user_info['gpus'].items():
        if gpu_id in GPUS:
            count = gpu_data.get('count', 0)
            durability = gpu_data.get('durability', 100)
            if durability < 100:
                wear = 100 - durability
                repair_cost = (wear / 100) * GPUS[gpu_id]['cost'] * count * 0.02  # Увеличена стоимость ремонта
                total_repair_cost += repair_cost
    
    if total_repair_cost <= 0:
        await query.edit_message_text(
            "✅ Все видеокарты в отличном состоянии!",
            reply_markup=get_back_keyboard()
        )
        return
    
    if user_info['balance'] < total_repair_cost:
        await query.edit_message_text(
            f"❌ Недостаточно средств для ремонта!\n"
            f"Нужно: {total_repair_cost:.2f}$\n"
            f"У вас: {user_info['balance']:.2f}$",
            reply_markup=get_back_keyboard()
        )
        return
    
    user_info['balance'] -= total_repair_cost
    user_info['last_repair_cost'] = total_repair_cost
    
    for gpu_id in user_info['gpus']:
        if user_info['gpus'][gpu_id]['durability'] < 100:
            user_info['gpus'][gpu_id]['durability'] = 100
    
    update_user(user_id, {
        'balance': user_info['balance'],
        'gpus': user_info['gpus'],
        'last_repair_cost': user_info['last_repair_cost']
    })
    
    log_transaction(user_id, user_info['username'], "REPAIR_GPUS", -total_repair_cost, "Ремонт всех GPU")
    
    await query.edit_message_text(
        f"✅ Все видеокарты отремонтированы!\n"
        f"💰 Стоимость: {total_repair_cost:.2f}$\n"
        f"💎 Новый баланс: {user_info['balance']:.2f}$",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== МОИ GPU ==========
async def show_my_gpus(query, user_id):
    """Показать мои видеокарты"""
    user_info = get_user_data(user_id)
    
    # Считаем реально активные карты (с учетом флага active и количества)
    active_gpus_count = 0
    for gpu_id, gpu_data in user_info.get('gpus', {}).items():
        if gpu_data.get('active', True):
            active_gpus_count += gpu_data.get('count', 0)
    
    text = f"🖥️ *Мои видеокарты*\n\n"
    text += f"📊 Активных видеокарт: {active_gpus_count}/{user_info['max_gpus']}\n\n"
    
    if not user_info.get('gpus') or active_gpus_count == 0:
        text += "❌ У вас нет активных видеокарт.\n"
        text += "🛒 Купите видеокарты в магазине или активируйте существующие!"
    else:
        total_hashrate = 5
        total_value = 0
        total_power = 0
        
        for gpu_id, gpu_data in user_info['gpus'].items():
            if gpu_id in GPUS:
                count = gpu_data.get('count', 0)
                if count > 0:
                    durability = gpu_data.get('durability', 100)
                    gpu_name = GPUS[gpu_id]['name']
                    hashrate = GPUS[gpu_id]['hashrate'] * count
                    gpu_value = GPUS[gpu_id]['cost'] * count
                    gpu_power = GPUS[gpu_id]['power'] * count
                    efficiency = durability / 100
                    is_active = gpu_data.get('active', True)
                    status = "🟢" if is_active else "🔴"
                    
                    text += f"{status} {gpu_name} ×{count}\n"
                    text += f"  ⛏ Хешрейт: {hashrate:.1f} MH/s ({efficiency*100:.0f}%)\n"
                    text += f"  ⚡ Потребление: {gpu_power} Вт\n"
                    text += f"  🛠 Прочность: {durability:.1f}%\n"
                    text += f"  💰 Стоимость: {gpu_value}$\n\n"
                    
                    if is_active:
                        total_hashrate += hashrate * efficiency
                        total_value += gpu_value
                        total_power += gpu_power
        
        text += f"\n📊 *Общая статистика:*\n"
        text += f"⛏ Общий хешрейт: {total_hashrate:.1f} MH/s\n"
        text += f"🖥 Всего видеокарт: {sum(gpu.get('count', 0) for gpu in user_info.get('gpus', {}).values())}\n"
        text += f"⚡ Общее потребление: {total_power} Вт\n"
        text += f"💰 Стоимость фермы: {total_value:.0f}$\n"
        text += f"🔧 Общий износ: {user_info.get('total_gpu_wear', 0):.2f}%"
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Управление", callback_data='manage_gpus'),
         InlineKeyboardButton("🛒 Купить еще", callback_data='gpu_shop')],
        [InlineKeyboardButton("🔧 Ремонт", callback_data='repair_gpus'),
         InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def manage_gpus_activity(query, user_id):
    """Управление активностью видеокарт"""
    user_info = get_user_data(user_id)
    
    # ИЗМЕНЕНИЕ: проверяем наличие любых видеокарт, а не только активных
    if not user_info.get('gpus'):
        await query.edit_message_text(
            "❌ У вас нет видеокарт для управления.",
            reply_markup=get_back_keyboard()
        )
        return
    
    text = "⚙️ *Управление видеокартами*\n\n"
    keyboard = []
    
    has_gpus_to_manage = False  # Флаг, есть ли карты для управления
    
    for gpu_id, gpu_data in user_info['gpus'].items():
        if gpu_id in GPUS:
            count = gpu_data.get('count', 0)
            if count > 0:
                has_gpus_to_manage = True  # Нашли хотя бы одну карту
                gpu_name = GPUS[gpu_id]['name']
                is_active = gpu_data.get('active', True)
                status = "🟢 Активна" if is_active else "🔴 Неактивна"
                
                text += f"{gpu_name} ×{count} - {status}\n"
                
                # Кнопки для управления
                if is_active:
                    keyboard.append([InlineKeyboardButton(
                        f"🔴 Выключить {gpu_name}",
                        callback_data=f'deactivate_gpu_{gpu_id}'
                    )])
                else:
                    keyboard.append([InlineKeyboardButton(
                        f"🟢 Включить {gpu_name}",
                        callback_data=f'activate_gpu_{gpu_id}'
                    )])
    
    # Если нет карт для управления
    if not has_gpus_to_manage:
        await query.edit_message_text(
            "❌ У вас нет видеокарт для управления.",
            reply_markup=get_back_keyboard()
        )
        return
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='my_gpus')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
async def activate_gpu(query, user_id, gpu_id):
    """Активировать видеокарту"""
    user_info = get_user_data(user_id)
    
    if gpu_id not in user_info.get('gpus', {}):
        await query.edit_message_text(
            "❌ Видеокарта не найдена!",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Проверяем лимит видеокарт
    if user_info['active_gpus'] >= user_info['max_gpus']:
        await query.edit_message_text(
            f"❌ Достигнут лимит активных видеокарт!\n"
            f"Максимум: {user_info['max_gpus']}\n"
            f"У вас: {user_info['active_gpus']}\n\n"
            f"Деактивируйте другие карты или увеличьте слоты.",
            reply_markup=get_back_keyboard()
        )
        return
    
    user_info['gpus'][gpu_id]['active'] = True
    user_info['active_gpus'] += 1
    
    update_user(user_id, {
        'gpus': user_info['gpus'],
        'active_gpus': user_info['active_gpus']
    })
    
    # После активации возвращаемся в меню управления
    await manage_gpus_activity(query, user_id)

async def deactivate_gpu(query, user_id, gpu_id):
    """Деактивировать видеокарту"""
    user_info = get_user_data(user_id)
    
    if gpu_id not in user_info.get('gpus', {}):
        await query.edit_message_text(
            "❌ Видеокарта не найдена!",
            reply_markup=get_back_keyboard()
        )
        return
    
    user_info['gpus'][gpu_id]['active'] = False
    user_info['active_gpus'] = max(0, user_info['active_gpus'] - 1)
    
    update_user(user_id, {
        'gpus': user_info['gpus'],
        'active_gpus': user_info['active_gpus']
    })
    
    # После деактивации возвращаемся в меню управления
    await manage_gpus_activity(query, user_id)
    
# ========== МАГАЗИН GPU ==========
async def show_gpu_shop(query, user_id):
    """Показать магазин видеокарт"""
    text = """
🛒 *Магазин видеокарт*

Выберите категорию видеокарт:

🟢 *Тир 1 (Самые слабые):* 1-100
Самые простые видеокарты для старта (5$-300$)

📱 *Тир 2 (Бюджетные):* 101-200
Бюджетные карты для развития фермы (300$-1000$)

⚡ *Тир 3 (Средние):* 201-300
Хорошее соотношение цена/качество (1000$-2500$)

💎 *Тир 4 (Хорошие):* 301-400
Мощные карты для серьезного майнинга (2500$-5000$)

🔥 *Тир 5 (Мощные):* 401-500
Профессиональные карты для больших ферм (5000$-10000$)

🚀 *Тир 6 (Топовые):* 501-600
Лучшие карты на рынке (10000$+)
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_gpu_shop_keyboard()
    )

async def show_gpu_tier(query, user_id, tier, page=0):
    """Показать видеокарты определенного тира с пагинацией"""
    tier = int(tier)
    tier_gpus = {k: v for k, v in GPUS.items() if v['tier'] == tier}
    
    if not tier_gpus:
        await query.edit_message_text(
            "❌ Нет видеокарт в этом тире!",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Получаем карты для текущей страницы
    sorted_gpus = sorted(tier_gpus.items(), key=lambda x: x[1]['cost'])
    start_idx = page * 10
    end_idx = start_idx + 10
    page_gpus = list(sorted_gpus)[start_idx:end_idx]
    
    tier_names = {
        1: "Самые слабые",
        2: "Бюджетные",
        3: "Средние",
        4: "Хорошие",
        5: "Мощные",
        6: "Топовые"
    }
    
    text = f"🛒 *Видеокарты: {tier_names[tier]}*\n"
    text += f"Страница {page + 1} из {len(sorted_gpus) // 10 + 1}\n\n"
    
    for i, (gpu_id, gpu_info) in enumerate(page_gpus, start_idx + 1):
        text += f"{gpu_info['icon']} *{gpu_info['name']}*\n"
        text += f"  ⛏ Хешрейт: {gpu_info['hashrate']} MH/s\n"
        text += f"  ⚡ Потребление: {gpu_info['power']} Вт\n"
        text += f"  🔥 Макс. темп.: {gpu_info['temp']}°C\n"
        text += f"  💰 Цена: {gpu_info['cost']}$\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_gpu_tier_keyboard(tier, page)
    )

async def buy_gpu(query, user_id, gpu_id):
    """Купить видеокарту"""
    if gpu_id not in GPUS:
        await query.edit_message_text(
            "❌ Такой видеокарты не существует!",
            reply_markup=get_back_keyboard()
        )
        return
    
    gpu_info = GPUS[gpu_id]
    user_info = get_user_data(user_id)
    
    if user_info['balance'] < gpu_info['cost']:
        await query.edit_message_text(
            f"❌ Недостаточно средств!\n"
            f"Нужно: {gpu_info['cost']}$\n"
            f"У вас: {user_info['balance']:.2f}$",
            reply_markup=get_back_keyboard()
        )
        return
    
    if user_info['active_gpus'] >= user_info['max_gpus']:
        await query.edit_message_text(
            f"❌ Достигнут лимит видеокарт!\n"
            f"Максимум: {user_info['max_gpus']}\n"
            f"У вас: {user_info['active_gpus']}\n\n"
            f"⚙️ Увеличьте слоты фермы в улучшениях!",
            reply_markup=get_back_keyboard()
        )
        return
    
    user_info['balance'] -= gpu_info['cost']
    
    # Проверяем, есть ли уже такая видеокарта
    if gpu_id not in user_info['gpus']:
        user_info['gpus'][gpu_id] = {
            'count': 1,
            'durability': 100,
            'active': True  # НОВОЕ: флаг активности
        }
        user_info['active_gpus'] += 1
    else:
        # Если карта уже есть, увеличиваем количество
        user_info['gpus'][gpu_id]['count'] += 1
        
        # Если карта была неактивна, активируем её
        if not user_info['gpus'][gpu_id].get('active', False):
            user_info['gpus'][gpu_id]['active'] = True
            user_info['active_gpus'] += 1
    
    # Деактивируем более слабые видеокарты
    deactivated_gpus = await deactivate_weaker_gpus(user_id, gpu_id)
    
    # Обновляем хешрейт
    total_hashrate = 5
    for gpu_id_inv, gpu_data in user_info['gpus'].items():
        if gpu_id_inv in GPUS and gpu_data.get('active', True):
            count = gpu_data.get('count', 0)
            durability = gpu_data.get('durability', 100)
            efficiency = durability / 100
            total_hashrate += GPUS[gpu_id_inv]['hashrate'] * count * efficiency
    
    user_info['hashrate'] = total_hashrate
    
    update_user(user_id, {
        'balance': user_info['balance'],
        'gpus': user_info['gpus'],
        'active_gpus': user_info['active_gpus'],
        'hashrate': user_info['hashrate']
    })
    
    log_transaction(user_id, user_info['username'], "BUY_GPU", -gpu_info['cost'], 
                   f"GPU: {gpu_info['name']}")
    
    text = f"""
✅ *Видеокарта куплена!*

{gpu_info['icon']} *{gpu_info['name']}*
💰 Стоимость: {gpu_info['cost']}$
⛏ +{gpu_info['hashrate']} MH/s к хешрейту

💎 Новый баланс: {user_info['balance']:.2f}$
🖥 Всего видеокарт: {user_info['active_gpus']}/{user_info['max_gpus']}
"""
    
    # Показываем деактивированные карты
    if deactivated_gpus:
        text += f"\n⚠️ *Автоматически деактивированы более слабые карты:*"
        for gpu_id_deact, gpu_data in deactivated_gpus:
            gpu_name = GPUS.get(gpu_id_deact, {}).get('name', 'Неизвестная')
            text += f"\n• {gpu_name}"
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== УЛУЧШЕНИЯ ==========
async def show_upgrades(query, user_id):
    """Показать улучшения"""
    user_info = get_user_data(user_id)
    
    text = "⚙️ *Улучшения фермы*\n\n"
    text += f"💰 Ваш баланс: *{user_info['balance']:.2f}* $\n\n"
    
    text += "*Доступные улучшения:*\n\n"
    
    # Кулеры
    text += "❄️ *Кулеры (макс. температура):*\n"
    for i in range(1, 51):
        upgrade_id = f'cooling_{i}'
        if upgrade_id in UPGRADES:
            upgrade = UPGRADES[upgrade_id]
            purchased = user_info['upgrades'].get(upgrade_id, False)
            status = "✅ Куплено" if purchased else f"🛒 {upgrade['price']}$"
            text += f"{upgrade['name']}: {status}\n"
    
    text += "\n⚡ *Блоки питания (энергия):*\n"
    for i in range(1, 51):
        upgrade_id = f'energy_{i}'
        if upgrade_id in UPGRADES:
            upgrade = UPGRADES[upgrade_id]
            purchased = user_info['upgrades'].get(upgrade_id, False)
            status = "✅ Куплено" if purchased else f"🛒 {upgrade['price']}$"
            text += f"{upgrade['name']}: {status}\n"
    
    text += "\n🌊 *Водяное охлаждение:*\n"
    for i in range(1, 11):
        upgrade_id = f'water_cooling_{i}'
        if upgrade_id in UPGRADES:
            upgrade = UPGRADES[upgrade_id]
            purchased = user_info['upgrades'].get(upgrade_id, False)
            status = "✅ Куплено" if purchased else f"🛒 {upgrade['price']}$"
            text += f"{upgrade['name']}: {status}\n"
    
    text += "\n🏭 *Слоты фермы:*\n"
    for i in range(1, 6):
        upgrade_id = f'farm_{i}'
        if upgrade_id in UPGRADES:
            upgrade = UPGRADES[upgrade_id]
            purchased = user_info['upgrades'].get(upgrade_id, False)
            status = "✅ Куплено" if purchased else f"🛒 {upgrade['price']}$"
            text += f"{upgrade['name']}: {status}\n"
    
    keyboard = [
        [InlineKeyboardButton("❄️ Купить кулер", callback_data='buy_cooling_menu'),
         InlineKeyboardButton("⚡ Купить БП", callback_data='buy_energy_menu')],
        [InlineKeyboardButton("🌊 Вод. охлаждение", callback_data='buy_water_cooling_menu'),
         InlineKeyboardButton("🏭 Слоты фермы", callback_data='buy_farm_menu')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_upgrade_menu(query, user_id, upgrade_type):
    """Меню покупки улучшений по категориям"""
    user_info = get_user_data(user_id)
    
    if upgrade_type == 'cooling':
        text = "❄️ *Купить кулер*\n\n"
        for i in range(1, 51):
            upgrade_id = f'cooling_{i}'
            if upgrade_id in UPGRADES:
                upgrade = UPGRADES[upgrade_id]
                purchased = user_info['upgrades'].get(upgrade_id, False)
                if not purchased:
                    text += f"{upgrade['name']} - {upgrade['price']}$\n"
        
        keyboard = [[InlineKeyboardButton(f"Купить Level {i}", callback_data=f'buy_upgrade_cooling_{i}')] for i in range(1, 11)]
    
    elif upgrade_type == 'energy':
        text = "⚡ *Купить блок питания*\n\n"
        for i in range(1, 51):
            upgrade_id = f'energy_{i}'
            if upgrade_id in UPGRADES:
                upgrade = UPGRADES[upgrade_id]
                purchased = user_info['upgrades'].get(upgrade_id, False)
                if not purchased:
                    text += f"{upgrade['name']} - {upgrade['price']}$\n"
        
        keyboard = [[InlineKeyboardButton(f"Купить Level {i}", callback_data=f'buy_upgrade_energy_{i}')] for i in range(1, 11)]
    
    elif upgrade_type == 'water_cooling':
        text = "🌊 *Купить водяное охлаждение*\n\n"
        for i in range(1, 11):
            upgrade_id = f'water_cooling_{i}'
            if upgrade_id in UPGRADES:
                upgrade = UPGRADES[upgrade_id]
                purchased = user_info['upgrades'].get(upgrade_id, False)
                if not purchased:
                    text += f"{upgrade['name']} - {upgrade['price']}$\n"
        
        keyboard = [[InlineKeyboardButton(f"Купить {UPGRADES[f'water_cooling_{i}']['name']}", callback_data=f'buy_upgrade_water_{i}')] for i in range(1, 11)]
    
    elif upgrade_type == 'farm':
        text = "🏭 *Купить слоты фермы*\n\n"
        for i in range(1, 6):
            upgrade_id = f'farm_{i}'
            if upgrade_id in UPGRADES:
                upgrade = UPGRADES[upgrade_id]
                purchased = user_info['upgrades'].get(upgrade_id, False)
                if not purchased:
                    text += f"{upgrade['name']} - {upgrade['price']}$\n"
        
        keyboard = [[InlineKeyboardButton(f"Купить Level {i}", callback_data=f'buy_upgrade_farm_{i}')] for i in range(1, 6)]
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='upgrades')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_upgrade(query, user_id, upgrade_type, level):
    """Купить улучшение"""
    upgrade_id = f"{upgrade_type}_{level}"
    
    if upgrade_id not in UPGRADES:
        await query.edit_message_text(
            "❌ Такого улучшения не существует!",
            reply_markup=get_back_keyboard()
        )
        return
    
    upgrade = UPGRADES[upgrade_id]
    user_info = get_user_data(user_id)
    
    if user_info['upgrades'].get(upgrade_id, False):
        await query.edit_message_text(
            f"❌ У вас уже куплено это улучшение!",
            reply_markup=get_back_keyboard()
        )
        return
    
    if user_info['balance'] < upgrade['price']:
        await query.edit_message_text(
            f"❌ Недостаточно средств!\n"
            f"Нужно: {upgrade['price']}$\n"
            f"У вас: {user_info['balance']:.2f}$",
            reply_markup=get_back_keyboard()
        )
        return
    
    user_info['balance'] -= upgrade['price']
    user_info['upgrades'][upgrade_id] = True
    
    # Применяем эффект улучшения
    if upgrade['type'] == 'cooling':
        temp_bonus = int(upgrade['effect'].split('_')[-1])
        user_info['max_temperature'] += temp_bonus
    
    elif upgrade['type'] == 'energy':
        energy_bonus = int(upgrade['effect'].split('_')[-1])
        user_info['max_energy'] += energy_bonus
    
    elif upgrade['type'] == 'water_cooling':
        temp_bonus = int(upgrade['effect'].split('_')[-1])
        user_info['max_temperature'] += temp_bonus
    
    elif upgrade['type'] == 'farm':
        gpu_bonus = int(upgrade['effect'].split('_')[-1])
        user_info['max_gpus'] += gpu_bonus
    
    update_user(user_id, {
        'balance': user_info['balance'],
        'upgrades': user_info['upgrades'],
        'max_temperature': user_info.get('max_temperature', 100),
        'max_energy': user_info.get('max_energy', 1500),
        'max_gpus': user_info.get('max_gpus', 1)
    })
    
    log_transaction(user_id, user_info['username'], "BUY_UPGRADE", -upgrade['price'], 
                   f"Улучшение: {upgrade['name']}")
    
    await query.edit_message_text(
        f"✅ *Улучшение куплено!*\n\n"
        f"{upgrade['name']}\n"
        f"💰 Стоимость: {upgrade['price']}$\n"
        f"⚡ Эффект: {upgrade['effect']}\n\n"
        f"💎 Новый баланс: {user_info['balance']:.2f}$",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== ЭНЕРГИЯ ==========
async def show_energy(query, user_id):
    """Показать энергию"""
    user_info = get_user_data(user_id)
    
    # Восстановление энергии
    last_mining = datetime.fromisoformat(user_info['last_mining'])
    now = datetime.now()
    minutes_passed = (now - last_mining).total_seconds() / 60
    energy_regen = int(minutes_passed * 2)
    
    if energy_regen > 0:
        user_info['energy'] = min(user_info['max_energy'], user_info['energy'] + energy_regen)
        user_info['last_mining'] = now.isoformat()
        update_user(user_id, {
            'energy': user_info['energy'],
            'last_mining': user_info['last_mining']
        })
    
    text = f"""
⚡ *Энергия фермы*

🔋 *Текущая энергия:* {user_info['energy']:.0f}/{user_info['max_energy']} кВт
📊 *Заполнение:* {(user_info['energy']/user_info['max_energy']*100):.1f}%

🔄 *Восстановление:* 2 кВт/минуту
⏳ *До полной зарядки:* {(user_info['max_energy'] - user_info['energy']) / 2:.0f} мин

💡 *Что делать при нехватке энергии:*
1. Подождать восстановления (2 кВт/мин)
2. Купить энергию за Telegram Stars
3. Улучшить блок питания
4. Использовать бустер энергии
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_energy_keyboard()
    )

async def buy_energy_stars(query, user_id):
    """Купить энергию за Telegram Stars"""
    user_info = get_user_data(user_id)
    
    text = f"""
⚡ *Покупка энергии за Telegram Stars*

У вас недостаточно энергии для майнинга.

📊 *Текущая энергия:* {user_info['energy']:.0f}/{user_info['max_energy']} кВт

💎 *Варианты покупки:*
1. 1000 кВт - 15 руб (Telegram Stars)
2. 5000 кВт - 70 руб (Telegram Stars) 
3. 10000 кВт - 130 руб (Telegram Stars)
4. 50000 кВт - 600 руб (Telegram Stars)

📱 *Как купить:*
1. Напишите менеджеру @HomsyAdmin
2. Укажите ваш ID: `{user_id}`
3. Укажите сколько энергии хотите купить
4. Оплатите через Telegram Stars

После оплаты энергия будет добавлена автоматически.

⏱️ Обычно доставка занимает 1-15 минут.
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("⚡ Продолжить майнинг", callback_data='mine'),
         InlineKeyboardButton("🔙 Назад", callback_data='energy')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== РЕФЕРАЛЫ ==========
async def show_referrals(query, user_id):
    """Показать рефералов"""
    user_info = get_user_data(user_id)
    
    ref_link = f"https://t.me/{BOT_USERNAME[1:]}?start=ref{user_id}"
    
    text = f"""
👥 *Реферальная система*

📊 *Ваша статистика:*
👥 Приглашено: *{len(user_info.get('referrals', []))}*
✅ Подписались на каналы: *{len(user_info.get('referrals_subscribed', []))}*
💰 Заработано $: *{user_info.get('ref_earned', 0):.2f}* $
🇷🇺 Заработано ₽: *{user_info.get('ref_rub_earned', 0):.2f}* ₽
💎 Текущий баланс $: *{user_info['balance']:.2f}* $
🇷🇺 Текущий баланс ₽: *{user_info.get('rub_balance', 0):.2f}* ₽

🔗 *Ваша реферальная ссылка:*
{ref_link}

🎁 *Бонусы за приглашение:*
• 25$ вам за регистрацию по вашей ссылке
• 50$ вашему рефереру
• *0.50₽ за каждого реферала, который подпишется на каналы*
• 5% от дохода рефералов навсегда!

💰 *Вывод рублей:*
• Минимальная сумма: 50₽
• На карты российских банков
• Для вывода пиши @HomsyAdmin

📱 *Как приглашать:*
1. Отправьте друзьям вашу ссылку
2. Они должны нажать на ссылку и начать играть
3. Они должны подписаться на каналы
4. Вы получаете 0.50₽ автоматически!
"""
    
    keyboard = [
        [InlineKeyboardButton("📢 Поделиться", url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся к Mine Evo Ultra! Зарабатывай криптовалюту и рубли! За подписку на каналы - 0.50₽ для пригласившего!")],
        [InlineKeyboardButton("💰 Вывод рублей", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
        [InlineKeyboardButton("👥 Мои рефералы", callback_data='my_referrals'),
         InlineKeyboardButton("📊 Топ рефереров", callback_data='top_referrals')],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_my_referrals(query, user_id):
    """Показать моих рефералов"""
    user_info = get_user_data(user_id)
    referrals = user_info.get('referrals', [])
    
    if not referrals:
        await query.edit_message_text(
            "👥 *Мои рефералы*\n\n"
            "❌ У вас еще нет рефералов.\n"
            "💡 Пригласите друзей по реферальной ссылке!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_back_keyboard()
        )
        return
    
    text = "👥 *Мои рефералы*\n\n"
    
    total_earned = 0
    for i, ref_id in enumerate(referrals[:50], 1):  # Ограничим 50 рефералов
        ref_info = get_user_data(ref_id)
        username = ref_info['username']
        if username.startswith('user_'):
            username = f"Игрок {str(ref_id)[-4:]}"
        
        earned_from_ref = ref_info.get('total_mined', 0) * 0.05
        total_earned += earned_from_ref
        
        text += f"{i}. @{username}\n"
        text += f"   💰 Заработал: {ref_info.get('total_mined', 0):.2f}$\n"
        text += f"   🎁 Мой доход: {earned_from_ref:.2f}$\n\n"
    
    if len(referrals) > 50:
        text += f"... и еще {len(referrals) - 50} рефералов\n\n"
    
    text += f"📊 *Итого:*\n"
    text += f"👥 Всего рефералов: {len(referrals)}\n"
    text += f"💰 Общий доход: {total_earned:.2f}$\n"
    text += f"🎁 Получено бонусов: {user_info.get('ref_earned', 0):.2f}$"
    
    keyboard = [
        [InlineKeyboardButton("🔗 Реф. ссылка", callback_data='referrals'),
         InlineKeyboardButton("📢 Поделиться", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME[1:]}?start=ref{user_id}&text=Присоединяйся к Mine Evo Ultra!")],
        [InlineKeyboardButton("🔙 Назад", callback_data='referrals')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== ПРОМОКОДЫ ==========
async def show_promo(query, user_id):
    """Показать промокоды"""
    user_info = get_user_data(user_id)
    
    text = """
🎁 *Промокоды*

✨ *Как получить промокоды:*
• Следите за нашим каналом @MineEvoUltra
• Участвуйте в конкурсах в чате @MineEvoUltraChat
• Следите за партнерскими розыгрышами

📝 *Как активировать:*
1. Введите промокод в чат
2. Нажмите отправить
3. Получите бонус!

💰 *Ваши использованные промокоды:* {}/{}
""".format(len(user_info.get('promocodes_used', [])), len(promocodes))
    
    keyboard = [
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/MineEvoUltra")],
        [InlineKeyboardButton("💬 Наш чат", url="https://t.me/MineEvoUltraChat")],
        [InlineKeyboardButton("🎮 Проверить код", callback_data='check_promo'),
         InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_promo(query, user_id):
    """Проверить промокод"""
    user_states[user_id] = 'enter_promo'
    await query.edit_message_text(
        "🎁 *Введите промокод:*\n\n"
        "Просто отправьте промокод в чат.\n"
        "Пример: `START2024`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )

async def activate_promo(user_id, promo_code, context):
    """Активировать промокод"""
    promo_code = promo_code.upper()
    user_info = get_user_data(user_id)
    
    # Проверяем существование промокода
    if promo_code in promocodes:
        promo = promocodes[promo_code]
        
        # Проверяем лимит использований
        if promo['used'] >= promo['max_uses']:
            return False, "❌ Промокод закончился!"
        
        # Проверяем, не использовал ли уже пользователь этот промокод
        if str(user_id) in promo.get('users', []):
            return False, "❌ Вы уже использовали этот промокод!"
        
        # Выдаем награду
        amount = promo['amount']
        user_info['balance'] += amount
        user_info['total_earned'] += amount
        
        # Добавляем в использованные
        if 'promocodes_used' not in user_info:
            user_info['promocodes_used'] = []
        user_info['promocodes_used'].append(promo_code)
        
        # Обновляем статистику промокода
        promo['used'] += 1
        if 'users' not in promo:
            promo['users'] = []
        promo['users'].append(str(user_id))
        
        update_user(user_id, {
            'balance': user_info['balance'],
            'total_earned': user_info['total_earned'],
            'promocodes_used': user_info['promocodes_used']
        })
        
        save_data()
        
        log_transaction(user_id, user_info['username'], "PROMO_ACTIVATE", amount, 
                       f"Промокод: {promo_code}")
        
        return True, f"✅ Промокод активирован!\n🎁 Получено: {amount}$\n💰 Новый баланс: {user_info['balance']:.2f}$"
    
    return False, "❌ Неверный промокод!"

# ========== УСЛУГИ ==========
async def show_services(query, user_id):
    """Показать раздел Услуги"""
    user_info = get_user_data(user_id)
    
    text = f"""
🛒 *Услуги и улучшения*

💰 Ваш баланс: *{user_info['balance']:.2f}* $

Выберите категорию:

🚀 *Бустеры* - временные усиления
⚜️ *Статусы* - постоянные бонусы
🎨 *Скины* - оформление фермы
🛡️ *Защита* - защита от атак

💎 *Популярные услуги:*
• Бустер энергии: +20% к восстановлению
• Алмазный статус: +100 MH/s навсегда
• Защита фермы: иммунитет к атакам

📱 *Все услуги покупаются через менеджера @HomsyAdmin*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_services_keyboard()
    )

async def show_boosters(query, user_id):
    """Показать бустеры"""
    text = """
🚀 *Бустеры*

Бустеры - временные усиления для вашей фермы.

🎯 *Доступные бустеры:*

❄️ *Бустер охлаждения*
Снижает температуру на 15°
💰 Цена: 0.30$ (25₽)
⏱ Длительность: 24 часа

⚡ *Бустер энергии*
Увеличивает восстановление энергии на 20%
💰 Цена: 0.30$ (25₽)
⏱ Длительность: 24 часа

🚀 *Комбо-бустер*
Охлаждение +15° и энергия +30%
💰 Цена: 0.60$ (50₽)
⏱ Длительность: 24 часа

💡 *Как работают бустеры:*
1. Покупаете бустер
2. Он автоматически активируется
3. Получаете бонусы на 24 часа
4. Можно использовать несколько бустеров

📱 *Для покупки напишите менеджеру @HomsyAdmin*
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='services')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_statuses(query, user_id):
    """Показать статусы"""
    text = """
⚜️ *Статусы майнера*

Статусы - постоянные бонусы к хешрейту.

🏆 *Доступные статусы:*

⚜️ *Начинающий майнер*
+10 MH/s к хешрейту
💰 Цена: 1.20$ (99₽)

⚜️ *Монетный майнер*
+25 MH/s к хешрейту
💰 Цена: 2.40$ (199₽)

⚜️ *Долларовый майнер*
+50 MH/s к хешрейту
💰 Цена: 4.20$ (349₽)

⚜️ *Золотой майнер*
+75 MH/s к хешрейту
💰 Цена: 6.00$ (499₽)

💎 *Алмазный майнер*
+100 MH/s к хешрейту
💰 Цена: 7.80$ (649₽)

💠 *Сапфировый майнер*
+200 MH/s к хешрейту
💰 Цена: 15.60$ (1299₽)

💡 *Особенности статусов:*
• Действуют навсегда
• Не суммируются (активен высший)
• Увеличивают базовый хешрейт
• Видны другим игрокам

📱 *Для покупки напишите менеджеру @HomsyAdmin*
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='services')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_skins(query, user_id):
    """Показать скины"""
    user_info = get_user_data(user_id)
    
    text = """
🎨 *Скины для фермы*

Измените внешний вид вашей фермы!

🌈 *Доступные скины:*

🎮 *Геймерский скин*
Стиль киберпанк с неоновыми цветами
💰 Цена: 2.50$ (200₽)

🏆 *Золотой скин*
Роскошное золотое оформление
💰 Цена: 5.00$ (400₽)

💎 *Алмазный скин*
Сверкающие бриллианты и кристаллы
💰 Цена: 10.00$ (800₽)

👾 *Хакерский скин*
Зеленый текст на черном фоне
💰 Цена: 3.00$ (240₽)

🚀 *Космический скин*
Тема космоса и звезд
💰 Цена: 4.00$ (320₽)

💡 *Особенности скинов:*
• Меняют внешний вид фермы
• Действуют навсегда
• Можно переключать
• Видны при атаках
"""
    
    if user_info.get('skins'):
        text += f"\n✅ *Ваши скины:*\n"
        for skin_id, skin_name in user_info['skins'].items():
            text += f"• {skin_name}\n"
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='services')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_service(query, user_id, service_id):
    """Купить услугу - направление к менеджеру"""
    if service_id not in SERVICES:
        await query.edit_message_text(
            "❌ Такой услуги не существует!",
            reply_markup=get_back_keyboard()
        )
        return
    
    service = SERVICES[service_id]
    
    text = f"""
🛒 *Покупка услуги*

{service['name']}
💰 Цена: {service['usd_price']}$ ({service['rub_price']}₽)

📱 *Как купить:*
1. Напишите менеджеру @HomsyAdmin
2. Укажите ваш ID: `{user_id}`
3. Укажите услугу: "{service['name']}"
4. Оплатите через Telegram Stars

После оплаты услуга будет активирована автоматически.

⏱️ Обычно активация занимает 1-15 минут.
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='services')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_skin(query, user_id, skin_id):
    """Купить скин - направление к менеджеру"""
    skin_prices = {
        'gamer': 2.50,
        'gold': 5.00,
        'diamond': 10.00,
        'hacker': 3.00,
        'space': 4.00
    }
    
    skin_names = {
        'gamer': '🎮 Геймерский скин',
        'gold': '🏆 Золотой скин',
        'diamond': '💎 Алмазный скин',
        'hacker': '👾 Хакерский скин',
        'space': '🚀 Космический скин'
    }
    
    if skin_id not in skin_prices:
        await query.edit_message_text(
            "❌ Такого скина не существует!",
            reply_markup=get_back_keyboard()
        )
        return
    
    price = skin_prices[skin_id]
    skin_name = skin_names[skin_id]
    
    text = f"""
🎨 *Покупка скина*

{skin_name}
💰 Цена: {price}$ ({int(price*80)}₽)

📱 *Как купить:*
1. Напишите менеджеру @HomsyAdmin
2. Укажите ваш ID: `{user_id}`
3. Укажите скин: "{skin_name}"
4. Оплатите через Telegram Stars

После оплаты скин будет активирован автоматически.

⏱️ Обычно активация занимает 1-15 минут.
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='services_skins')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== ПОДДЕРЖКА ==========
async def show_support(query, user_id):
    """Показать поддержку"""
    text = """
*🆘 ПОДДЕРЖКА*

*💬 Связаться с нами:*
• Менеджер: @HomsyAdmin
• Канал: @MineEvoUltra  
• Чат: @MineEvoUltraChat
• Бот: @MineEvoUltra_bot

*🕒 Время работы поддержки:*
Понедельник - Воскресенье
10:00 - 22:00 (МСК)

*📋 Частые вопросы:*
1. *Как начать майнить?*
   Купите видеокарту и нажмите "Майнить"

2. *Как купить услуги?*
   Напишите менеджеру @HomsyAdmin

3. *Не работает бот?*
   Перезапустите бота командой /start

4. *Как пригласить друзей?*
   Используйте реферальную ссылку

5. *Как купить энергию?*
   Напишите менеджеру @HomsyAdmin

*🚀 Быстрая помощь:*
Выберите действие ниже:
"""
    
    keyboard = [
        [InlineKeyboardButton("📝 Создать тикет", callback_data='create_ticket')],
        [InlineKeyboardButton("📋 Мои тикеты", callback_data='my_tickets')],
        [InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== ФУНКЦИЯ ПОМОЩИ ==========
async def show_help(query, user_id):
    """Показать помощь"""
    text = """
ℹ️ ПОМОЩЬ ПО БОТУ MINE EVO ULTRA

📖 ОСНОВНЫЕ КОМАНДЫ:
/start - Начать игру
/menu - Главное меню
/profile - Ваш профиль

🎮 ОСНОВНЫЕ ДЕЙСТВИЯ:
⛏️ Майнить - начать майнинг криптовалюты
🖥 Мои GPU - посмотреть ваши видеокарты
🛒 Магазин GPU - купить новые видеокарты
⚙️ Улучшения - улучшить ферму
⚡️ Энергия - управление энергией фермы
🛡 Защита - защитить ферму от атак
🗡 Атаковать - атаковать других игроков
🔧 Ремонт - отремонтировать видеокарты

💰 ЭКОНОМИКА:
💰 Баланс - ваш текущий баланс в долларах
🇷🇺 Баланс в рублях - ваш баланс в рублях
📊 Статистика - подробная статистика
👥 Рефералы - пригласить друзей и получить бонусы
🎁 Промокод - активировать промокод

📢 НАШИ РЕСУРСЫ:
📢 Канал: @MineEvoUltra
💬 Чат: @MineEvoUltraChat
🤖 Бот: @MineEvoUltra_bot
👨‍💼 Поддержка: @HomsyAdmin

💡 СОВЕТЫ ДЛЯ НОВИЧКОВ:
1. Начните с покупки дешевых видеокарт
2. Регулярно майните для заработка
3. Приглашайте друзей по реферальной ссылке
4. Участвуйте в ивентах для бонусов
5. Защищайте ферму от атак

💎 УДАЧИ В МАЙНИНГЕ!
"""
    
    keyboard = [
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/MineEvoUltra")],
        [InlineKeyboardButton("💬 Наш чат", url="https://t.me/MineEvoUltraChat")],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=None,  # ← ОТКЛЮЧИТЕ MARKDOWN
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_support(query, user_id):
    """Показать поддержку"""
    text = """
🆘 ПОДДЕРЖКА

💬 СВЯЗАТЬСЯ С НАМИ:
• Менеджер: @HomsyAdmin
• Канал: @MineEvoUltra
• Чат: @MineEvoUltraChat
• Бот: @MineEvoUltra_bot

🕒 ВРЕМЯ РАБОТЫ ПОДДЕРЖКИ:
Понедельник - Воскресенье
10:00 - 22:00 (МСК)

🚀 БЫСТРАЯ ПОМОЩЬ:
Выберите действие ниже:
"""
    
    keyboard = [
        [InlineKeyboardButton("📝 Создать тикет", callback_data='create_ticket')],
        [InlineKeyboardButton("📋 Мои тикеты", callback_data='my_tickets')],
        [InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=None,  # ← ОТКЛЮЧИТЕ MARKDOWN
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
async def create_ticket(query, user_id):
    """Создать тикет"""
    user_states[user_id] = 'create_ticket'
    
    await query.edit_message_text(
        "📝 *Создание тикета*\n\n"
        "Опишите вашу проблему или вопрос:\n"
        "• Что произошло?\n"
        "• Как воспроизвести проблему?\n"
        "• Что вы уже пробовали?\n\n"
        "⚠️ *Правила:*\n"
        "1. Будьте вежливы\n"
        "2. Описывайте проблему подробно\n"
        "3. Приложите скриншоты если нужно\n\n"
        "Просто отправьте сообщение с описанием проблемы.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard()
    )

async def show_my_tickets(query, user_id):
    """Показать мои тикеты"""
    user_tickets = []
    for ticket_id, ticket in support_tickets.items():
        if ticket.get('user_id') == user_id:
            user_tickets.append((ticket_id, ticket))
    
    if not user_tickets:
        await query.edit_message_text(
            "📋 *Мои тикеты*\n\n"
            "❌ У вас нет созданных тикетов.\n\n"
            "💡 Создайте тикет если у вас есть вопросы или проблемы!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_support_keyboard()
        )
        return
    
    text = "📋 *Мои тикеты*\n\n"
    
    for ticket_id, ticket in user_tickets[:10]:  # Ограничим 10 тикетов
        status = ticket.get('status', 'open')
        status_icon = "🟢" if status == 'open' else "🟡" if status == 'in_progress' else "🔴" if status == 'closed' else "⚪"
        
        created = datetime.fromisoformat(ticket['created'])
        text += f"{status_icon} *Тикет #{ticket_id}*\n"
        text += f"📝 Тема: {ticket.get('subject', 'Без темы')}\n"
        text += f"📊 Статус: {status}\n"
        text += f"📅 Создан: {created.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if len(user_tickets) > 10:
        text += f"... и еще {len(user_tickets) - 10} тикетов\n\n"
    
    keyboard = [
        [InlineKeyboardButton("📝 Новый тикет", callback_data='create_ticket')],
        [InlineKeyboardButton("💬 Чат с менеджером", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
        [InlineKeyboardButton("🔙 Назад", callback_data='support')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== ЗАЩИТА ФЕРМЫ ==========
def is_farm_protected(user_info):
    """Проверяет, активна ли защита фермы"""
    if not user_info.get('farm_protection'):
        return False
    
    protection_end = datetime.fromisoformat(user_info['farm_protection'])
    return protection_end > datetime.now()

async def show_protection_menu(query, user_id):
    """Показывает меню защиты фермы"""
    user_info = get_user_data(user_id)
    
    text = f"""
🛡️ *Защита фермы*

Защитите свою ферму от атак других игроков.
"""
    
    if is_farm_protected(user_info):
        protection_end = datetime.fromisoformat(user_info['farm_protection'])
        time_left = protection_end - datetime.now()
        hours_left = time_left.total_seconds() / 3600
        text += f"\n✅ *Активная защита:*\n"
        text += f"⏱️ Осталось: {hours_left:.1f} часов\n"
        text += f"🕒 Истекает: {protection_end.strftime('%d.%m.%Y %H:%M')}\n"
    else:
        text += "\n❌ *Защита не активна*\n"
    
    text += f"""
💰 *Доступные планы:*
"""
    
    for plan_id, plan in PROTECTION_PLANS.items():
        text += f"\n{plan['name']} - {plan['price']} {'$' if plan['price_type'] == 'balance' else '⭐'} ({plan['duration']}ч)"
    
    keyboard = []
    for plan_id, plan in PROTECTION_PLANS.items():
        keyboard.append([InlineKeyboardButton(
            f"{plan['name']} - {plan['price']}{'$' if plan['price_type'] == 'balance' else '⭐'}",
            callback_data=f'buy_protection_{plan_id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_protection(query, user_id, plan_id):
    """Покупка защиты фермы"""
    if plan_id not in PROTECTION_PLANS:
        await query.edit_message_text(
            "❌ Такого плана защиты не существует!",
            reply_markup=get_back_keyboard()
        )
        return
    
    plan = PROTECTION_PLANS[plan_id]
    user_info = get_user_data(user_id)
    
    if is_farm_protected(user_info):
        protection_end = datetime.fromisoformat(user_info['farm_protection'])
        if protection_end > datetime.now():
            await query.edit_message_text(
                f"❌ У вас уже есть активная защита!\n"
                f"Действует до: {protection_end.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=get_back_keyboard()
            )
            return
    
    if plan['price_type'] == 'balance':
        if user_info['balance'] < plan['price']:
            await query.edit_message_text(
                f"❌ Недостаточно средств!\nНужно: {plan['price']}$\nУ вас: {user_info['balance']:.2f}$",
                reply_markup=get_back_keyboard()
            )
            return
        
        user_info['balance'] -= plan['price']
        payment_method = 'balance'
        
    else:  # stars
        await handle_stars_payment_for_protection(query, user_id, plan_id)
        return
    
    protection_end = datetime.now() + timedelta(hours=plan['duration'])
    user_info['farm_protection'] = protection_end.isoformat()
    
    if 'protection_plans' not in user_info:
        user_info['protection_plans'] = {}
    user_info['protection_plans'][plan_id] = {
        'bought': datetime.now().isoformat(),
        'expires': protection_end.isoformat()
    }
    
    update_user(user_id, {
        'balance': user_info['balance'],
        'farm_protection': user_info['farm_protection'],
        'protection_plans': user_info['protection_plans']
    })
    
    log_transaction(user_id, user_info['username'], "BUY_PROTECTION", -plan['price'], 
                   f"План: {plan['name']}")
    
    text = f"""
✅ *Защита фермы активирована!*

{plan['name']}
🛡️ Защита действует до: {protection_end.strftime('%d.%m.%Y %H:%M')}
💰 Списано: {plan['price']}{'$' if plan['price_type'] == 'balance' else ' Stars'}

*Ваша ферма теперь защищена от атак других игроков!*
"""
    
    keyboard = [
        [InlineKeyboardButton("🎮 В игру", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_stars_payment_for_protection(query, user_id, plan_id):
    """Оплата защиты через Telegram Stars"""
    plan = PROTECTION_PLANS[plan_id]
    
    text = f"""
⭐ *Оплата защиты через Telegram Stars*

{plan['name']}
💰 Цена: *{plan['price']} Stars* ({plan['price']} руб)

📱 *Инструкция:*
1. Напишите менеджеру @HomsyAdmin
2. Отправьте ему {plan['price']} Stars
3. Укажите ваш ID: `{user_id}`
4. Укажите услугу: "Защита фермы {plan['name']}"

После подтверждения оплаты защита будет активирована.

⏱️ Обычно активация занимает 1-15 минут.
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Написать менеджеру", url="https://t.me/HomsyAdmin")],
        [InlineKeyboardButton("❌ Отмена", callback_data='protection_menu')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== PVP СИСТЕМА ==========
async def get_attackable_players(attacker_id):
    """Возвращает список игроков, которых можно атаковать"""
    attacker_id_str = str(attacker_id)
    attackable_players = []
    
    attacker_data = get_user_data(attacker_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if attacker_data.get('pvp_attacks_date') != today:
        attacker_data['pvp_attacks_today'] = 0
        attacker_data['pvp_attacks_date'] = today
        update_user(attacker_id, {
            'pvp_attacks_today': 0,
            'pvp_attacks_date': today
        })
    
    for user_id_str, user_info in user_data.items():
        if user_id_str == attacker_id_str:
            continue
        
        # Админов нельзя атаковать
        if int(user_id_str) in ADMIN_IDS:
            continue
        
        # Не атакуем игроков с защитой
        if is_farm_protected(user_info):
            continue
        
        # Проверяем время последней атаки
        last_attacked = user_info.get('last_attacked')
        if last_attacked:
            last_time = datetime.fromisoformat(last_attacked)
            if (datetime.now() - last_time).total_seconds() < 3600:
                continue
        
        # Не показываем игроков с нулевым балансом (по желанию)
        if user_info.get('balance', 0) <= 0:
            continue
        
        attackable_players.append({
            'user_id': int(user_id_str),
            'username': user_info.get('username', f'Игрок_{user_id_str}'),
            'balance': user_info.get('balance', 0),
            'hashrate': user_info.get('hashrate', 0),
            'active_gpus': user_info.get('active_gpus', 0),
            'total_mined': user_info.get('total_mined', 0)
        })
    
    # Сортируем по балансу (самые богатые сверху)
    attackable_players.sort(key=lambda x: x['balance'], reverse=True)
    return attackable_players

def calculate_online_minutes(user_info):
    """Вычисляет сколько минут игрок онлайн"""
    if not user_info.get('last_mining'):
        return 0
    
    last_mining = datetime.fromisoformat(user_info['last_mining'])
    now = datetime.now()
    minutes = (now - last_mining).total_seconds() / 60
    
    return min(60, minutes)

async def show_pvp_menu(query, user_id):
    """Показывает меню PvP атак"""
    user_info = get_user_data(user_id)
    attackable_players = await get_attackable_players(user_id)
    
    attacks_left = max(0, 5 - user_info.get('pvp_attacks_today', 0))
    
    text = f"""
🗡 *АТАКА ДРУГИХ ИГРОКОВ*

🎯 *Ваша статистика:*
• Атак сегодня: {user_info.get('pvp_attacks_today', 0)}/5
• Успешных атак: {user_info.get('pvp_success', 0)}
• Украдено всего: {user_info.get('pvp_total_stolen', 0):.2f}$

💡 *Правила атак:*
1. Можно атаковать только игроков без защиты
2. Максимум 5 атак в день
3. За успешную атаку получаете 5% баланса жертвы
4. Наносите урон видеокартам врагам
5. После атаки игрок получает 1 час иммунитета

🎯 *Доступные цели ({len(attackable_players)}):*
"""
    
    if attacks_left <= 0:
        text += f"\n❌ *Лимит атак исчерпан!*\nПопробуйте завтра."
    
    keyboard = []
    
    if attacks_left > 0 and attackable_players:
        for i, target in enumerate(attackable_players[:10], 1):
            display_name = target['username'] if not target['username'].startswith('user_') else f"Игрок {str(target['user_id'])[-4:]}"
            keyboard.append([InlineKeyboardButton(
                f"{i}. {display_name} - {target['balance']:.0f}$",
                callback_data=f'pvp_info_{target["user_id"]}'
            )])
    else:
        text += "\n\n❌ *Нет доступных целей для атаки!*"
    
    keyboard.append([InlineKeyboardButton("🔄 Обновить список", callback_data='pvp_menu')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
async def show_target_info(query, user_id, target_id):
    """Показывает статистику цели для атаки"""
    try:
        attacker_info = get_user_data(user_id)
        target_info = get_user_data(target_id)
        
        can_attack, reason = await can_attack_player(user_id, target_id)
        
        # Используем простой текст без сложного форматирования
        text = f"""
🎯 ЦЕЛЬ ДЛЯ АТАКИ

👤 Игрок: {target_info.get('username', f'Игрок_{target_id}')}
🆔 ID: {target_id}
💰 Баланс: {target_info.get('balance', 0):.2f}$
⛏️ Хешрейт: {target_info.get('hashrate', 0):.1f} MH/s
🖥️ Видеокарт: {target_info.get('active_gpus', 0)} шт.
📊 Всего добыто: {target_info.get('total_mined', 0):.2f}$
⏰ Онлайн: {calculate_online_minutes(target_info)} мин назад

📋 Инвентарь GPU:
"""
        
        if target_info.get('gpus'):
            total_gpu_value = 0
            for gpu_id, gpu_data in target_info['gpus'].items():
                if gpu_id in GPUS and gpu_data.get('count', 0) > 0:
                    count = gpu_data['count']
                    durability = gpu_data.get('durability', 100)
                    gpu_name = GPUS[gpu_id]['name']
                    gpu_value = GPUS[gpu_id]['cost'] * count
                    total_gpu_value += gpu_value
                    
                    text += f"• {gpu_name} ×{count} ({durability:.0f}%) - {gpu_value}$\n"
            
            text += f"\n💰 Стоимость фермы: {total_gpu_value:.0f}$"
        else:
            text += "• Нет видеокарт"
        
        text += f"\n\n🎯 Потенциальная добыча:"
        text += f"\n💰 Деньги: {target_info.get('balance', 0) * 0.05:.2f}$ (5%)"
        text += f"\n⚠️ Урон GPU: 10-30% износа"
        
        if not can_attack:
            text += f"\n\n❌ Нельзя атаковать: {reason}"
        
        keyboard = []
        
        if can_attack:
            keyboard.append([InlineKeyboardButton(
                "🗡️ АТАКОВАТЬ ЗА 10$", 
                callback_data=f'pvp_attack_{target_id}'
            )])
        
        keyboard.append([
            InlineKeyboardButton("🔙 К списку целей", callback_data='pvp_menu'),
            InlineKeyboardButton("🎮 В игру", callback_data='main_menu')
        ])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_target_info: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке информации о цели.",
            reply_markup=get_back_keyboard()
        )

async def can_attack_player(attacker_id, target_id):
    """Проверяет может ли игрок атаковать цель"""
    attacker_info = get_user_data(attacker_id)
    target_info = get_user_data(target_id)
    
    # Проверка лимита атак
    today = datetime.now().strftime("%Y-%m-%d")
    if attacker_info.get('pvp_attacks_date') != today:
        attacker_info['pvp_attacks_today'] = 0
        attacker_info['pvp_attacks_date'] = today
        update_user(attacker_id, {
            'pvp_attacks_today': 0,
            'pvp_attacks_date': today
        })
    
    if attacker_info.get('pvp_attacks_today', 0) >= 5:
        return False, "Лимит атак (5/день)"
    
    # Проверка баланса
    if attacker_info.get('balance', 0) < 10:
        return False, "Нужно 10$ для атаки"
    
    # Проверка защиты цели
    if is_farm_protected(target_info):
        return False, "Цель под защитой"
    
    # Проверка времени последней атаки
    last_attacked = target_info.get('last_attacked')
    if last_attacked:
        last_time = datetime.fromisoformat(last_attacked)
        if (datetime.now() - last_time).total_seconds() < 3600:
            return False, "Цель недавно атаковали"
    
    # Другие проверки
    if attacker_id == target_id:
        return False, "Нельзя атаковать себя"
    
    if target_id in ADMIN_IDS:
        return False, "Нельзя атаковать админа"
    
    if target_info.get('balance', 0) <= 0:
        return False, "У цели нет денег"
    
    return True, "Можно атаковать"

async def attack_player(query, user_id, target_id):
    """Проводит атаку на другого игрока"""
    try:
        # Проверка возможности атаки
        can_attack, reason = await can_attack_player(user_id, target_id)
        if not can_attack:
            await query.edit_message_text(
                f"❌ Нельзя атаковать: {reason}",
                reply_markup=get_back_keyboard()
            )
            return
        
        attacker_info = get_user_data(user_id)
        target_info = get_user_data(target_id)
        
        # Стоимость атаки
        attack_cost = 10
        if attacker_info['balance'] < attack_cost:
            await query.edit_message_text(
                f"❌ Недостаточно средств для атаки!\nНужно {attack_cost}$",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Крадем деньги (5% от баланса цели, макс 1000$)
        steal_amount = target_info.get('balance', 0) * 0.05
        steal_amount = min(steal_amount, 1000)
        
        if steal_amount <= 0:
            await query.edit_message_text(
                "❌ У цели нет денег для кражи!",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Наносим урон
        damage_percent = random.uniform(10, 30)
        
        # Обновляем балансы
        attacker_info['balance'] -= attack_cost
        target_info['balance'] -= steal_amount
        attacker_info['balance'] += steal_amount
        
        # Применяем урон видеокартам
        damage_details = await apply_gpu_damage(target_info, damage_percent)
        
        # Обновляем статистику
        today = datetime.now().strftime("%Y-%m-%d")
        if attacker_info.get('pvp_attacks_date') != today:
            attacker_info['pvp_attacks_today'] = 0
            attacker_info['pvp_attacks_date'] = today
        
        attacker_info['pvp_attacks_today'] = attacker_info.get('pvp_attacks_today', 0) + 1
        attacker_info['pvp_success'] = attacker_info.get('pvp_success', 0) + 1
        attacker_info['pvp_total_stolen'] = attacker_info.get('pvp_total_stolen', 0) + steal_amount
        
        # Цель получает иммунитет
        target_info['last_attacked'] = datetime.now().isoformat()
        
        # Сохраняем изменения
        update_user(user_id, {
            'balance': attacker_info['balance'],
            'pvp_attacks_today': attacker_info['pvp_attacks_today'],
            'pvp_success': attacker_info['pvp_success'],
            'pvp_total_stolen': attacker_info['pvp_total_stolen'],
            'pvp_attacks_date': attacker_info['pvp_attacks_date']
        })
        
        update_user(target_id, {
            'balance': target_info['balance'],
            'last_attacked': target_info['last_attacked'],
            'gpus': target_info.get('gpus', {})
        })
        
        # Сообщение об успешной атаке
        text = f"""
✅ АТАКА УСПЕШНА!

🎯 Цель: {target_info.get('username', f'Игрок_{target_id}')}
💰 Потрачено на атаку: {attack_cost}$
💰 Украдено: +{steal_amount:.2f}$
📊 Чистая прибыль: {steal_amount - 10:.2f}$
⚡ Нанесен урон: {damage_percent:.1f}% износа GPU

⏰ Иммунитет цели: 1 час
🎯 Атак осталось сегодня: {5 - attacker_info['pvp_attacks_today']}
"""
        
        keyboard = [
            [InlineKeyboardButton("🗡️ Атаковать снова", callback_data='pvp_menu'),
             InlineKeyboardButton("🎮 В игру", callback_data='main_menu')]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Уведомляем цель
        try:
            await query.bot.send_message(
                chat_id=target_id,
                text=f"⚠️ ВАС АТАКОВАЛИ!\n\n"
                     f"🗡️ Атакующий: {attacker_info.get('username', f'Игрок_{user_id}')}\n"
                     f"💰 Потеряно: {steal_amount:.2f}$\n"
                     f"⚡ Урон GPU: {damage_percent:.1f}%\n"
                     f"⏰ Время: {datetime.now().strftime('%H:%M')}\n\n"
                     f"Ваша ферма получила иммунитет на 1 час."
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить цель: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка при атаке: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при атаке.\nПопробуйте еще раз.",
            reply_markup=get_back_keyboard()
        )

async def apply_gpu_damage(user_info, damage_percent):
    """Наносит урон видеокартам игрока"""
    if not user_info.get('gpus'):
        return {}
    
    damage_details = {}
    
    for gpu_id, gpu_data in user_info['gpus'].items():
        if gpu_id not in GPUS:
            continue
        
        count = gpu_data.get('count', 0)
        if count <= 0:
            continue
        
        durability = gpu_data.get('durability', 100)
        
        actual_damage = random.uniform(damage_percent * 0.5, damage_percent)
        new_durability = max(0, durability - actual_damage)
        
        user_info['gpus'][gpu_id]['durability'] = new_durability
        gpu_name = GPUS[gpu_id]['name']
        damage_details[gpu_name] = actual_damage
        
        if new_durability < 5 and random.random() < 0.3:
            broken_count = random.randint(1, min(3, count))
            user_info['gpus'][gpu_id]['count'] = count - broken_count
            user_info['active_gpus'] = user_info.get('active_gpus', 0) - broken_count
            damage_details[f"{gpu_name} (сломано)"] = broken_count
    
    return damage_details

# ========== ТОПЫ ==========
async def show_tops(query, user_id):
    """Показать меню топов"""
    await query.edit_message_text(
        "🏆 *Топы игроков*\n\n"
        "Выберите категорию для просмотра топ-10 игроков:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_tops_keyboard()
    )

async def show_top_balance(query, user_id):
    """Топ по балансу - БЕЗ MARKDOWN"""
    try:
        # Собираем данные для топа
        top_data = []
        for uid, user_info in user_data.items():
            try:
                balance = float(user_info.get('balance', 0))
                if balance > 0:
                    username = user_info.get('username', f'Игрок_{uid}')
                    top_data.append({
                        'user_id': uid,
                        'username': username,
                        'balance': balance
                    })
            except:
                continue
        
        # Сортируем по балансу
        top_data.sort(key=lambda x: x['balance'], reverse=True)
        
        text = "💰 Топ-10 по балансу\n\n"
        
        if not top_data:
            text += "❌ Пока нет игроков с балансом.\n"
        else:
            for i, player in enumerate(top_data[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                username = player['username']
                if username.startswith('user_'):
                    username = f"Игрок {str(player['user_id'])[-4:]}"
                
                text += f"{medal} {username}\n"
                text += f"   💰 {player['balance']:.2f}$\n\n"
        
        keyboard = [
            [InlineKeyboardButton("👥 Топ по приглашениям", callback_data='top_referrals'),
             InlineKeyboardButton("⛏️ Топ по хешрейту", callback_data='top_hashrate')],
            [InlineKeyboardButton("🔙 Назад", callback_data='tops')]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка в show_top_balance: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке топа по балансу.",
            reply_markup=get_back_keyboard()
        )

async def show_top_referrals(query, user_id):
    """Топ по приглашениям"""
    ref_stats = []
    for uid, user_info in user_data.items():
        ref_count = len(user_info.get('referrals', []))
        if ref_count > 0:
            username = user_info['username']
            if username.startswith('user_'):
                username = f"Игрок {str(uid)[-4:]}"
            
            ref_stats.append({
                'user_id': uid,
                'username': username,
                'ref_count': ref_count,
                'ref_earned': user_info.get('ref_earned', 0)
            })
    
    ref_stats.sort(key=lambda x: x['ref_count'], reverse=True)
    
    text = "👥 *Топ-10 по приглашениям*\n\n"
    
    if not ref_stats:
        text += "❌ Пока нет активных рефереров."
    else:
        for i, stat in enumerate(ref_stats[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} @{stat['username']}\n"
            text += f"   👥 Приглашено: {stat['ref_count']}\n"
            text += f"   💰 Заработал: {stat['ref_earned']:.2f}$\n\n"
    
    keyboard = [
        [InlineKeyboardButton("💰 Топ по балансу", callback_data='top_balance'),
         InlineKeyboardButton("🏆 Топ по PvP", callback_data='top_pvp')],
        [InlineKeyboardButton("🔙 Назад", callback_data='tops')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_top_hashrate(query, user_id):
    """Топ по хешрейту"""
    # Собираем данные для топа
    top_data = []
    for uid, user_info in user_data.items():
        hashrate = user_info.get('hashrate', 0)
        if hashrate > 5:  # Базовый хешрейт 5, показываем только больше
            username = user_info.get('username', f'Игрок_{uid}')
            top_data.append({
                'user_id': uid,
                'username': username,
                'hashrate': hashrate
            })
    
    # Сортируем по хешрейту
    top_data.sort(key=lambda x: x['hashrate'], reverse=True)
    
    text = "⛏️ *Топ-10 по хешрейту*\n\n"
    
    if not top_data:
        text += "❌ Пока нет игроков с видеокартами.\n"
    else:
        for i, player in enumerate(top_data[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username = player['username']
            if username.startswith('user_'):
                username = f"Игрок {str(player['user_id'])[-4:]}"
            
            text += f"{medal} {username}\n"
            text += f"   ⛏️ {player['hashrate']:.1f} MH/s\n\n"
    
    keyboard = [
        [InlineKeyboardButton("👥 Топ по приглашениям", callback_data='top_referrals'),
         InlineKeyboardButton("🖥️ Топ по GPU", callback_data='top_gpus')],
        [InlineKeyboardButton("🔙 Назад", callback_data='tops')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_top_gpus(query, user_id):
    """Топ по количеству GPU"""
    try:
        # Собираем данные для топа
        top_data = []
        for uid, user_info in user_data.items():
            try:
                active_gpus = user_info.get('active_gpus', 0)
                if active_gpus > 0:
                    top_data.append({
                        'user_id': uid,
                        'username': user_info.get('username', f'Игрок_{uid}'),
                        'active_gpus': active_gpus
                    })
            except Exception as e:
                logger.error(f"Ошибка при обработке пользователя {uid}: {e}")
                continue
        
        # Сортируем по количеству GPU
        top_data.sort(key=lambda x: x['active_gpus'], reverse=True)
        
        text = "*Топ\\-10 по видеокартам*\n\n"
        
        if not top_data:
            text += "❌ Пока нет игроков с видеокартами\.\n"
        else:
            for i, player in enumerate(top_data[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}\."
                username = player['username']
                if username.startswith('user_'):
                    username = f"Игрок {str(player['user_id'])[-4:]}"
                
                # Экранируем специальные символы
                username_escaped = username.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
                
                text += f"{medal} {username_escaped}\n"
                text += f"   🖥️ {player['active_gpus']} видеокарт\n\n"
        
        keyboard = [
            [InlineKeyboardButton("⛏️ Топ по хешрейту", callback_data='top_hashrate'),
             InlineKeyboardButton("📈 Топ по доходу", callback_data='top_earned')],
            [InlineKeyboardButton("🔙 Назад", callback_data='tops')]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка в show_top_gpus: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке топа по GPU\.",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=get_back_keyboard()
        )

async def show_top_pvp(query, user_id):
    """Топ по PvP"""
    # Собираем данные для топа
    top_data = []
    for uid, user_info in user_data.items():
        if int(uid) == user_id:
            continue
        pvp_success = user_info.get('pvp_success', 0)
        if pvp_success > 0:
            top_data.append({
                'user_id': uid,
                'username': user_info.get('username', f'Игрок_{uid}'),
                'pvp_success': pvp_success,
                'pvp_total_stolen': user_info.get('pvp_total_stolen', 0)
            })
    
    # Сортируем по успешным атакам
    top_data.sort(key=lambda x: x['pvp_success'], reverse=True)
    
    text = "🗡️ *Топ-10 по PvP атакам*\n\n"
    
    if not top_data:
        text += "❌ Пока нет активных PvP игроков.\n"
    else:
        for i, player in enumerate(top_data[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username = player['username']
            if username.startswith('user_'):
                username = f"Игрок {str(player['user_id'])[-4:]}"
            
            text += f"{medal} {username}\n"
            text += f"   🗡️ Успешных атак: {player['pvp_success']}\n"
            text += f"   💰 Украдено: {player['pvp_total_stolen']:.2f}$\n\n"
    
    keyboard = [
        [InlineKeyboardButton("💰 Топ по балансу", callback_data='top_balance'),
         InlineKeyboardButton("👥 Топ по приглашениям", callback_data='top_referrals')],
        [InlineKeyboardButton("🔙 Назад", callback_data='tops')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_top_earned(query, user_id):
    """Топ по общему заработку"""
    try:
        # Собираем данные для топа
        top_data = []
        for uid, user_info in user_data.items():
            try:
                total_earned = float(user_info.get('total_earned', 0))
                if total_earned > 5:  # стартовый баланс 5
                    top_data.append({
                        'user_id': uid,
                        'username': user_info.get('username', f'Игрок_{uid}'),
                        'total_earned': total_earned
                    })
            except:
                continue
        
        # Сортируем по общему заработку
        top_data.sort(key=lambda x: x['total_earned'], reverse=True)
        
        text = "📈 *Топ-10 по общему заработку*\n\n"
        
        if not top_data:
            text += "❌ Пока нет активных игроков.\n"
        else:
            for i, player in enumerate(top_data[:10], 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                username = player['username']
                if username.startswith('user_'):
                    username = f"Игрок {str(player['user_id'])[-4:]}"
                
                text += f"{medal} {username}\n"
                text += f"   📈 {player['total_earned']:.2f}$\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🖥️ Топ по GPU", callback_data='top_gpus'),
             InlineKeyboardButton("🏆 Топ по PvP", callback_data='top_pvp')],
            [InlineKeyboardButton("🔙 Назад", callback_data='tops')]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка в show_top_earned: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при загрузке топа по доходу.",
            reply_markup=get_back_keyboard()
        )

# ========== СТАТИСТИКА ==========
async def show_stats(query, user_id):
    """Показать статистику"""
    try:
        user_info = get_user_data(user_id)
        
        reg_date = datetime.fromisoformat(user_info['registered'])
        days_playing = (datetime.now() - reg_date).days
        
        total_investment = 0
        for gpu_id, gpu_data in user_info.get('gpus', {}).items():
            if gpu_id in GPUS:
                total_investment += GPUS[gpu_id]['cost'] * gpu_data.get('count', 0)
        
        roi = 0
        if total_investment > 0:
            roi = (user_info['total_earned'] / total_investment) * 100
        
        display_name = f"@{user_info['username']}" if user_info['username'] and not user_info['username'].startswith('user_') else f"ID: {user_id}"
        
        # Проверяем активные бустеры
        active_boosters = []
        if user_info.get('active_boosters'):
            for booster_id, booster_data in user_info['active_boosters'].items():
                expires = datetime.fromisoformat(booster_data['expires'])
                if expires > datetime.now():
                    booster_name = SERVICES.get(booster_id, {}).get('name', 'Бустер')
                    time_left = expires - datetime.now()
                    hours_left = time_left.total_seconds() / 3600
                    active_boosters.append(f"{booster_name} ({hours_left:.1f}ч)")
        
        text = f"""
📊 *Статистика майнера*

👤 Майнер: *{display_name}*
📅 Играет дней: *{days_playing}*
💰 Баланс: *{user_info['balance']:.2f}* $

🏭 *Ферма:*
🖥️ Видеокарт: *{user_info['active_gpus']}* шт.
⛏️ Хешрейт: *{user_info['hashrate']:.1f}* MH/s
⚡ Энергия: *{user_info['energy']:.0f}/{user_info['max_energy']}* кВт
🌡️ Температура: *{user_info['temperature']:.1f}°C*

💰 *Финансы:*
💸 Всего добыто: *{user_info['total_mined']:.2f}* $
💎 Всего заработано: *{user_info['total_earned']:.2f}* $
🏦 Инвестировано: *{total_investment:.2f}* $
📈 ROI: *{roi:.1f}%*

👥 *Рефералы:*
👥 Приглашено: *{len(user_info.get('referrals', []))}*
💰 Заработано: *{user_info.get('ref_earned', 0):.2f}* $

🗡️ *PvP:*
🎯 Успешных атак: *{user_info.get('pvp_success', 0)}*
🛡️ Защищался: *{user_info.get('pvp_defended', 0)}*
💰 Украдено: *{user_info.get('pvp_total_stolen', 0):.2f}* $

🎁 *Промокоды:*
🎫 Использовано: *{len(user_info.get('promocodes_used', []))}*

⏱️ *Время майнинга:*
🕒 Всего: *{user_info.get('mining_time_minutes', 0)}* мин.
"""
        
        if active_boosters:
            text += f"\n🚀 *Активные бустеры:*\n"
            for booster in active_boosters:
                text += f"• {booster}\n"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass  # Игнорируем эту ошибку
        else:
            raise

# ========== ОХЛАЖДЕНИЕ И ОБНОВЛЕНИЕ ==========
async def cool_farm(query, user_id):
    """Остудить ферму"""
    user_info = get_user_data(user_id)
    
    if user_info['temperature'] <= 30:
        await query.edit_message_text(
            "❄️ *Температура уже оптимальна!*\n\n"
            f"🌡️ Текущая температура: {user_info['temperature']:.1f}°C",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    
    cooling_cost = (user_info['temperature'] - 30) * 0.5
    cooling_amount = (user_info['temperature'] - 30) * 0.7
    
    if user_info['balance'] < cooling_cost:
        await query.edit_message_text(
            f"❌ *Недостаточно средств для охлаждения!*\n\n"
            f"💰 Нужно: {cooling_cost:.2f}$\n"
            f"💎 У вас: {user_info['balance']:.2f}$\n\n"
            f"💡 Совет: Подождите пока ферма остынет сама или купите улучшенное охлаждение.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    
    user_info['balance'] -= cooling_cost
    user_info['temperature'] -= cooling_amount
    
    if user_info['temperature'] < 30:
        user_info['temperature'] = 30
    
    update_user(user_id, {
        'balance': user_info['balance'],
        'temperature': user_info['temperature']
    })
    
    log_transaction(user_id, user_info['username'], "COOL_FARM", -cooling_cost,
                   f"Охлаждение на {cooling_amount:.1f}°C")
    
    await query.edit_message_text(
        f"❄️ *Ферма охлаждена!*\n\n"
        f"🌡️ Температура снижена на: {cooling_amount:.1f}°C\n"
        f"💸 Стоимость охлаждения: {cooling_cost:.2f}$\n"
        f"🌡️ Новая температура: {user_info['temperature']:.1f}°C\n"
        f"💰 Остаток баланса: {user_info['balance']:.2f}$",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

async def refresh_stats(query, user_id):
    """Обновить статистику"""
    user_info = get_user_data(user_id)
    
    # Восстановление энергии
    if user_info.get('last_mining'):
        last_mining = datetime.fromisoformat(user_info['last_mining'])
        now = datetime.now()
        minutes_passed = (now - last_mining).total_seconds() / 60
        energy_to_add = int(minutes_passed * 2)
        if energy_to_add > 0:
            user_info['energy'] = min(user_info['max_energy'], user_info['energy'] + energy_to_add)
            update_user(user_id, {'energy': user_info['energy']})
    
    # Остывание фермы (если не майнит)
    cooling_rate = 0.1  # °C в минуту
    temp_to_reduce = minutes_passed * cooling_rate
    if temp_to_reduce > 0 and user_info['temperature'] > 30:
        user_info['temperature'] = max(30, user_info['temperature'] - temp_to_reduce)
        update_user(user_id, {'temperature': user_info['temperature']})
    
    await query.edit_message_text(
        f"🔄 *Статистика обновлена!*\n\n"
        f"⚡ Энергия восстановлена: +{energy_to_add} кВт\n"
        f"🌡️ Температура снижена: -{temp_to_reduce:.1f}°C\n"
        f"⏱️ Прошло времени: {minutes_passed:.0f} мин",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== АДМИН ПАНЕЛЬ ==========
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    text = f"""
👑 *Панель администратора*

👥 Пользователей: *{len(user_data)}*
💰 Общий баланс: *{sum(u['balance'] for u in user_data.values()):.2f}* $
⛏️ Активных ферм: *{sum(1 for u in user_data.values() if u['active_gpus'] > 0)}*

🎁 Промокодов: *{len(promocodes)}*
🆘 Открытых тикетов: *{sum(1 for t in support_tickets.values() if t.get('status') == 'open')}*

Выберите действие:
"""
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_give_balance(query, user_id):
    """Выдать баланс (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_give_balance'
    await query.edit_message_text(
        "💰 *Выдача баланса*\n\n"
        "Введите ID пользователя и сумму через пробел:\n"
        "Пример: `123456789 1000`\n\n"
        "*После выдачи вы вернетесь в админ-панель*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_create_promo(query, user_id):
    """Создать промокод (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_create_promo'
    await query.edit_message_text(
        "🎁 *Создание промокода*\n\n"
        "Введите данные промокода в формате:\n"
        "`КОД СУММА КОЛИЧЕСТВО`\n"
        "Пример: `SUMMER2024 500 100`\n\n"
        "*После создания вы вернетесь в админ-панель*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_give_protection(query, user_id):
    """Меню выдачи защиты (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_give_protection'
    await query.edit_message_text(
        "🛡️ *Выдача защиты*\n\n"
        "Введите ID пользователя и количество часов через пробел:\n"
        "Пример: `123456789 24` - защита на 24 часа\n"
        "Пример: `123456789 0` - снять защиту\n\n"
        "*После выдачи вы вернетесь в админ-панель*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_give_items(query, user_id):
    """Выдать скины/бустеры/статусы (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_give_items'
    
    text = """
🎨 *Выдача предметов*

Введите данные в формате:
`ID_пользователя тип_предмета название_предмета`

Примеры:
`123456789 skin Геймерский скин`
`123456789 booster Бустер энергии`
`123456789 status Алмазный майнер`

Доступные типы:
• skin - скины
• booster - бустеры
• status - статусы

*После выдачи вы вернетесь в админ-панель*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_give_secret_items(query, user_id):
    """Выдать секретные предметы (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_give_secret_items'
    
    text = """
🔒 *Выдача секретных предметов*

Введите данные в формате:
`ID_пользователя тип_предмета название_предмета`

Примеры:
`123456789 secret_skin Золотой дракон`
`123456789 secret_booster Супер энергия`
`123456789 secret_status Легендарный майнер`
`123456789 secret_currency 1000`

Доступные типы:
• secret_skin - секретные скины
• secret_booster - секретные бустеры
• secret_status - секретные статусы
• secret_currency - секретная валюта

*После выдачи вы вернетесь в админ-панель*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_create_secret_promo(query, user_id):
    """Создать секретный промокод (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_create_secret_promo'
    
    text = """
🎫 *Создание секретного промокода*

Введите данные в формате:
`КОД тип_награды значение_награды количество_использований`

Примеры:
`SECRET2024 secret_gpu RTX_5090 100`
`SECRET2024 secret_status Легендарный 50`
`SECRET2024 secret_skin Дракон 25`
`SECRET2024 secret_booster Мега 75`

Доступные типы:
• secret_gpu - секретные видеокарты
• secret_status - секретные статусы
• secret_skin - секретные скины
• secret_booster - секретные бустеры

*После создания вы вернетесь в админ-панель*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_events(query, user_id):
    """Управление ивентами (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    current_event = events_data.get('current_event', {})
    next_event = events_data.get('next_event', {})
    
    text = f"""
🎪 *Управление ивентами*

🎯 *Текущий ивент:*
• Название: {current_event.get('name', 'Нет')}
• Описание: {current_event.get('description', 'Нет')}
• Бонус: {current_event.get('bonus_percent', 0)}%
• Статус: {'🟢 Активен' if current_event.get('active') else '🔴 Не активен'}
• Начало: {datetime.fromisoformat(current_event.get('start_date', datetime.now().isoformat())).strftime('%d.%m.%Y')}
• Конец: {datetime.fromisoformat(current_event.get('end_date', datetime.now().isoformat())).strftime('%d.%m.%Y')}

⏭️ *Следующий ивент:*
• Название: {next_event.get('name', 'Нет')}
• Описание: {next_event.get('description', 'Нет')}
• Начало: {datetime.fromisoformat(next_event.get('start_date', datetime.now().isoformat())).strftime('%d.%m.%Y')}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 Изменить текущий ивент", callback_data='admin_change_current_event')],
        [InlineKeyboardButton("⏭️ Изменить следующий ивент", callback_data='admin_change_next_event')],
        [InlineKeyboardButton("➕ Добавить будущий ивент", callback_data='admin_add_future_event')],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_change_current_event(query, user_id):
    """Изменить текущий ивент"""
    if user_id not in ADMIN_IDS:
        return
    
    user_states[user_id] = 'admin_change_current_event'
    
    text = """
🔄 *Изменение текущего ивента*

Введите данные в формате:
`название|описание|бонус_в_процентах|дата_окончания(ГГГГ-ММ-ДД)`

Пример:
`Летний майнинг|Увеличенный доход на 20%|20|2024-08-31`

*После изменения вы вернетесь в админ-панель*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_change_next_event(query, user_id):
    """Изменить следующий ивент"""
    if user_id not in ADMIN_IDS:
        return
    
    user_states[user_id] = 'admin_change_next_event'
    
    text = """
⏭️ *Изменение следующего ивента*

Введите данные в формате:
`название|описание|дата_начала(ГГГГ-ММ-ДД)|дата_окончания(ГГГГ-ММ-ДД)`

Пример:
`Хэллоуин Хоррор|Шанс найти редкие видеокарты призраков|2024-10-01|2024-10-31`

*После изменения вы вернетесь в админ-панель*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_add_future_event(query, user_id):
    """Добавить будущий ивент"""
    if user_id not in ADMIN_IDS:
        return
    
    user_states[user_id] = 'admin_add_future_event'
    
    text = """
➕ *Добавление будущего ивента*

Введите данные в формате:
`название|описание|дата_начала(ГГГГ-ММ-ДД)|дата_окончания(ГГГГ-ММ-ДД)`

Пример:
`Новый год 2025|Бонусы за активность в праздники|2024-12-25|2025-01-10`

*После добавления вы вернетесь в админ-панель*
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )

async def admin_show_users(query, user_id):
    """Показать список пользователей (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    # Сортируем пользователей по балансу
    sorted_users = sorted(user_data.items(), key=lambda x: x[1].get('balance', 0), reverse=True)
    
    text = f"""
👥 *Список пользователей*

Всего пользователей: *{len(user_data)}*

🏆 *Топ-10 по балансу:*
"""
    
    for i, (uid, user_info) in enumerate(sorted_users[:10], 1):
        username = user_info.get('username', f'user_{uid}')
        if username.startswith('user_'):
            username = f"Игрок {str(uid)[-4:]}"
        
        balance = user_info.get('balance', 0)
        active_gpus = user_info.get('active_gpus', 0)
        hashrate = user_info.get('hashrate', 0)
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} @{username}\n"
        text += f"   💰 {balance:.2f}$ | 🖥 {active_gpus} GPU | ⛏ {hashrate:.1f} MH/s\n"
        text += f"   🆔 ID: `{uid}`\n\n"
    
    text += f"\n📊 *Статистика:*\n"
    text += f"• Средний баланс: {sum(u['balance'] for u in user_data.values())/len(user_data):.2f}$\n"
    text += f"• Всего добыто: {sum(u['total_mined'] for u in user_data.values()):.2f}$\n"
    text += f"• Всего видеокарт: {sum(u['active_gpus'] for u in user_data.values())}"
    
    keyboard = [
        [InlineKeyboardButton("📊 Подробная статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("💰 Выдать баланс", callback_data='admin_give_balance')],
        [InlineKeyboardButton("🔙 Назад", callback_data='admin')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_show_stats(query, user_id):
    """Показать статистику бота (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    total_balance = sum(u['balance'] for u in user_data.values())
    total_mined = sum(u['total_mined'] for u in user_data.values())
    total_earned = sum(u['total_earned'] for u in user_data.values())
    total_gpus = sum(u['active_gpus'] for u in user_data.values())
    total_hashrate = sum(u['hashrate'] for u in user_data.values())
    total_ref_earned = sum(u.get('ref_earned', 0) for u in user_data.values())
    total_investment = 0
    
    for user_info in user_data.values():
        for gpu_id, gpu_data in user_info.get('gpus', {}).items():
            if gpu_id in GPUS:
                total_investment += GPUS[gpu_id]['cost'] * gpu_data.get('count', 0)
    
    # Активные пользователи (за последние 24 часа)
    active_users = 0
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    for user_info in user_data.values():
        if 'last_mining' in user_info:
            last_mining = datetime.fromisoformat(user_info['last_mining'])
            if last_mining > twenty_four_hours_ago:
                active_users += 1
    
    text = f"""
📊 *Статистика бота*

👥 *Пользователи:*
• Всего: {len(user_data)}
• Активных (24ч): {active_users}
• Новых (7 дней): {sum(1 for u in user_data.values() if datetime.fromisoformat(u['registered']) > datetime.now() - timedelta(days=7))}

💰 *Экономика:*
• Общий баланс: {total_balance:.2f}$
• Всего добыто: {total_mined:.2f}$
• Всего заработано: {total_earned:.2f}$
• Инвестировано в GPU: {total_investment:.0f}$

🏭 *Фермы:*
• Всего видеокарт: {total_gpus}
• Общий хешрейт: {total_hashrate:.1f} MH/s
• Средняя ферма: {total_gpus/len(user_data):.1f} GPU

👥 *Рефералы:*
• Всего приглашено: {sum(len(u.get('referrals', [])) for u in user_data.values())}
• Выплачено бонусов: {total_ref_earned:.2f}$

🎁 *Промокоды:*
• Создано: {len(promocodes)}
• Использовано: {sum(p['used'] for p in promocodes.values())}
• Осталось: {sum(p['max_uses'] - p['used'] for p in promocodes.values())}

🆘 *Тикеты:*
• Открыто: {sum(1 for t in support_tickets.values() if t.get('status') == 'open')}
• В работе: {sum(1 for t in support_tickets.values() if t.get('status') == 'in_progress')}
• Закрыто: {sum(1 for t in support_tickets.values() if t.get('status') == 'closed')}
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 Список пользователей", callback_data='admin_users'),
         InlineKeyboardButton("⚙️ Настройки", callback_data='admin_settings')],
        [InlineKeyboardButton("🆘 Тикеты", callback_data='admin_tickets'),
         InlineKeyboardButton("🔙 Назад", callback_data='admin')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_show_settings(query, user_id):
    """Показать настройки бота (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    text = f"""
⚙️ *Настройки бота*

📊 *Текущие настройки:*
• Бот: {BOT_USERNAME}
• Канал: {CHANNEL_USERNAME}
• Чат: {CHAT_USERNAME}
• Поддержка: {SUPPORT_USERNAME}
• Админы: {len(ADMIN_IDS)}

💾 *Данные:*
• Пользователей: {len(user_data)}
• Промокодов: {len(promocodes)}
• Тикетов: {len(support_tickets)}

🔧 *Настройки майнинга:*
• Стартовый баланс: 5$
• Стартовый хешрейт: 5 MH/s
• Базовая энергия: 1500 кВт
• Макс. температура: 100°C

⚡ *Настройки PvP:*
• Атак в день: 5
• Стоимость атаки: 10$
• Процент кражи: 5%
• Иммунитет: 1 час

🛡️ *Настройки защиты:*
• Планы: 1ч/100$, 8ч/500$, 24ч/15⭐
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 Перезагрузить данные", callback_data='admin_reload_data'),
         InlineKeyboardButton("📊 Статистика", callback_data='admin_stats')],
        [InlineKeyboardButton("👥 Пользователи", callback_data='admin_users'),
         InlineKeyboardButton("🔙 Назад", callback_data='admin')]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_show_tickets(query, user_id):
    """Показать тикеты поддержки (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    open_tickets = []
    for ticket_id, ticket in support_tickets.items():
        if ticket.get('status') == 'open':
            open_tickets.append((ticket_id, ticket))
    
    if not open_tickets:
        await query.edit_message_text(
            "🆘 *Тикеты поддержки*\n\n"
            "✅ Нет открытых тикетов!\n\n"
            "Все вопросы решены.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_admin_keyboard()
        )
        return
    
    text = "🆘 *Открытые тикеты*\n\n"
    
    for ticket_id, ticket in open_tickets[:10]:  # Ограничим 10 тикетов
        user_id_ticket = ticket.get('user_id')
        user_info = get_user_data(user_id_ticket)
        username = user_info['username']
        if username.startswith('user_'):
            username = f"Игрок {str(user_id_ticket)[-4:]}"
        
        created = datetime.fromisoformat(ticket['created'])
        text += f"📝 *Тикет #{ticket_id}*\n"
        text += f"👤 Пользователь: @{username} (ID: `{user_id_ticket}`)\n"
        text += f"📅 Создан: {created.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"📋 Тема: {ticket.get('subject', 'Без темы')}\n"
        text += f"📝 Сообщение: {ticket.get('message', 'Нет сообщения')[:50]}...\n\n"
    
    if len(open_tickets) > 10:
        text += f"... и еще {len(open_tickets) - 10} тикетов\n\n"
    
    keyboard = []
    for ticket_id, _ in open_tickets[:5]:
        keyboard.append([InlineKeyboardButton(
            f"📝 Ответить на тикет #{ticket_id}",
            callback_data=f'admin_reply_ticket_{ticket_id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='admin')])
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_clear_rub_balance(query, user_id):
    """Обнулить рублевый баланс пользователя"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    user_states[user_id] = 'admin_clear_rub_balance'
    
    text = """
💰 *Обнуление рублевого баланса*

Введите ID пользователя, которому нужно обнулить рублевый баланс.

📝 *Формат:*
`ID_пользователя` - просто ID без дополнительных символов

*Пример:*
`1499855064` - обнулит рублевый баланс пользователя с этим ID

⚠️ *Внимание:*
• Эта операция необратима
• Баланс в долларах ($) не затрагивается
• Только рублевый баланс (₽) будет обнулен

После обнуления вы вернетесь в админ-панель.
"""
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )
    
async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий админа"""
    user_id = update.message.from_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    message_text = update.message.text.strip()
    
    try:
        if state == 'admin_give_balance':
            try:
                parts = message_text.split()
                if len(parts) != 2:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `ID СУММА`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                target_id_str = str(parts[0])
                amount = float(parts[1])
                
                if target_id_str not in user_data:
                    await update.message.reply_text(
                        f"❌ Пользователь {target_id_str} не найден!",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                user_data[target_id_str]['balance'] += amount
                user_data[target_id_str]['total_earned'] += amount
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "ADMIN_GIVE_BALANCE", amount, f"Пользователю {target_id_str}")
                
                await update.message.reply_text(
                    f"✅ Баланс пользователя {target_id_str} увеличен на {amount}$\n"
                    f"Новый баланс: {user_data[target_id_str]['balance']:.2f}$",
                    reply_markup=get_admin_keyboard()
                )
                
            except ValueError:
                await update.message.reply_text(
                    "❌ Ошибка в данных!",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_create_promo':
            try:
                parts = message_text.split()
                if len(parts) != 3:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `КОД СУММА КОЛИЧЕСТВО`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                code = parts[0].upper()
                amount = float(parts[1])
                uses = int(parts[2])
                
                if code in promocodes:
                    await update.message.reply_text(
                        f"❌ Промокод {code} уже существует!",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                promocodes[code] = {
                    'amount': amount,
                    'max_uses': uses,
                    'used': 0,
                    'created': datetime.now().isoformat(),
                    'created_by': user_id,
                    'users': []
                }
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "CREATE_PROMO", amount, f"Промокод: {code}, Использований: {uses}")
                
                await update.message.reply_text(
                    f"✅ Промокод создан!\n"
                    f"🎁 Код: `{code}`\n"
                    f"💰 Сумма: {amount}$\n"
                    f"📊 Использований: {uses}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_admin_keyboard()
                )
            
            except ValueError:
                await update.message.reply_text(
                    "❌ Ошибка в данных!",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_give_protection':
            try:
                parts = message_text.split()
                if len(parts) != 2:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `ID ЧАСЫ`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                target_id_str = str(parts[0])
                hours = float(parts[1])
                
                if target_id_str not in user_data:
                    await update.message.reply_text(
                        f"❌ Пользователь {target_id_str} не найден!",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                user_info = user_data[target_id_str]
                username = user_info.get('username', target_id_str)
                
                if hours <= 0:
                    user_info['farm_protection'] = None
                    text = f"✅ Защита снята с игрока {username} (ID: {target_id_str})"
                else:
                    protection_end = datetime.now() + timedelta(hours=hours)
                    user_info['farm_protection'] = protection_end.isoformat()
                    
                    text = (f"✅ Защита выдана игроку {username} (ID: {target_id_str})\n"
                           f"⏱️ Длительность: {hours} часов\n"
                           f"🕒 Истекает: {protection_end.strftime('%d.%m.%Y %H:%M')}")
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                               "ADMIN_PROTECT", 0, f"ID: {target_id_str}, Часы: {hours}")
                
                await update.message.reply_text(
                    text,
                    reply_markup=get_admin_keyboard()
                )
                
            except ValueError:
                await update.message.reply_text(
                    "❌ Ошибка в данных!",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_give_items':
            try:
                parts = message_text.split()
                if len(parts) < 3:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `ID тип название`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                target_id_str = str(parts[0])
                item_type = parts[1]
                item_name = ' '.join(parts[2:])
                
                if target_id_str not in user_data:
                    await update.message.reply_text(
                        f"❌ Пользователь {target_id_str} не найден!",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                user_info = user_data[target_id_str]
                
                if item_type == 'skin':
                    if 'skins' not in user_info:
                        user_info['skins'] = {}
                    user_info['skins'][item_name.lower().replace(' ', '_')] = item_name
                    text = f"✅ Скин '{item_name}' выдан игроку {target_id_str}"
                
                elif item_type == 'booster':
                    if 'active_boosters' not in user_info:
                        user_info['active_boosters'] = {}
                    booster_id = item_name.lower().replace(' ', '_')
                    user_info['active_boosters'][booster_id] = {
                        'activated': datetime.now().isoformat(),
                        'expires': (datetime.now() + timedelta(hours=24)).isoformat()
                    }
                    text = f"✅ Бустер '{item_name}' выдан игроку {target_id_str}"
                
                elif item_type == 'status':
                    if 'purchased_services' not in user_info:
                        user_info['purchased_services'] = {}
                    status_id = item_name.lower().replace(' ', '_')
                    user_info['purchased_services'][status_id] = {
                        'purchased': datetime.now().isoformat(),
                        'active': True
                    }
                    text = f"✅ Статус '{item_name}' выдан игроку {target_id_str}"
                
                else:
                    await update.message.reply_text(
                        "❌ Неверный тип предмета! Доступно: skin, booster, status",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "ADMIN_GIVE_ITEM", 0, f"ID: {target_id_str}, Тип: {item_type}, Название: {item_name}")
                
                await update.message.reply_text(
                    text,
                    reply_markup=get_admin_keyboard()
                )
                
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка: {e}",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_give_secret_items':
            try:
                parts = message_text.split()
                if len(parts) < 3:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `ID тип название`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                target_id_str = str(parts[0])
                item_type = parts[1]
                item_value = ' '.join(parts[2:])
                
                if target_id_str not in user_data:
                    await update.message.reply_text(
                        f"❌ Пользователь {target_id_str} не найден!",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                user_info = user_data[target_id_str]
                
                if item_type == 'secret_skin':
                    if 'secret_skins' not in user_info:
                        user_info['secret_skins'] = {}
                    skin_id = item_value.lower().replace(' ', '_')
                    user_info['secret_skins'][skin_id] = item_value
                    text = f"✅ Секретный скин '{item_value}' выдан игроку {target_id_str}"
                
                elif item_type == 'secret_booster':
                    if 'secret_boosters' not in user_info:
                        user_info['secret_boosters'] = {}
                    booster_id = item_value.lower().replace(' ', '_')
                    user_info['secret_boosters'][booster_id] = {
                        'activated': datetime.now().isoformat(),
                        'expires': (datetime.now() + timedelta(hours=48)).isoformat()
                    }
                    text = f"✅ Секретный бустер '{item_value}' выдан игроку {target_id_str}"
                
                elif item_type == 'secret_status':
                    if 'secret_statuses' not in user_info:
                        user_info['secret_statuses'] = {}
                    status_id = item_value.lower().replace(' ', '_')
                    user_info['secret_statuses'][status_id] = {
                        'purchased': datetime.now().isoformat(),
                        'active': True
                    }
                    text = f"✅ Секретный статус '{item_value}' выдан игроку {target_id_str}"
                
                elif item_type == 'secret_currency':
                    try:
                        amount = float(item_value)
                        user_info['balance'] += amount
                        user_info['total_earned'] += amount
                        text = f"✅ Секретная валюта {amount}$ выдана игроку {target_id_str}"
                    except ValueError:
                        await update.message.reply_text(
                            "❌ Неверная сумма!",
                            reply_markup=get_admin_keyboard()
                        )
                        return
                
                else:
                    await update.message.reply_text(
                        "❌ Неверный тип предмета! Доступно: secret_skin, secret_booster, secret_status, secret_currency",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "ADMIN_GIVE_SECRET_ITEM", 0, f"ID: {target_id_str}, Тип: {item_type}, Значение: {item_value}")
                
                await update.message.reply_text(
                    text,
                    reply_markup=get_admin_keyboard()
                )
                
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка: {e}",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_create_secret_promo':
            try:
                parts = message_text.split()
                if len(parts) != 4:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `КОД тип значение количество`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                code = parts[0].upper()
                reward_type = parts[1]
                reward_value = parts[2]
                uses = int(parts[3])
                
                if code in promocodes:
                    await update.message.reply_text(
                        f"❌ Промокод {code} уже существует!",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                promocodes[code] = {
                    'type': 'secret',
                    'reward_type': reward_type,
                    'reward_value': reward_value,
                    'max_uses': uses,
                    'used': 0,
                    'created': datetime.now().isoformat(),
                    'created_by': user_id,
                    'users': []
                }
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "CREATE_SECRET_PROMO", 0, f"Код: {code}, Тип: {reward_type}, Значение: {reward_value}, Использований: {uses}")
                
                await update.message.reply_text(
                    f"✅ Секретный промокод создан!\n"
                    f"🎁 Код: `{code}`\n"
                    f"📦 Тип награды: {reward_type}\n"
                    f"🎯 Значение: {reward_value}\n"
                    f"📊 Использований: {uses}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_admin_keyboard()
                )
            
            except ValueError:
                await update.message.reply_text(
                    "❌ Ошибка в данных!",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_change_current_event':
            try:
                parts = message_text.split('|')
                if len(parts) != 4:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `название|описание|бонус|дата_окончания`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                name = parts[0].strip()
                description = parts[1].strip()
                bonus = int(parts[2].strip())
                end_date = parts[3].strip()
                
                events_data['current_event'] = {
                    'name': name,
                    'description': description,
                    'bonus_percent': bonus,
                    'start_date': datetime.now().isoformat(),
                    'end_date': end_date + "T23:59:59",
                    'active': True
                }
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "CHANGE_CURRENT_EVENT", 0, f"Название: {name}, Бонус: {bonus}%")
                
                await update.message.reply_text(
                    f"✅ Текущий ивент изменен!\n"
                    f"🎪 Название: {name}\n"
                    f"📝 Описание: {description}\n"
                    f"🎯 Бонус: {bonus}%\n"
                    f"📅 Окончание: {end_date}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_admin_keyboard()
                )
            
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка: {e}",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_change_next_event':
            try:
                parts = message_text.split('|')
                if len(parts) != 4:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `название|описание|дата_начала|дата_окончания`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                name = parts[0].strip()
                description = parts[1].strip()
                start_date = parts[2].strip()
                end_date = parts[3].strip()
                
                events_data['next_event'] = {
                    'name': name,
                    'description': description,
                    'start_date': start_date + "T00:00:00",
                    'end_date': end_date + "T23:59:59",
                    'active': False
                }
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "CHANGE_NEXT_EVENT", 0, f"Название: {name}")
                
                await update.message.reply_text(
                    f"✅ Следующий ивент изменен!\n"
                    f"🎪 Название: {name}\n"
                    f"📝 Описание: {description}\n"
                    f"📅 Начало: {start_date}\n"
                    f"📅 Окончание: {end_date}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_admin_keyboard()
                )
            
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка: {e}",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_add_future_event':
            try:
                parts = message_text.split('|')
                if len(parts) != 4:
                    await update.message.reply_text(
                        "❌ Неверный формат! Используйте: `название|описание|дата_начала|дата_окончания`",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                name = parts[0].strip()
                description = parts[1].strip()
                start_date = parts[2].strip()
                end_date = parts[3].strip()
                
                if 'future_events' not in events_data:
                    events_data['future_events'] = []
                
                events_data['future_events'].append({
                    'name': name,
                    'description': description,
                    'start_date': start_date + "T00:00:00",
                    'end_date': end_date + "T23:59:59"
                })
                
                save_data()
                
                log_transaction(user_id, update.effective_user.username or "admin", 
                              "ADD_FUTURE_EVENT", 0, f"Название: {name}")
                
                await update.message.reply_text(
                    f"✅ Будущий ивент добавлен!\n"
                    f"🎪 Название: {name}\n"
                    f"📝 Описание: {description}\n"
                    f"📅 Начало: {start_date}\n"
                    f"📅 Окончание: {end_date}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_admin_keyboard()
                )
            
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка: {e}",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state.startswith('admin_reply_ticket_'):
            ticket_id = state[19:]
            if ticket_id in support_tickets:
                ticket = support_tickets[ticket_id]
                target_user_id = ticket['user_id']
                
                # Отправляем ответ пользователю
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"💬 *Ответ от администратора*\n\n"
                             f"📝 Тикет: `{ticket_id}`\n"
                             f"👤 Админ: @{update.effective_user.username or 'Администратор'}\n"
                             f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                             f"📋 Ответ:\n{message_text}\n\n"
                             f"📌 *Статус тикета:* В работе\n"
                             f"💬 Для ответа создайте новый тикет.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить ответ пользователю {target_user_id}: {e}")
                    await update.message.reply_text(
                        f"❌ Не удалось отправить ответ пользователю!\n"
                        f"Ошибка: {e}",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                
                # Обновляем тикет
                support_tickets[ticket_id]['status'] = 'in_progress'
                support_tickets[ticket_id]['updated'] = datetime.now().isoformat()
                support_tickets[ticket_id]['admin_reply'] = message_text
                support_tickets[ticket_id]['admin_id'] = user_id
                
                save_data()
                
                await update.message.reply_text(
                    f"✅ Ответ отправлен пользователю!\n"
                    f"📝 Тикет: `{ticket_id}`\n"
                    f"👤 Пользователь: {ticket['username']} (ID: `{target_user_id}`)",
                    reply_markup=get_admin_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ Тикет не найден!",
                    reply_markup=get_admin_keyboard()
                )
        
        elif state == 'admin_clear_rub_balance':
            try:
                target_id_str = str(message_text.strip())

                if target_id_str not in user_data:
                    await update.message.reply_text(
                        f"❌ Пользователь с ID {target_id_str} не найден!",
                        reply_markup=get_admin_keyboard()
                    )
                    return

                target_user = user_data[target_id_str]
                old_balance = target_user.get('rub_balance', 0)
                username = target_user.get('username', f'ID: {target_id_str}')

                target_user['rub_balance'] = 0
                save_data()

                log_transaction(
                    user_id,
                    update.effective_user.username or "admin",
                    "ADMIN_CLEAR_RUB_BALANCE",
                    0,
                    f"ID: {target_id_str}, Было: {old_balance}₽"
                )

                await update.message.reply_text(
                    f"✅ Рублевый баланс обнулен!\n"
                    f"Пользователь: @{username}\n"
                    f"ID: {target_id_str}\n"
                    f"Было: {old_balance}₽\n"
                    f"Стало: 0₽",
                    reply_markup=get_admin_keyboard()
                )

            except Exception as e:
                await update.message.reply_text(
                    f"❌ Ошибка: {e}",
                    reply_markup=get_admin_keyboard()
                )
        
        # НЕ ИСПОЛЬЗУЙТЕ else ЗДЕСЬ - ЭТО ВЫЗЫВАЕТ ОШИБКУ
    
    except Exception as e:
        logger.error(f"Ошибка в handle_admin_actions: {e}")
        await update.message.reply_text(
            f"❌ Произошла ошибка: {e}",
            reply_markup=get_admin_keyboard()
        )
    
    finally:
        # Очищаем состояние пользователя
        if user_id in user_states:
            user_states.pop(user_id, None)

# ========== МОДЕРАЦИЯ В ЧАТЕ ==========
async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений в чате"""
    if update.message.chat.id != CHAT_ID:
        return
    
    user_id = update.message.from_user.id
    message_text = update.message.text or ""
    
    # Проверка на мут
    if user_id in muted_users:
        unmute_time = muted_users[user_id]
        if datetime.now() < unmute_time:
            try:
                await update.message.delete()
                await update.message.reply_text(
                    f"⚠️ @{update.message.from_user.username or update.message.from_user.first_name}, вы в муте до {unmute_time.strftime('%H:%M:%S')}. "
                    f"Если мут выдан по ошибке, напишите @HomsyAdmin",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                pass
            return
    
    # Обработка команд
    if message_text.startswith('/'):
        command = message_text.split()[0].lower()
        
        if command == '/rules':
            await update.message.reply_text(
                "📜 *Правила чата:*\n\n"
                "1. Уважайте других участников\n"
                "2. Запрещен спам и флуд\n"
                "3. Запрещена реклама без согласования\n"
                "4. Запрещены оскорбления\n"
                "5. Следуйте указаниям администрации\n\n"
                "⚠️ *Нарушение правил ведет к муту или бану!*\n\n"
                "📢 *Канал проекта:* @MineEvoUltra\n"
                "🤖 *Бот:* @MineEvoUltra_bot",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif command == '/profile' or command == '/профиль':
            user_info = get_user_data(user_id, update.message.from_user.username)
            
            text = f"""
👤 *Профиль игрока*

👤 Игрок: @{update.message.from_user.username or update.message.from_user.first_name}
💰 Баланс: {user_info['balance']:.2f}$
⛏️ Хешрейт: {user_info['hashrate']:.1f} MH/s
🖥️ Видеокарт: {user_info['active_gpus']} шт.
⚡ Энергия: {user_info['energy']:.0f}/{user_info['max_energy']} кВт

📊 *Статистика:*
• Всего добыто: {user_info['total_mined']:.2f}$
• Время майнинга: {user_info.get('mining_time_minutes', 0)} мин.
• Использовано промокодов: {len(user_info.get('promocodes_used', []))}
• Рефералов: {len(user_info.get('referrals', []))}

💎 *Начать игру:* @MineEvoUltra_bot
"""
            
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN
            )

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда мута пользователя"""
    if update.message.chat.id != CHAT_ID:
        return
    
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Использование: /mute @username время(в минутах)")
            return
        
        username = args[0].replace('@', '')
        minutes = int(args[1])
        
        # Получаем ID пользователя по username
        target_user_id = None
        for uid, user_info in user_data.items():
            if user_info['username'].replace('@', '') == username:
                target_user_id = int(uid)
                break
        
        if not target_user_id:
            await update.message.reply_text("❌ Пользователь не найден!")
            return
        
        unmute_time = datetime.now() + timedelta(minutes=minutes)
        muted_users[target_user_id] = unmute_time
        
        await update.message.reply_text(
            f"✅ Пользователь @{username} замучен на {minutes} минут.\n"
            f"⏰ Размут: {unmute_time.strftime('%H:%M:%S')}\n\n"
            f"⚠️ Если мут выдан по ошибке, напишите @HomsyAdmin",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда бана пользователя"""
    if update.message.chat.id != CHAT_ID:
        return
    
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора!")
        return
    
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Использование: /ban @username время(в минутах)")
            return
        
        username = args[0].replace('@', '')
        minutes = int(args[1])
        
        # Получаем ID пользователя по username
        target_user_id = None
        for uid, user_info in user_data.items():
            if user_info['username'].replace('@', '') == username:
                target_user_id = int(uid)
                break
        
        if not target_user_id:
            await update.message.reply_text("❌ Пользователь не найден!")
            return
        
        try:
            await context.bot.ban_chat_member(
                chat_id=CHAT_ID,
                user_id=target_user_id,
                until_date=datetime.now() + timedelta(minutes=minutes)
            )
            await update.message.reply_text(
                f"✅ Пользователь @{username} забанен на {minutes} минут.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Не удалось забанить: {e}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# ========== ПРОДОЛЖЕНИЕ КОДА (НАЧАЛО) ==========
async def handle_missing_callbacks(query, user_id, callback_data):
    """Обработчик для отсутствующих callback-данных"""
    logger.warning(f"Отсутствующий обработчик для callback: {callback_data}")
    await query.edit_message_text(
        "❌ Эта функция временно недоступна.\nПопробуйте позже или обратитесь в поддержку.",
        reply_markup=get_main_keyboard()
    )

async def admin_reload_data(query, user_id):
    """Перезагрузить данные (админ)"""
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ У вас нет прав администратора!")
        return
    
    global user_data, promocodes, support_tickets, events_data
    data = load_data()
    user_data = data['users']
    promocodes = data['promocodes']
    support_tickets = data.get('support_tickets', {})
    events_data = data.get('events', {})
    
    await query.edit_message_text(
        "✅ Данные успешно перезагружены!\n"
        f"👥 Пользователей: {len(user_data)}\n"
        f"🎁 Промокодов: {len(promocodes)}\n"
        f"🆘 Тикетов: {len(support_tickets)}",
        reply_markup=get_admin_keyboard()
    )

# ========== ОБРАБОТЧИК CALLBACK (ПРОДОЛЖЕНИЕ) ==========
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback-запросов"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    logger.info(f"Пользователь {user_id} нажал кнопку: {callback_data}")
    
    # ОТЛАДКА ДЛЯ PVP
    if callback_data.startswith('pvp_'):
        logger.info(f"PVP callback: {callback_data}")
    
    # Проверка подписки
    if callback_data not in ['check_subscription', 'main_menu', 'admin', 'noop']:
        if not await check_subscriptions(user_id, context):
            await require_subscription(update, context)
            return
    
    try:
        # Основные обработчики
        if callback_data == 'main_menu':
            await query.edit_message_text(
                "⚡ *Главное меню*\n\nВыберите действие:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
        
        elif callback_data == 'admin':
            if user_id not in ADMIN_IDS:
                await query.edit_message_text("❌ У вас нет прав администратора!")
                return
            text = f"""
👑 *Панель администратора*

👥 Пользователей: *{len(user_data)}*
💰 Общий баланс: *{sum(u['balance'] for u in user_data.values()):.2f}* $
⛏️ Активных ферм: *{sum(1 for u in user_data.values() if u['active_gpus'] > 0)}*

🎁 Промокодов: *{len(promocodes)}*
🆘 Открытых тикетов: *{sum(1 for t in support_tickets.values() if t.get('status') == 'open')}*

Выберите действие:
"""
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_admin_keyboard()
            )
        
        elif callback_data == 'check_subscription':
            if await check_subscriptions(user_id, context):
                await query.edit_message_text(
                    "✅ *Отлично! Вы подписаны на канал и чат!*\n\n"
                    "Теперь вам доступны все функции бота.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_keyboard()
                )
            else:
                await require_subscription(update, context, "❌ *Вы еще не подписались на канал или чат!*")
        
        elif callback_data == 'mine':
            await mine_crypto(query, user_id, context)
        
        elif callback_data == 'my_gpus':
            await show_my_gpus(query, user_id)
        
        elif callback_data == 'manage_gpus':
            await manage_gpus_activity(query, user_id)

        elif callback_data.startswith('activate_gpu_'):
            gpu_id = callback_data[13:]
            await activate_gpu(query, user_id, gpu_id)

        elif callback_data.startswith('deactivate_gpu_'):
            gpu_id = callback_data[15:]
            await deactivate_gpu(query, user_id, gpu_id)
    
        elif callback_data == 'repair_gpus':
            await repair_gpus(query, user_id)
        
        elif callback_data == 'pvp_menu':
            await show_pvp_menu(query, user_id)
        
        elif callback_data.startswith('pvp_info_'):
            target_id = int(callback_data[9:])
            await show_target_info(query, user_id, target_id)
        
        elif callback_data.startswith('pvp_attack_'):
            target_id = int(callback_data[11:])
            await attack_player(query, user_id, target_id)
        
        elif callback_data == 'protection_menu':
            await show_protection_menu(query, user_id)
        
        elif callback_data.startswith('buy_protection_'):
            plan_id = callback_data[15:]
            await buy_protection(query, user_id, plan_id)
        
        elif callback_data == 'gpu_shop':
            await show_gpu_shop(query, user_id)
        
        elif callback_data.startswith('gpu_tier_'):
            # Обработка пагинации
            parts = callback_data[9:].split('_')
            if len(parts) == 1:
                tier = parts[0]
                await show_gpu_tier(query, user_id, tier, 0)
            elif len(parts) == 2:
                tier = parts[0]
                page = int(parts[1])
                await show_gpu_tier(query, user_id, tier, page)
        
        elif callback_data.startswith('buy_gpu_'):
            gpu_id = callback_data[8:]
            await buy_gpu(query, user_id, gpu_id)
        
        elif callback_data == 'upgrades':
            await show_upgrades(query, user_id)
        
        elif callback_data.startswith('buy_upgrade_'):
            parts = callback_data[12:].split('_')
            if len(parts) >= 2:
                upgrade_type = parts[0]
                level = parts[1]
                await buy_upgrade(query, user_id, upgrade_type, level)
        
        elif callback_data == 'buy_cooling_menu':
            await buy_upgrade_menu(query, user_id, 'cooling')
        
        elif callback_data == 'buy_energy_menu':
            await buy_upgrade_menu(query, user_id, 'energy')
        
        elif callback_data == 'buy_water_cooling_menu':
            await buy_upgrade_menu(query, user_id, 'water_cooling')
        
        elif callback_data == 'buy_farm_menu':
            await buy_upgrade_menu(query, user_id, 'farm')
        
        elif callback_data == 'energy':
            await show_energy(query, user_id)
        
        elif callback_data == 'cool_farm':
            await cool_farm(query, user_id)
        
        elif callback_data == 'refresh_stats':
            await refresh_stats(query, user_id)
        
        elif callback_data == 'stats':
            await show_stats(query, user_id)
        
        elif callback_data == 'tops':
            await show_tops(query, user_id)
        
        elif callback_data == 'referrals':
            await show_referrals(query, user_id)
        
        elif callback_data == 'promo':
            await show_promo(query, user_id)
        
        elif callback_data == 'services':
            await show_services(query, user_id)
        
        elif callback_data == 'support':
            await show_support(query, user_id)
        
        elif callback_data == 'help':
            await show_help(query, user_id)
        
        elif callback_data == 'services_boosters':
            await show_boosters(query, user_id)
        
        elif callback_data == 'services_statuses':
            await show_statuses(query, user_id)
        
        elif callback_data == 'services_skins':
            await show_skins(query, user_id)
        
        elif callback_data.startswith('buy_service_'):
            service_id = callback_data[12:]
            await buy_service(query, user_id, service_id)
        
        elif callback_data == 'create_ticket':
            await create_ticket(query, user_id)
        
        elif callback_data == 'my_tickets':
            await show_my_tickets(query, user_id)
        
        elif callback_data == 'my_referrals':
            await show_my_referrals(query, user_id)
        
        elif callback_data == 'check_promo':
            await check_promo(query, user_id)
        
        elif callback_data == 'top_balance':
            await show_top_balance(query, user_id)
        
        elif callback_data == 'top_referrals':
            await show_top_referrals(query, user_id)
        
        elif callback_data == 'top_hashrate':
            await show_top_hashrate(query, user_id)
        
        elif callback_data == 'top_gpus':
            await show_top_gpus(query, user_id)
        
        elif callback_data == 'top_pvp':
            await show_top_pvp(query, user_id)
        
        elif callback_data == 'top_earned':
            await show_top_earned(query, user_id)
        
        elif callback_data == 'buy_energy_stars':
            await buy_energy_stars(query, user_id)
        
        # АДМИН КНОПКИ
        elif callback_data == 'admin_give_balance':
            await admin_give_balance(query, user_id)
        
        elif callback_data == 'admin_create_promo':
            await admin_create_promo(query, user_id)
        
        elif callback_data == 'admin_give_protection':
            await admin_give_protection(query, user_id)
        
        elif callback_data == 'admin_users':
            await admin_show_users(query, user_id)
        
        elif callback_data == 'admin_give_items':
            await admin_give_items(query, user_id)
        
        elif callback_data == 'admin_give_secret_items':
            await admin_give_secret_items(query, user_id)
        
        elif callback_data == 'admin_create_secret_promo':
            await admin_create_secret_promo(query, user_id)
        
        elif callback_data == 'admin_events':
            await admin_events(query, user_id)
        
        elif callback_data == 'admin_stats':
            await admin_show_stats(query, user_id)
        
        elif callback_data == 'admin_settings':
            await admin_show_settings(query, user_id)
        
        elif callback_data == 'admin_tickets':
            await admin_show_tickets(query, user_id)
        
        elif callback_data == 'admin_change_current_event':
            await admin_change_current_event(query, user_id)
        
        elif callback_data == 'admin_change_next_event':
            await admin_change_next_event(query, user_id)
        
        elif callback_data == 'admin_add_future_event':
            await admin_add_future_event(query, user_id)
        
        elif callback_data.startswith('admin_reply_ticket_'):
            ticket_id = callback_data[19:]
            user_states[user_id] = f'admin_reply_ticket_{ticket_id}'
            await query.edit_message_text(
                f"✏️ *Ответ на тикет #{ticket_id}*\n\n"
                f"Введите ваш ответ сообщением ниже:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_admin_keyboard()
            )
        
        elif callback_data == 'admin_reload_data':
            await admin_reload_data(query, user_id)
        
        elif callback_data == 'admin_clear_rub':
            if user_id in ADMIN_IDS:
                await admin_clear_rub_balance(query, user_id)
            else:
                await query.edit_message_text("❌ У вас нет прав администратора!")
        
        elif callback_data.startswith('admin_do_clear_rub_'):
            if user_id in ADMIN_IDS:
                target_id_str = callback_data.replace('admin_do_clear_rub_', '')
                
                if target_id_str in user_data:
                    target_user = user_data[target_id_str]
                    old_balance = target_user.get('rub_balance', 0)
                    username = target_user.get('username', f'ID: {target_id_str}')
                    
                    # Обнуляем баланс
                    target_user['rub_balance'] = 0
                    save_data()
                    
                    # Логируем
                    log_transaction(user_id, "admin", "CLEAR_RUB_BALANCE", 0, 
                                  f"ID: {target_id_str}, Было: {old_balance}₽")
                    
                    # Уведомляем пользователя
                    try:
                        await query.bot.send_message(
                            chat_id=int(target_id_str),
                            text=f"ℹ️ *Информация о балансе*\n\n"
                                 f"Ваш рублевый баланс был обнулен администратором.\n"
                                 f"💰 Старый баланс: {old_balance}₽\n"
                                 f"💰 Новый баланс: 0₽\n\n"
                                 f"*Причина:* Вывод средств успешно обработан.\n"
                                 f"Если у вас есть вопросы, обратитесь в поддержку: @HomsyAdmin",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except:
                        pass
                    
                    await query.edit_message_text(
                        f"✅ *Рублевый баланс обнулен!*\n\n"
                        f"👤 Пользователь: @{username}\n"
                        f"🆔 ID: `{target_id_str}`\n"
                        f"💰 Было: {old_balance}₽\n"
                        f"💰 Стало: 0₽\n\n"
                        f"✅ Пользователь уведомлен.",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_admin_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Пользователь {target_id_str} не найден!",
                        reply_markup=get_admin_keyboard()
                    )
            else:
                await query.edit_message_text("❌ У вас нет прав администратора!")
        
        elif callback_data == 'noop':
            pass  # Ничего не делаем
        
        else:
            # Если callback не найден, используем общий обработчик
            await handle_missing_callbacks(query, user_id, callback_data)
    
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass  # Игнорируем эту ошибку
        else:
            logger.error(f"BadRequest ошибка: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при обновлении сообщения.",
                reply_markup=get_main_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике callback: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке команды. Пожалуйста, попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
        
# ========== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    if not update.message:
        return
    
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Игнорируем команды
    if message_text.startswith('/'):
        return
    
    # Проверяем состояние пользователя
    if user_id in user_states:
        state = user_states[user_id]
        
        if state == 'enter_promo':
            success, result = await activate_promo(user_id, message_text, context)
            await update.message.reply_text(
                result,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
            user_states.pop(user_id, None)
            
        elif state == 'create_ticket':
            # Создаем тикет
            ticket_id = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
            support_tickets[ticket_id] = {
                'user_id': user_id,
                'username': update.effective_user.username or update.effective_user.first_name,
                'message': message_text,
                'status': 'open',
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat()
            }
            save_data()
            
            # Уведомляем админов
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🆘 *НОВЫЙ ТИКЕТ*\n\n"
                             f"📝 ID: `{ticket_id}`\n"
                             f"👤 Пользователь: {update.effective_user.username or update.effective_user.first_name} (ID: `{user_id}`)\n"
                             f"📅 Создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                             f"💬 Сообщение: {message_text}\n\n"
                             f"Для ответа используйте команду /admin",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
            
            await update.message.reply_text(
                f"✅ *Тикет создан!*\n\n"
                f"📝 Номер тикета: `{ticket_id}`\n"
                f"👨‍💼 Администратор ответит вам в ближайшее время.\n"
                f"💬 Вы можете отслеживать статус в разделе 'Мои тикеты'.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
            user_states.pop(user_id, None)
            
        elif state.startswith('admin_'):
            await handle_admin_actions(update, context)

# ========== КОМАНДА МЕНЮ ==========
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /menu для главного меню"""
    user_id = update.effective_user.id
    
    if not await check_subscriptions(user_id, context):
        await require_subscription(update, context)
        return
    
    await update.message.reply_text(
        "⚡ *Главное меню*\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== КОМАНДА ПРОФИЛЬ ==========
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profile для просмотра профиля"""
    user_id = update.effective_user.id
    
    if not await check_subscriptions(user_id, context):
        await require_subscription(update, context)
        return
    
    user_info = get_user_data(user_id)
    
    # Экранируем username
    display_username = update.effective_user.username or update.effective_user.first_name
    display_username = display_username.replace('_', '\\_').replace('*', '\\*').replace('', '\\').replace('[', '\\[')
    
    text = f"""
👤 *Профиль игрока*

👤 Игрок: @{display_username}
🆔 ID: {user_id}
📅 Зарегистрирован: {datetime.fromisoformat(user_info['registered']).strftime('%d\\.%m\\.%Y')}
💰 Баланс: *{user_info['balance']:.2f}* \\$
🇷🇺 Рублевый баланс: *{user_info.get('rub_balance', 0):.2f}* ₽
⛏️ Хешрейт: *{user_info['hashrate']:.1f}* MH/s
🖥 Видеокарт: *{user_info['active_gpus']}* шт\.
⚡️ Энергия: *{user_info['energy']:.0f}/{user_info['max_energy']}* кВт

📊 *Реферальная статистика:*
• Приглашено: *{len(user_info.get('referrals', []))}*
• Подписались на каналы: *{len(user_info.get('referrals_subscribed', []))}*
• Заработано $: *{user_info.get('ref_earned', 0):.2f}* \\$
• Заработано ₽: *{user_info.get('ref_rub_earned', 0):.2f}* ₽

💎 *Реферальная ссылка:*
https://t.me/{BOT_USERNAME[1:]}?start=ref{user_id}

💰 *Вывод рублей:*
• Минимальная сумма: 50₽
• На карты российских банков
• Для вывода пиши @HomsyAdmin
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 Рефералы", callback_data='referrals')],
        [InlineKeyboardButton("💰 Вывод рублей", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
    ]
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== КОМАНДА ПРАВИЛА ==========
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /rules для показа правил"""
    user_id = update.effective_user.id
    
    if not await check_subscriptions(user_id, context):
        await require_subscription(update, context)
        return
    
    text = """
📜 *Правила Mine Evo Ultra*

1. *Уважайте других игроков*
   - Запрещены оскорбления, угрозы и травля
   - Будьте вежливы в общении

2. *Честная игра*
   - Запрещено использование читов и эксплойтов
   - Запрещено создание мультиаккаунтов для накрутки

3. *Защита аккаунта*
   - Не передавайте свои данные третьим лицам
   - Бот не запрашивает пароли от аккаунтов

4. *Торговля и обмен*
   - Все сделки совершаются на ваш страх и риск
   - Администрация не несет ответственности за мошенничество

5. *Контент*
   - Запрещен контент для взрослых
   - Запрещена реклама без согласования

6. *Технические вопросы*
   - Сообщайте о багах в поддержку
   - Не злоупотребляйте ошибками в системе

7. *Модерация*
   - Решения администрации окончательны
   - Нарушение правил ведет к бану

⚠️ *Наказания за нарушения:*
- Первое нарушение: предупреждение
- Второе нарушение: мут на 24 часа
- Третье нарушение: бан навсегда

📢 *Контакты:*
- Поддержка: @HomsyAdmin
- Жалобы и предложения: через тикет-систему
"""
    
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ========== ОБРАБОТКА НОВЫХ УЧАСТНИКОВ ЧАТА ==========
async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка новых участников чата"""
    if update.chat_member:
        chat_id = update.chat_member.chat.id
        user_id = update.chat_member.new_chat_member.user.id
        status = update.chat_member.new_chat_member.status
        
        # Приветствуем новых участников в чате
        if status == 'member' and chat_id == CHAT_ID:
            try:
                welcome_text = f"""
👋 Добро пожаловать в чат Mine Evo Ultra, {update.chat_member.new_chat_member.user.first_name}!

📢 *Важная информация:*
• Основной канал: {CHANNEL_USERNAME}
• Бот для игры: {BOT_USERNAME}
• Поддержка: {SUPPORT_USERNAME}

🎮 *Как начать играть:*
1. Подпишитесь на канал {CHANNEL_USERNAME}
2. Перейдите в бота {BOT_USERNAME}
3. Нажмите /start и начинайте майнить!

💡 *Правила чата:*
• Уважайте других участников
• Запрещен спам и флуд
• Запрещена реклама без согласования

Приятной игры! 🚀
"""
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Ошибка приветствия нового участника: {e}")

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("rules", rules_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Регистрируем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Регистрируем обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик обновлений участников чата
    application.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    
    # Регистрируем обработчики модерации (только для чата)
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("ban", ban_user))
    
    # Обработчик сообщений в чате
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_chat_message))
    
    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ========== ЗАПУСК ПРОГРАММЫ ==========
if __name__ == '__main__':
    main()

# ========== КОНЕЦ КОДА ==========