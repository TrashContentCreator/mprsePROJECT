import os
import time
import base64
import hashlib
import threading
import socket
import sys
import logging
import traceback
import requests
from datetime import datetime
from cryptography.fernet import Fernet
from colorama import init, Fore, Style

# Инициализация colorama
init(autoreset=True)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='secure_chat.log',
    filemode='a'
)
logger = logging.getLogger('SecureChat')

class SecureChat:
    def __init__(self):
        try:
            # Основные настройки
            self.chat_file = "Z:/chat.txt"
            self.username = socket.gethostname()
            self.display_name = self.username
            self.console_lock = threading.Lock()
            self.running = True
            self.message_queue = []
            self.current_version = "1.2.0"  # Обновлена версия
            self.github_user = "TrashContentCreator"
            self.github_repo = "mprsePROJECT"
            
            # URLs для обновлений
            self.update_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/main/mprse.exe"
            self.version_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/main/version.txt"
            self.beta_update_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/beta/mprse.exe"
            self.beta_version_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/beta/version.txt"
            
            # Статистика для дебаггера
            self.start_time = time.time()
            self.messages_processed = 0
            self.errors_count = 0
            self.last_activity = time.time()
            self.last_error = None
            self.debug_mode = False
            
            # Комнаты чата с паролями
            self.rooms = {
                "general": {
                    "file": "Z:/chat_general.txt",
                    "password": None,
                    "users": set()
                }
            }
            self.current_room = "general"
            
            # Список заглушенных пользователей
            self.muted_users = set()
            
            # Активные пользователи
            self.active_users = set()
            self.last_seen = {}
            
            # Темы оформления
            self.themes = {
                "default": {
                    "banner": Fore.CYAN,
                    "system": Fore.YELLOW,
                    "username": Fore.GREEN,
                    "message": Fore.WHITE,
                    "background": ""
                },
                "dark": {
                    "banner": Fore.BLUE,
                    "system": Fore.LIGHTBLUE_EX,
                    "username": Fore.LIGHTCYAN_EX,
                    "message": Fore.LIGHTWHITE_EX,
                    "background": ""
                },
                "colorful": {
                    "banner": Fore.MAGENTA,
                    "system": Fore.YELLOW,
                    "username": Fore.CYAN,
                    "message": Fore.LIGHTGREEN_EX,
                    "background": ""
                },
                "matrix": {
                    "banner": Fore.GREEN,
                    "system": Fore.GREEN,
                    "username": Fore.GREEN,
                    "message": Fore.LIGHTGREEN_EX,
                    "background": ""
                },
                "sunset": {
                    "banner": Fore.RED,
                    "system": Fore.YELLOW,
                    "username": Fore.LIGHTYELLOW_EX,
                    "message": Fore.LIGHTRED_EX,
                    "background": ""
                }
            }
            self.current_theme = "default"
            
            # Цвета для разных пользователей
            self.user_colors = [
                Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE,
                Fore.MAGENTA, Fore.CYAN, Fore.WHITE
            ]
            
            # Обновленные примечания
            self.update_notes = """
            Примечания к обновлениям:
            --------------------------
            Версия 1.2.0:
            - Добавлена возможность обновления до бета-версии
            - Добавлена команда 'update beta' для обновления до бета-версии
            - Улучшена система обновлений
            - Исправлены ошибки в работе чата
            
            Версия 1.1.0:
            - Добавлена команда 'users' для просмотра активных пользователей
            - Добавлена команда 'username' для изменения отображаемого имени
            - Добавлена команда 'room' для создания/входа в комнаты с паролем
            - Добавлена команда 'mute' для заглушения пользователей
            - Добавлена команда 'theme' для изменения темы оформления
            - Добавлена команда 'help' для просмотра списка команд
            - Добавлена команда 'logout' для выхода из чата
            - Добавлена команда 'debug' для отображения отладочной информации
            
            Версия 1.0.0:
            - Добавлена команда 'clear' для очистки чата
            - Добавлена команда 'update' для проверки обновлений
            - Добавлена команда 'notes' для просмотра примечаний
            - Улучшен интерфейс чата
            - Исправлены ошибки отображения
            """
            
            logger.info("Инициализация SecureChat завершена успешно")
        except Exception as e:
            self.log_error("Ошибка при инициализации", e)
            raise

    def log_error(self, message, exception=None):
        """Логирование ошибок с трассировкой стека"""
        self.errors_count += 1
        self.last_error = f"{message}: {str(exception)}" if exception else message
        
        error_msg = f"{message}: {str(exception)}" if exception else message
        logger.error(error_msg)
        
        if exception:
            logger.error(traceback.format_exc())
        
        return error_msg

    def get_debug_info(self):
        """Получение отладочной информации о работе приложения"""
        uptime = time.time() - self.start_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Проверка доступности файлов
        file_status = {}
        for room_name, room_info in self.rooms.items():
            file_path = room_info["file"]
            try:
                file_exists = os.path.exists(file_path)
                file_writable = os.access(file_path, os.W_OK) if file_exists else False
                file_status[room_name] = {
                    "path": file_path,
                    "exists": file_exists,
                    "writable": file_writable
                }
            except Exception as e:
                file_status[room_name] = {
                    "path": file_path,
                    "error": str(e)
                }
        
        debug_info = f"""
        === Отладочная информация ===
        Время работы: {int(hours)}ч {int(minutes)}м {int(seconds)}с
        Обработано сообщений: {self.messages_processed}
        Количество ошибок: {self.errors_count}
        Последняя активность: {datetime.fromtimestamp(self.last_activity).strftime('%H:%M:%S')}
        Последняя ошибка: {self.last_error if self.last_error else "нет"}
        
        Текущая комната: {self.current_room}
        Активных пользователей: {len(self.active_users)}
        Заглушенных пользователей: {len(self.muted_users)}
        
        Статус файлов:
        """
        
        for room, status in file_status.items():
            debug_info += f"  - {room}: "
            if "error" in status:
                debug_info += f"ОШИБКА: {status['error']}\n"
            else:
                debug_info += f"{'ДОСТУПЕН' if status['exists'] else 'НЕ СУЩЕСТВУЕТ'}, "
                debug_info += f"{'ДОСТУПЕН ДЛЯ ЗАПИСИ' if status['writable'] else 'НЕДОСТУПЕН ДЛЯ ЗАПИСИ'}\n"
        
        return debug_info

    def get_help_text(self):
        return """
        Доступные команды:
        ------------------
        - quit/logout    : Выйти из чата
        - clear          : Очистить историю чата для всех
        - help           : Показать список доступных команд
        - notes          : Показать примечания к обновлениям
        - update         : Проверить наличие обновлений
        - users          : Показать список активных пользователей
        - username <имя> : Изменить отображаемое имя
        - room <имя> [пароль] : Создать/войти в комнату чата (пароль опционален)
        - mute <имя>     : Заглушить пользователя (не видеть его сообщения)
        - unmute <имя>   : Разглушить пользователя
        - theme <имя>    : Изменить тему оформления
                           Доступные темы: default, dark, colorful, matrix, sunset
        - debug          : Показать отладочную информацию
        """

    def get_user_color(self, username):
        try:
            return self.user_colors[hash(username) % len(self.user_colors)]
        except Exception as e:
            self.log_error("Ошибка при получении цвета пользователя", e)
            return Fore.WHITE

    def get_theme_color(self, element):
        try:
            return self.themes.get(self.current_theme, self.themes["default"]).get(element, Fore.WHITE)
        except Exception as e:
            self.log_error("Ошибка при получении цвета темы", e)
            return Fore.WHITE

    def derive_key(self, password: str):
        try:
            key = hashlib.sha256(password.encode()).digest()
            return base64.urlsafe_b64encode(key)
        except Exception as e:
            self.log_error("Ошибка при генерации ключа", e)
            raise

    def encrypt_message(self, message, username, key):
        try:
            full_message = f"{username}: {message}"
            cipher = Fernet(key)
            return cipher.encrypt(full_message.encode()).decode()
        except Exception as e:
            self.log_error("Ошибка при шифровании сообщения", e)
            raise

    def decrypt_message(self, encrypted_message, key):
        try:
            cipher = Fernet(key)
            return cipher.decrypt(encrypted_message.encode()).decode()
        except Exception:
            # Ошибки дешифрования не логируем, так как они ожидаемы при неверном ключе
            return None

    def clear_chat_file(self):
        try:
            # Очищаем файл чата
            chat_file_path = self.rooms[self.current_room]["file"]
            
            # Проверяем доступность файла
            if not os.path.exists(os.path.dirname(chat_file_path)):
                os.makedirs(os.path.dirname(chat_file_path), exist_ok=True)
                logger.info(f"Создана директория для файла чата: {os.path.dirname(chat_file_path)}")
            
            with open(chat_file_path, "w", encoding="utf-8") as chat_file:
                chat_file.write("")
            logger.info(f"Файл чата очищен: {chat_file_path}")

            # Добавляем системное сообщение об очистке чата с временной меткой
            timestamp = str(int(time.time()))
            system_message = f"CLEAR_CHAT_COMMAND:{self.display_name}:{timestamp}"
            encrypted_message = self.encrypt_message(system_message, "System", self.current_key)

            with open(chat_file_path, "a", encoding="utf-8") as chat_file:
                chat_file.write(encrypted_message + "\n")

            # Очищаем локальную очередь сообщений
            self.message_queue.clear()
            self.add_message("System", f"Чат очищен пользователем {self.display_name}")
            return True
        except Exception as e:
            error_msg = self.log_error("Ошибка при очистке чата", e)
            self.add_message("System", f"Ошибка при очистке чата: {error_msg}")
            return False

    def list_active_users(self):
        try:
            # Удаляем пользователей, которые не были активны более 5 минут
            current_time = time.time()
            inactive_users = [user for user in self.active_users 
                             if current_time - self.last_seen.get(user, 0) > 300]
            
            for user in inactive_users:
                self.active_users.discard(user)
                if user in self.last_seen:
                    del self.last_seen[user]
            
            # Добавляем текущего пользователя
            self.active_users.add(self.display_name)
            self.last_seen[self.display_name] = current_time
            
            # Формируем список активных пользователей
            users_in_room = [user for user in self.active_users 
                            if user in self.rooms[self.current_room]["users"]]
            
            if not users_in_room:
                users_in_room = [self.display_name]
            
            users_str = ", ".join(users_in_room)
            self.add_message("System", f"Активные пользователи в комнате {self.current_room}: {users_str}")
            
            # Показываем заглушенных пользователей
            if self.muted_users:
                muted_str = ", ".join(self.muted_users)
                self.add_message("System", f"Заглушенные пользователи: {muted_str}")
        except Exception as e:
            error_msg = self.log_error("Ошибка при получении списка пользователей", e)
            self.add_message("System", f"Ошибка: {error_msg}")

    def change_username(self, new_username):
        try:
            if not new_username or len(new_username) < 3:
                self.add_message("System", "Имя пользователя должно содержать не менее 3 символов")
                return False
            
            old_name = self.display_name
            self.display_name = new_username
            
            # Обновляем в списке активных пользователей
            if old_name in self.active_users:
                self.active_users.discard(old_name)
            self.active_users.add(new_username)
            
            # Обновляем в комнате
            room_info = self.rooms[self.current_room]
            if old_name in room_info["users"]:
                room_info["users"].discard(old_name)
            room_info["users"].add(new_username)
            
            self.add_message("System", f"Ваше имя изменено на {new_username}")
            logger.info(f"Пользователь изменил имя с {old_name} на {new_username}")
            return True
        except Exception as e:
            error_msg = self.log_error("Ошибка при изменении имени пользователя", e)
            self.add_message("System", f"Ошибка: {error_msg}")
            return False

    def switch_room(self, room_name, password=None):
        try:
            # Если комната существует, проверяем пароль
            if room_name in self.rooms:
                room_password = self.rooms[room_name]["password"]
                if room_password and room_password != password:
                    self.add_message("System", f"Неверный пароль для комнаты {room_name}")
                    return False
            # Если комнаты нет, создаем ее
            else:
                self.rooms[room_name] = {
                    "file": f"Z:/chat_{room_name}.txt",
                    "password": password,
                    "users": set()
                }
                self.add_message("System", f"Создана новая комната: {room_name}")
                logger.info(f"Создана новая комната: {room_name}")
                
                # Создаем файл для новой комнаты
                try:
                    # Проверяем доступность директории
                    room_file = self.rooms[room_name]["file"]
                    dir_path = os.path.dirname(room_file)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                        
                    with open(room_file, "w", encoding="utf-8") as f:
                        pass
                except Exception as e:
                    error_msg = self.log_error(f"Ошибка при создании файла комнаты {room_name}", e)
                    self.add_message("System", f"Ошибка при создании файла комнаты: {error_msg}")
                    return False
            
            # Выходим из текущей комнаты
            if self.display_name in self.rooms[self.current_room]["users"]:
                self.rooms[self.current_room]["users"].discard(self.display_name)
            
            # Входим в новую комнату
            self.current_room = room_name
            self.rooms[room_name]["users"].add(self.display_name)
            self.chat_file = self.rooms[room_name]["file"]
            
            self.add_message("System", f"Вы переключились в комнату: {room_name}")
            logger.info(f"Пользователь {self.display_name} переключился в комнату {room_name}")
            self.refresh_display()
            return True
        except Exception as e:
            error_msg = self.log_error(f"Ошибка при переключении в комнату {room_name}", e)
            self.add_message("System", f"Ошибка: {error_msg}")
            return False

    def mute_user(self, username):
        try:
            if username == self.display_name:
                self.add_message("System", "Вы не можете заглушить себя")
                return False
            
            self.muted_users.add(username)
            self.add_message("System", f"Пользователь {username} заглушен")
            logger.info(f"Пользователь {username} заглушен")
            return True
        except Exception as e:
            error_msg = self.log_error(f"Ошибка при заглушении пользователя {username}", e)
            self.add_message("System", f"Ошибка: {error_msg}")
            return False

    def unmute_user(self, username):
        try:
            if username in self.muted_users:
                self.muted_users.discard(username)
                self.add_message("System", f"Пользователь {username} разглушен")
                logger.info(f"Пользователь {username} разглушен")
                return True
            else:
                self.add_message("System", f"Пользователь {username} не был заглушен")
                return False
        except Exception as e:
            error_msg = self.log_error(f"Ошибка при разглушении пользователя {username}", e)
            self.add_message("System", f"Ошибка: {error_msg}")
            return False

    def change_theme(self, theme_name):
        try:
            if theme_name in self.themes:
                self.current_theme = theme_name
                self.add_message("System", f"Тема изменена на: {theme_name}")
                logger.info(f"Тема изменена на: {theme_name}")
                return True
            else:
                available_themes = ", ".join(self.themes.keys())
                self.add_message("System", f"Тема {theme_name} не найдена! Доступные темы: {available_themes}")
                return False
        except Exception as e:
            error_msg = self.log_error(f"Ошибка при изменении темы на {theme_name}", e)
            self.add_message("System", f"Ошибка: {error_msg}")
            return False

    def check_update(self):
        try:
            self.add_message("System", "Проверка обновлений...")
            
            # Проверяем доступность сервера
            try:
                response = requests.get(self.version_url, timeout=5)
                latest_version = response.text.strip()
            except requests.exceptions.RequestException as e:
                self.add_message("System", f"Не удалось подключиться к серверу обновлений: {e}")
                return False

            self.add_message("System", f"Текущая версия: {self.current_version}")
            self.add_message("System", f"Последняя версия: {latest_version}")

            if latest_version > self.current_version:
                self.add_message("System", f"Доступна новая версия: {latest_version}")
                self.add_message("System", "Загрузка обновления...")

                try:
                    response = requests.get(self.update_url, stream=True, timeout=30)
                    with open("mprse_new.exe", "wb") as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                except Exception as e:
                    self.add_message("System", f"Ошибка при загрузке обновления: {e}")
                    return False

                self.add_message("System", "Обновление загружено. Создание установщика...")

                update_script = """@echo off
echo Обновление Secure Chat...
timeout /t 2 /nobreak >nul
taskkill /f /im mprse.exe 2>nul
del /f /q mprse_old.exe 2>nul
move /y mprse.exe mprse_old.exe >nul
move /y mprse_new.exe mprse.exe >nul
start "" mprse.exe
del /f /q update.bat
"""
                with open("update.bat", "w", encoding="utf-8") as f:
                    f.write(update_script)

                self.add_message("System", "Обновление готово. Перезапуск программы...")
                logger.info(f"Обновление до версии {latest_version} загружено. Перезапуск программы.")
                os.system("start update.bat")
                sys.exit(0)
            else:
                self.add_message("System", "У вас установлена последняя версия.")
                return True
        except Exception as e:
            error_msg = self.log_error("Ошибка при проверке обновлений", e)
            self.add_message("System", f"Ошибка при проверке обновлений: {error_msg}")
            return False

    def refresh_display(self):
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            banner_color = self.get_theme_color("banner")
            system_color = self.get_theme_color("system")
            
            print(f"""
{banner_color}╔════════════════════════════════════════════════╗
║         Защищенный Чат - Версия {self.current_version}         ║
║         Шифрованная Связь в Сети                ║
╚════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
            
            print(f"\n{self.get_theme_color('username')}Подключено как: {self.display_name}{Style.RESET_ALL}")
            print(f"{system_color}Комната: {self.current_room}{Style.RESET_ALL}")
            print(f"{system_color}Тема: {self.current_theme}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Введите 'help' для просмотра списка команд{Style.RESET_ALL}")
            print("-" * 50)

            for msg in self.message_queue:
                username, message = msg
                
                # Пропускаем сообщения от заглушенных пользователей
                if username in self.muted_users:
                    continue
                    
                if username == "System":
                    user_color = system_color
                else:
                    user_color = self.get_user_color(username)
                    
                message_color = self.get_theme_color("message")
                print(f"{user_color}{username}{Style.RESET_ALL}: {message_color}{message}{Style.RESET_ALL}")

            print("> ", end='', flush=True)
        except Exception as e:
            self.log_error("Ошибка при обновлении дисплея", e)
            print(f"\n{Fore.RED}Ошибка при обновлении дисплея: {e}{Style.RESET_ALL}")

    def add_message(self, username, message):
        try:
            with self.console_lock:
                self.message_queue.append((username, message))
                if len(self.message_queue) > 50:
                    self.message_queue = self.message_queue[-50:]
                self.refresh_display()
                
            self.messages_processed += 1
            self.last_activity = time.time()
        except Exception as e:
            self.log_error("Ошибка при добавлении сообщения", e)
            print(f"\n{Fore.RED}Ошибка при добавлении сообщения: {e}{Style.RESET_ALL}")

    def send_message(self, key):
        self.current_key = key
        while self.running:
            try:
                message = input()
                self.last_activity = time.time()

                with self.console_lock:
                    self.refresh_display()

                # Обработка команд
                if message.lower() in ["quit", "logout"]:
                    logger.info(f"Пользователь {self.display_name} вышел из чата")
                    self.running = False
                    break
                elif message.lower() == "clear":
                    self.clear_chat_file()
                    continue
                elif message.lower() == "update":
                    self.check_update()
                    continue
                elif message.lower() == "notes":
                    self.add_message("System", self.update_notes)
                    continue
                elif message.lower() == "help":
                    self.add_message("System", self.get_help_text())
                    continue
                elif message.lower() == "users":
                    self.list_active_users()
                    continue
                elif message.lower() == "debug":
                    self.add_message("System", self.get_debug_info())
                    continue
                elif message.lower().startswith("username "):
                    new_username = message.split(" ", 1)[1]
                    self.change_username(new_username)
                    continue
                elif message.lower().startswith("room "):
                    parts = message.split(" ")
                    if len(parts) >= 2:
                        room_name = parts[1]
                        password = parts[2] if len(parts) > 2 else None
                        self.switch_room(room_name, password)
                    continue
                elif message.lower().startswith("mute "):
                    username = message.split(" ", 1)[1]
                    self.mute_user(username)
                    continue
                elif message.lower().startswith("unmute "):
                    username = message.split(" ", 1)[1]
                    self.unmute_user(username)
                    continue
                elif message.lower().startswith("theme "):
                    theme_name = message.split(" ", 1)[1]
                    self.change_theme(theme_name)
                    continue

                # Отправка обычного сообщения
                if message.strip():
                    try:
                        encrypted_message = self.encrypt_message(message, self.display_name, key)
                        
                        # Проверяем доступность файла чата
                        chat_file_path = self.chat_file
                        dir_path = os.path.dirname(chat_file_path)
                        if not os.path.exists(dir_path):
                            os.makedirs(dir_path, exist_ok=True)
                            
                        with open(chat_file_path, "a", encoding="utf-8") as chat_file:
                            chat_file.write(encrypted_message + "\n")
                            
                        self.add_message(self.display_name, message)
                        logger.debug(f"Отправлено сообщение от {self.display_name}")
                    except Exception as e:
                        error_msg = self.log_error("Ошибка при отправке сообщения", e)
                        self.add_message("System", f"Ошибка при отправке сообщения: {error_msg}")

            except Exception as e:
                error_msg = self.log_error("Ошибка в обработке ввода", e)
                print(f"\n{Fore.RED}Ошибка: {error_msg}{Style.RESET_ALL}")
                time.sleep(1)

    def receive_messages(self, key):
        seen_messages = set()
        last_clear_time = "0"
        self.refresh_display()

        while self.running:
            try:
                chat_file_path = self.rooms[self.current_room]["file"]
                
                # Проверяем существование файла и директории
                dir_path = os.path.dirname(chat_file_path)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    logger.info(f"Создана директория для файла чата: {dir_path}")
                    
                if not os.path.exists(chat_file_path):
                    open(chat_file_path, "w").close()
                    logger.info(f"Создан файл чата: {chat_file_path}")

                # Проверяем доступность файла для чтения
                if not os.access(chat_file_path, os.R_OK):
                    logger.warning(f"Файл чата недоступен для чтения: {chat_file_path}")
                    time.sleep(5)
                    continue

                with open(chat_file_path, "r", encoding="utf-8") as chat_file:
                    lines = chat_file.readlines()

                for line in lines:
                    line = line.strip()
                    if line and line not in seen_messages:
                        decrypted = self.decrypt_message(line, key)
                        if decrypted:
                            if "CLEAR_CHAT_COMMAND:" in decrypted:
                                parts = decrypted.split(":")
                                if len(parts) == 3:
                                    username = parts[1]
                                    clear_time = parts[2]
                                    if clear_time > last_clear_time:
                                        last_clear_time = clear_time
                                        self.message_queue.clear()
                                        self.add_message("System", f"Чат очищен пользователем {username}")
                                    seen_messages.add(line)
                            else:
                                parts = decrypted.split(":", 1)
                                if len(parts) == 2:
                                    username = parts[0].strip()
                                    message = parts[1].strip()
                                    
                                    # Обновляем список активных пользователей
                                    if username != "System":
                                        self.active_users.add(username)
                                        self.last_seen[username] = time.time()
                                        self.rooms[self.current_room]["users"].add(username)
                                    
                                    if username != self.display_name:
                                        self.add_message(username, message)
                                    seen_messages.add(line)

                time.sleep(0.5)

            except Exception as e:
                error_msg = self.log_error("Ошибка при чтении сообщений", e)
                print(f"\n{Fore.RED}Ошибка при чтении сообщений: {error_msg}{Style.RESET_ALL}")
                time.sleep(5)

    def print_banner(self):
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            banner_color = self.get_theme_color("banner")
            print(f"""
{banner_color}╔════════════════════════════════════════════════╗
║         Защищенный Чат - Версия {self.current_version}         ║
║         Шифрованная Связь в Сети                ║
╚════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        except Exception as e:
            self.log_error("Ошибка при отображении баннера", e)
            print(f"\n{Fore.RED}Ошибка при отображении баннера: {e}{Style.RESET_ALL}")

    def run(self):
        try:
            self.print_banner()
            logger.info("Запуск приложения")

            # Создаем директорию для файлов чата
            try:
                os.makedirs(os.path.dirname(self.chat_file), exist_ok=True)
                logger.info(f"Проверка директории для файлов чата: {os.path.dirname(self.chat_file)}")
            except Exception as e:
                error_msg = self.log_error("Ошибка при создании директории для файлов чата", e)
                print(f"\n{Fore.RED}Ошибка: {error_msg}{Style.RESET_ALL}")
                
                # Пробуем использовать локальную директорию
                self.chat_file = "chat.txt"
                for room_name in self.rooms:
                    self.rooms[room_name]["file"] = f"chat_{room_name}.txt"
                
                print(f"\n{Fore.YELLOW}Используем локальную директорию для файлов чата.{Style.RESET_ALL}")
                logger.info("Переключение на локальную директорию для файлов чата")
            
            # Создаем файлы для всех комнат
            for room_name, room_info in self.rooms.items():
                room_file = room_info["file"]
                try:
                    if not os.path.exists(room_file):
                        with open(room_file, "w", encoding="utf-8") as f:
                            pass
                        logger.info(f"Создан файл для комнаты {room_name}: {room_file}")
                except Exception as e:
                    error_msg = self.log_error(f"Ошибка при создании файла для комнаты {room_name}", e)
                    print(f"\n{Fore.RED}Ошибка: {error_msg}{Style.RESET_ALL}")

            # Запрашиваем пароль
            try:
                password = input(f"{Fore.YELLOW}Введите пароль для входа в чат: {Style.RESET_ALL}")
                key = self.derive_key(password)
            except Exception as e:
                error_msg = self.log_error("Ошибка при обработке пароля", e)
                print(f"\n{Fore.RED}Критическая ошибка: {error_msg}{Style.RESET_ALL}")
                time.sleep(5)
                return
            
            # Добавляем пользователя в текущую комнату
            self.rooms[self.current_room]["users"].add(self.display_name)
            self.active_users.add(self.display_name)
            self.last_seen[self.display_name] = time.time()

            # Запускаем потоки для отправки и получения сообщений
            send_thread = threading.Thread(target=self.send_message, args=(key,))
            receive_thread = threading.Thread(target=self.receive_messages, args=(key,))

            send_thread.daemon = True
            receive_thread.daemon = True

            receive_thread.start()
            send_thread.start()

            logger.info("Потоки отправки и получения сообщений запущены")
            
            # Запускаем поток мониторинга файлов
            def monitor_files():
                while self.running:
                    try:
                        for room_name, room_info in self.rooms.items():
                            file_path = room_info["file"]
                            file_exists = os.path.exists(file_path)
                            file_writable = os.access(file_path, os.W_OK) if file_exists else False
                            logger.debug(f"Мониторинг файла {file_path}: существует={file_exists}, доступен для записи={file_writable}")
                    except Exception as e:
                        self.log_error("Ошибка при мониторинге файлов", e)
                    time.sleep(60)  # Проверяем раз в минуту
            
            monitor_thread = threading.Thread(target=monitor_files)
            monitor_thread.daemon = True
            monitor_thread.start()

            # Ожидаем завершения потока отправки сообщений
            send_thread.join()

        except Exception as e:
            error_msg = self.log_error("Критическая ошибка в основном потоке", e)
            print(f"\n{Fore.RED}Критическая ошибка: {error_msg}{Style.RESET_ALL}")
        finally:
            self.running = False
            logger.info("Завершение работы приложения")
            print(f"\n{Fore.YELLOW}До свидания!{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        chat = SecureChat()
        chat.run()
    except Exception as e:
        print(f"\n{Fore.RED}Критическая ошибка при запуске приложения: {e}{Style.RESET_ALL}")
        logger.critical(f"Критическая ошибка при запуске приложения: {e}")
        logger.critical(traceback.format_exc())
        print("\nПодробная информация об ошибке записана в файл secure_chat.log")
        print("Нажмите Enter для выхода...")
        input()
