import re
import urllib.request
import urllib.error
import os
import socket


class MyFile:
    
    
    def __init__(self, path: str, mode: str = "read"):
        
        self.path = path
        self.mode = mode.lower()
        self.file = None
        
        # Проверяем допустимость режима
        valid_modes = ["read", "write", "append", "url"]
        if self.mode not in valid_modes:
            raise ValueError(f"Недопустимый режим '{mode}'. Допустимые режимы: {valid_modes}")
        
        # Для режима read проверяем существование файла
        if self.mode == "read" and not self._file_exists(path):
            raise FileNotFoundError(f"Файл '{path}' не существует")
        
        # Если режим url, проверяем что передан URL и он доступен
        if self.mode == "url":
            if not self._is_url(path):
                raise ValueError(f"'{path}' не является валидным URL для режима 'url'")
            # Проверяем доступность URL
            if not self._check_url_availability(path):
                raise ConnectionError(f"URL '{path}' недоступен или не существует")
    
    def _is_url(self, path: str) -> bool:
       
        url_patterns = ["http://", "https://", "ftp://", "file://"]
        return any(path.startswith(pattern) for pattern in url_patterns)
    
    def _file_exists(self, filepath: str) -> bool:
    
        # Проверяем, не является ли путь директорией
        if os.path.isdir(filepath):
            return False
        return os.path.exists(filepath)
    
    def _check_url_availability(self, url: str, timeout: int = 5) -> bool:
        
        try:
            # Устанавливаем заголовки
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            # Открываем URL с таймаутом
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.getcode() == 200
                
        except urllib.error.HTTPError as e:
            # Проверяем, что это не ошибка 404 (страница не найдена)
            if e.code == 404:
                return False
            # Для других HTTP ошибок считаем URL доступным (но с ошибкой)
            return True
        except (urllib.error.URLError, socket.timeout, TimeoutError):
            return False
        except Exception:
            return False
    
    def _check_file_access(self, filepath: str, mode: str) -> bool:

        try:
            # Для режима записи/добавления проверяем доступность директории
            if mode in ['w', 'a']:
                dir_path = os.path.dirname(filepath)
                if dir_path and not os.path.exists(dir_path):
                    # Пытаемся создать директорию
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                    except:
                        return False
                
                # Проверяем права на запись
                if os.path.exists(filepath):
                    return os.access(filepath, os.W_OK)
                else:
                    # Для нового файла проверяем права на запись в директорию
                    dir_path = os.path.dirname(filepath) or '.'
                    return os.access(dir_path, os.W_OK)
            
            # Для режима чтения проверяем права на чтение
            elif mode == 'r':
                return os.access(filepath, os.R_OK)
                
            return True
        except:
            return False
    
    def _open_file(self):
        
        if self.mode == "read":
            if not self._file_exists(self.path):
                raise FileNotFoundError(f"Файл '{self.path}' не существует")
            if not self._check_file_access(self.path, 'r'):
                raise PermissionError(f"Нет прав на чтение файла '{self.path}'")
            self.file = open(self.path, 'r', encoding='utf-8')
        elif self.mode == "write":
            if not self._check_file_access(self.path, 'w'):
                raise PermissionError(f"Нет прав на запись в файл '{self.path}'")
            self.file = open(self.path, 'w', encoding='utf-8')
        elif self.mode == "append":
            if not self._check_file_access(self.path, 'a'):
                raise PermissionError(f"Нет прав на добавление в файл '{self.path}'")
            self.file = open(self.path, 'a', encoding='utf-8')
    
    def _close_file(self):
        
        if self.file and not self.file.closed:
            self.file.close()
    
    def read(self) -> str:
       
        if self.mode != "read":
            raise ValueError(f"Метод read() доступен только в режиме 'read', текущий режим: '{self.mode}'")
        
        # Проверяем существование файла перед открытием
        if not self._file_exists(self.path):
            raise FileNotFoundError(f"Файл '{self.path}' не существует")
        
        try:
            self._open_file()
            return self.file.read()
        except FileNotFoundError as e:
            raise e
        except PermissionError as e:
            raise e
        except Exception as e:
            raise IOError(f"Ошибка при чтении файла '{self.path}': {e}")
        finally:
            self._close_file()
    
    def write(self, content: str) -> bool:
        
        if self.mode not in ["write", "append"]:
            raise ValueError(f"Метод write() доступен только в режимах 'write' или 'append', текущий режим: '{self.mode}'")
        
        # Проверяем доступ к файлу перед открытием
        mode_char = 'w' if self.mode == "write" else 'a'
        if not self._check_file_access(self.path, mode_char):
            raise PermissionError(f"Нет прав на запись в файл '{self.path}'")
        
        try:
            self._open_file()
            self.file.write(content)
            return True
        except PermissionError as e:
            raise e
        except Exception as e:
            raise IOError(f"Ошибка при записи в файл '{self.path}': {e}")
        finally:
            self._close_file()
    
    def read_url(self) -> str:
        
        if self.mode != "url":
            raise ValueError(f"Метод read_url() доступен только в режиме 'url', текущий режим: '{self.mode}'")
        
        # Проверяем доступность URL перед запросом
        if not self._check_url_availability(self.path):
            raise ConnectionError(f"URL '{self.path}' недоступен или не существует")
        
        try:
            # Устанавливаем заголовки, чтобы не блокировали как бота
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(self.path, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                # Проверяем статус ответа
                if response.getcode() != 200:
                    raise ConnectionError(f"URL вернул статус {response.getcode()}")
                
                # Пытаемся определить кодировку
                content = response.read()
                
                # Пробуем разные кодировки
                encodings = ['utf-8', 'cp1251', 'koi8-r', 'iso-8859-1']
                
                for encoding in encodings:
                    try:
                        return content.decode(encoding)
                    except UnicodeDecodeError:
                        continue
                
                # Если ни одна кодировка не подошла, возвращаем как utf-8 с заменой ошибок
                return content.decode('utf-8', errors='replace')
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ConnectionError(f"Страница '{self.path}' не найдена (404)")
            else:
                raise ConnectionError(f"HTTP ошибка {e.code}: {e.reason} для URL '{self.path}'")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Ошибка URL '{self.path}': {e.reason}")
        except TimeoutError:
            raise ConnectionError(f"Таймаут при загрузке URL '{self.path}'")
        except ConnectionError as e:
            raise e
        except Exception as e:
            raise IOError(f"Ошибка при чтении URL '{self.path}': {e}")
    
    def count_urls(self) -> int:
        
        if self.mode != "url":
            raise ValueError(f"Метод count_urls() доступен только в режиме 'url', текущий режим: '{self.mode}'")
        
        try:
            html_content = self.read_url()
            
            # Регулярное выражение для поиска URL в HTML
            url_patterns = [
                r'href=["\'](https?://[^"\']+)["\']',
                r'src=["\'](https?://[^"\']+)["\']',
                r'url\(["\']?(https?://[^"\')]+)["\']?\)',
            ]
            
            urls = set()
            
            for pattern in url_patterns:
                found_urls = re.findall(pattern, html_content, re.IGNORECASE)
                urls.update(found_urls)
            
            general_pattern = r'https?://[^\s<>"\']+'
            general_urls = re.findall(general_pattern, html_content, re.IGNORECASE)
            urls.update(general_urls)
            
            return len(urls)
            
        except ConnectionError as e:
            print(f"Ошибка: {e}")
            return 0
        except Exception as e:
            print(f"Предупреждение: не удалось подсчитать URL: {e}")
            return 0
    
    def write_url(self, filepath: str) -> bool:
        
        if self.mode != "url":
            raise ValueError(f"Метод write_url() доступен только в режиме 'url', текущий режим: '{self.mode}'")
        
        # Проверяем, что можем создать файл для записи
        if os.path.exists(filepath):
            if not self._check_file_access(filepath, 'w'):
                raise PermissionError(f"Нет прав на запись в файл '{filepath}'")
        else:
            dir_path = os.path.dirname(filepath) or '.'
            if not os.access(dir_path, os.W_OK):
                raise PermissionError(f"Нет прав на создание файла в директории '{dir_path}'")
        
        try:
            # Читаем содержимое URL
            content = self.read_url()
            
            # Создаем объект для записи в файл
            file_writer = MyFile(filepath, "write")
            success = file_writer.write(content)
            
            if success:
                print(f"Содержимое URL успешно сохранено в файл: {filepath}")
            
            return success
            
        except (ConnectionError, PermissionError) as e:
            raise e
        except Exception as e:
            raise IOError(f"Ошибка при сохранении содержимого URL в файл: {e}")
    
    def __enter__(self):
        
        if self.mode in ["read", "write", "append"]:
            self._open_file()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
    
        if self.mode in ["read", "write", "append"]:
            self._close_file()
    
    def __repr__(self):
        return f"MyFile(path='{self.path}', mode='{self.mode}')"
    
    def __del__(self):
        
        self._close_file()


def display_menu():
    
    print("\n" + "=" * 50)
    print("МЕНЮ РАБОТЫ С ФАЙЛАМИ И URL")
    print("=" * 50)
    print("1. Работа с файлом (чтение/запись)")
    print("2. Работа с URL")
    print("3. Выход")
    print("=" * 50)


def file_operations():
    
    print("\n" + "-" * 30)
    print("РАБОТА С ФАЙЛАМИ")
    print("-" * 30)
    
    # Запрос пути к файлу
    while True:
        file_path = input("Введите путь к файлу: ").strip()
        if file_path:
            break
        print("Ошибка: путь к файлу не может быть пустым")
    
    # Выбор режима работы
    print("\nВыберите режим работы:")
    print("1. Чтение файла")
    print("2. Запись в файл (перезапись)")
    print("3. Добавление в файл")
    
    mode_choice = input("Введите номер режима (1-3): ").strip()
    
    mode_map = {
        "1": "read",
        "2": "write", 
        "3": "append"
    }
    
    if mode_choice not in mode_map:
        print("Ошибка: неверный выбор режима")
        return
    
    mode = mode_map[mode_choice]
    
    try:
        # Создаем объект MyFile
        file_obj = MyFile(file_path, mode)
        
        if mode == "read":
            # Чтение файла
            content = file_obj.read()
            print(f"\nСодержимое файла '{file_path}':")
            print("=" * 40)
            print(content)
            print("=" * 40)
            
        elif mode in ["write", "append"]:
            # Запись или добавление в файл
            print(f"\nВведите содержимое для {'записи' if mode == 'write' else 'добавления'}:")
            print("(Для завершения ввода введите пустую строку или 'END' на отдельной строке)")
            print("-" * 40)
            
            lines = []
            line_num = 1
            while True:
                line = input(f"Строка {line_num}: ").strip()
                if line == "" or line.upper() == "END":
                    break
                lines.append(line)
                line_num += 1
            
            content = "\n".join(lines)
            
            # Подтверждение для перезаписи существующего файла
            if mode == "write" and os.path.exists(file_path):
                confirm = input(f"\nФайл '{file_path}' уже существует. Перезаписать? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("Операция отменена")
                    return
            
            # Выполняем запись
            success = file_obj.write(content)
            if success:
                action = "записано" if mode == "write" else "добавлено"
                print(f"\nСодержимое успешно {action} в файл '{file_path}'")
                
    except FileNotFoundError as e:
        print(f"\nОшибка: {e}")
        print("Проверьте правильность пути к файлу")
    except PermissionError as e:
        print(f"\nОшибка: {e}")
        print("Запустите программу с правами администратора или выберите другой файл")
    except Exception as e:
        print(f"\nОшибка: {e}")


def url_operations():
    
    print("\n" + "-" * 30)
    print("РАБОТА С URL")
    print("-" * 30)
    
    # Запрос URL
    while True:
        url = input("Введите URL (например, https://example.com): ").strip()
        if url:
            break
        print("Ошибка: URL не может быть пустым")
    
    # Проверяем, что URL начинается с протокола
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        print(f"Используется URL: {url}")
    
    try:
        # Проверяем доступность URL перед созданием объекта
        print("Проверяем доступность URL...")
        
        # Создаем временный объект для проверки
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.getcode() == 200:
                    print("URL доступен")
                else:
                    print(f" URL вернул статус {response.getcode()}")
        except Exception as e:
            print(f" URL может быть недоступен: {e}")
            proceed = input("Продолжить? (y/N): ").strip().lower()
            if proceed != 'y':
                return
        
        # Создаем объект MyFile в режиме url
        url_obj = MyFile(url, "url")
        
        # Выбор операции с URL
        print("\nВыберите операцию:")
        print("1. Прочитать содержимое страницы")
        print("2. Подсчитать количество ссылок на странице")
        print("3. Сохранить содержимое страницы в файл")
        
        operation = input("Введите номер операции (1-3): ").strip()
        
        if operation == "1":
            # Чтение содержимого URL
            try:
                content = url_obj.read_url()
                print(f"\nСодержимое страницы '{url}':")
                print("=" * 60)
                print(content[:1000] + ("..." if len(content) > 1000 else ""))
                print("=" * 60)
                print(f"Общий размер: {len(content)} символов")
            except ConnectionError as e:
                print(f"\n Ошибка подключения: {e}")
            except Exception as e:
                print(f"\n Ошибка: {e}")
            
        elif operation == "2":
            # Подсчет ссылок
            try:
                url_count = url_obj.count_urls()
                print(f"\n На странице '{url}' найдено {url_count} URL-адресов")
            except Exception as e:
                print(f"\n Ошибка при подсчете ссылок: {e}")
            
        elif operation == "3":
            # Сохранение содержимого в файл
            while True:
                save_path = input("Введите путь для сохранения файла: ").strip()
                if not save_path:
                    # Генерируем имя файла на основе URL
                    domain = url.split("//")[-1].split("/")[0].replace('.', '_')
                    save_path = f"{domain}_content.html"
                    print(f"Используется имя файла по умолчанию: {save_path}")
                    break
                
                # Проверяем, не является ли путь директорией
                if os.path.isdir(save_path):
                    print("Ошибка: указанный путь является директорией, а не файлом")
                    continue
                
                # Проверяем существование файла
                if os.path.exists(save_path):
                    confirm = input(f"Файл '{save_path}' уже существует. Перезаписать? (y/N): ").strip().lower()
                    if confirm != 'y':
                        print("Введите другой путь к файлу")
                        continue
                
                break
            
            try:
                success = url_obj.write_url(save_path)
                if success:
                    print(f"\n Содержимое успешно сохранено в файл '{save_path}'")
                    print(f"Размер файла: {os.path.getsize(save_path)} байт")
            except PermissionError as e:
                print(f"\n Ошибка доступа: {e}")
                print("Попробуйте выбрать другую директорию или запустить программу с правами администратора")
            except ConnectionError as e:
                print(f"\n Ошибка подключения: {e}")
            except Exception as e:
                print(f"\n Ошибка: {e}")
                
        else:
            print("\n Ошибка: неверный выбор операции")
            
    except ValueError as e:
        print(f"\n Ошибка: {e}")
    except ConnectionError as e:
        print(f"\n Ошибка подключения: {e}")
        print("Проверьте:")
        print("1. Наличие интернет-соединения")
        print("2. Правильность URL")
        print("3. Доступность сайта")
    except Exception as e:
        print(f"\nНепредвиденная ошибка: {e}")


def main():
    
    print("=" * 50)
    print("ПРОГРАММА ДЛЯ РАБОТЫ С ФАЙЛАМИ И URL")
    print("=" * 50)
    print("Версия с проверкой существования файлов и ссылок")
    print("=" * 50)
    
    while True:
        display_menu()
        
        choice = input("\nВыберите действие (1-3): ").strip()
        
        if choice == "1":
            file_operations()
        elif choice == "2":
            url_operations()
        elif choice == "3":
            print("\nДо свидания!")
            break
        else:
            print("\nОшибка: введите число от 1 до 3")
        
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем.")
    except Exception as e:
        print(f"\nПроизошла непредвиденная ошибка: {e}")
