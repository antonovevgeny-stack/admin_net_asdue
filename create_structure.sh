#!/bin/bash
# Скрипт создания структуры проекта admin_net_asdue для Debian

set -e  # Прерывать выполнение при ошибках

echo "========================================"
echo " Создание структуры проекта АСДУЕ"
echo " Для Debian/Linux"
echo "========================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для создания директории
create_dir() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}[OK]${NC} Создана директория: $1"
    else
        echo -e "${YELLOW}[EXISTS]${NC} Директория уже существует: $1"
    fi
}

# Функция для создания файла (если не существует)
create_file() {
    if [ ! -f "$1" ]; then
        touch "$1"
        echo -e "${GREEN}[OK]${NC} Создан файл: $1"
    else
        echo -e "${YELLOW}[EXISTS]${NC} Файл уже существует: $1"
    fi
}

# Функция для создания файла с содержимым (если не существует)
create_file_with_content() {
    if [ ! -f "$1" ]; then
        cat > "$1" << EOL
$2
EOL
        echo -e "${GREEN}[OK]${NC} Создан файл: $1"
    else
        echo -e "${YELLOW}[EXISTS]${NC} Файл уже существует: $1"
    fi
}

# Проверка прав администратора (опционально)
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}[INFO]${NC} Скрипт запущен с правами root"
fi

echo -e "\n${YELLOW}[1/5]${NC} Создание основных директорий..."

# Основные директории проекта
create_dir "scanner"
create_dir "static/css"
create_dir "static/js"
create_dir "static/images"
create_dir "templates"
create_dir "uploads"
create_dir "results"
create_dir "docs"
create_dir "logs"
create_dir "config"
create_dir "migrations"
create_dir "tests"

echo -e "\n${YELLOW}[2/5]${NC} Создание основных файлов..."

# Основные файлы (только если не существуют)
create_file "app.py"
create_file "requirements.txt"
create_file "Dockerfile"
create_file "docker-compose.yml"
create_file "nginx.conf"
create_file "deploy.sh"
create_file "manage.sh"
create_file "networks.json"
create_file "README.md"
create_file ".gitignore"
create_file ".env.example"
create_file "config/settings.py"

echo -e "\n${YELLOW}[3/5]${NC} Создание модулей сканирования..."

# Файлы в scanner/
create_file_with_content "scanner/__init__.py" "# Модуль сканирования сети"
create_file_with_content "scanner/network_scanner.py" "#!/usr/bin/env python3\n\"\"\"\nМодуль сканирования сети\n\"\"\"\n\nimport nmap\nimport socket\nfrom datetime import datetime\n\nclass NetworkScanner:\n    def __init__(self):\n        self.nm = nmap.PortScanner()\n    \n    def scan_network(self, network_cidr):\n        \"\"\"Сканирование сети\"\"\"\n        print(f\"[{datetime.now()}] Сканирование сети: {network_cidr}\")\n        return []\n"
create_file_with_content "scanner/export_results.py" "#!/usr/bin/env python3\n\"\"\"\nМодуль экспорта результатов\n\"\"\"\nimport pandas as pd\nfrom docx import Document\n\n\ndef export_to_excel(results, filename):\n    \"\"\"Экспорт в Excel\"\"\"\n    df = pd.DataFrame(results)\n    df.to_excel(filename, index=False)\n    return filename\n\n\ndef export_to_word(results, filename):\n    \"\"\"Экспорт в Word\"\"\"\n    doc = Document()\n    doc.add_heading('Результаты сканирования сети', 0)\n    doc.save(filename)\n    return filename\n"
create_file_with_content "scanner/host_db.py" "#!/usr/bin/env python3\n\"\"\"\nМодуль работы с базой данных хостов\n\"\"\"\nimport sqlite3\nimport json\nfrom datetime import datetime\n\nclass HostDB:\n    def __init__(self, db_path='hosts.db'):\n        self.conn = sqlite3.connect(db_path)\n        self.create_tables()\n    \n    def create_tables(self):\n        \"\"\"Создание таблиц\"\"\"\n        cursor = self.conn.cursor()\n        cursor.execute('''\n            CREATE TABLE IF NOT EXISTS hosts (\n                id INTEGER PRIMARY KEY,\n                ip TEXT UNIQUE,\n                hostname TEXT,\n                mac TEXT,\n                vendor TEXT,\n                os TEXT,\n                first_seen TIMESTAMP,\n                last_seen TIMESTAMP\n            )\n        ''')\n        self.conn.commit()\n"

echo -e "\n${YELLOW}[4/5]${NC} Создание веб-шаблонов..."

# HTML шаблоны
create_file_with_content "templates/index.html" "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Аудит сети АСДУЕ</title>\n</head>\n<body>\n    <h1>Аудит сети АСДУЕ</h1>\n    <p>Система сканирования и мониторинга сети</p>\n</body>\n</html>"
create_file_with_content "templates/networks.html" "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Настройка сетей</title>\n</head>\n<body>\n    <h1>Настройка сетей для сканирования</h1>\n</body>\n</html>"
create_file_with_content "templates/scan.html" "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Сканирование сети</title>\n</head>\n<body>\n    <h1>Сканирование сети</h1>\n    <div id=\"progress\">\n        <p>Прогресс: <span id=\"progress-value\">0%</span></p>\n    </div>\n</body>\n</html>"
create_file_with_content "templates/results.html" "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Результаты</title>\n</head>\n<body>\n    <h1>Результаты сканирования</h1>\n</body>\n</html>"
create_file_with_content "templates/layout.html" "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>{% block title %}АСДУЕ{% endblock %}</title>\n    {% block styles %}{% endblock %}\n</head>\n<body>\n    <header>\n        <nav>\n            <a href=\"/\">Главная</a>\n            <a href=\"/scan\">Сканирование</a>\n            <a href=\"/networks\">Настройка</a>\n            <a href=\"/results\">Результаты</a>\n        </nav>\n    </header>\n    \n    <main>\n        {% block content %}{% endblock %}\n    </main>\n    \n    <footer>\n        <p>АСДУЕ &copy; 2024</p>\n    </footer>\n    \n    {% block scripts %}{% endblock %}\n</body>\n</html>"

echo -e "\n${YELLOW}[5/5]${NC} Создание конфигурационных файлов..."

# Конфигурационные файлы
create_file_with_content "requirements.txt" "# Основные зависимости\nFlask>=2.3.0\npython-nmap>=0.7.0\npandas>=2.0.0\nopenpyxl>=3.1.0\npython-docx>=0.8.0\ngunicorn>=20.0.0\npython-dotenv>=1.0.0\n"
create_file_with_content "networks.json" "[\n    \"192.168.1.0/24\",\n    \"10.0.0.0/24\"\n]"
create_file_with_content ".gitignore" "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\nwheels/\n*.egg-info/\n.installed.cfg\n*.egg\n\n# Virtual Environment\nvenv/\nenv/\n\n# IDE\n.vscode/\n.idea/\n*.swp\n*.swo\n\n# OS\n.DS_Store\nThumbs.db\n\n# Project specific\nuploads/*\n!uploads/.gitkeep\nresults/*\n!results/.gitkeep\nlogs/*\n!logs/.gitkeep\n*.db\n.env\n"
create_file_with_content "deploy.sh" "#!/bin/bash\n# Скрипт развертывания проекта\n\necho \"Развертывание АСДУЕ...\"\n\n# Остановка существующих контейнеров\ndocker-compose down 2>/dev/null\n\n# Сборка образов\necho \"Сборка Docker образов...\"\ndocker-compose build\n\n# Запуск контейнеров\necho \"Запуск контейнеров...\"\ndocker-compose up -d\n\necho \"Готово!\"\necho \"Приложение доступно по адресу: http://localhost\""
create_file_with_content "manage.sh" "#!/bin/bash\n# Скрипт управления проектом\n\ncase \"\$1\" in\n    start)\n        docker-compose up -d\n        ;;\n    stop)\n        docker-compose down\n        ;;\n    restart)\n        docker-compose restart\n        ;;\n    logs)\n        docker-compose logs -f\n        ;;\n    status)\n        docker-compose ps\n        ;;\n    update)\n        git pull\n        docker-compose build\n        docker-compose up -d\n        ;;\n    *)\n        echo \"Использование: \$0 {start|stop|restart|logs|status|update}\"\n        exit 1\n        ;;\nesac"

# Делаем скрипты исполняемыми
chmod +x deploy.sh manage.sh 2>/dev/null

# Создаем пустые файлы в папках, чтобы они не были пустыми
touch uploads/.gitkeep
touch results/.gitkeep
touch logs/.gitkeep

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Структура проекта успешно создана!${NC}"
echo -e "${GREEN}========================================${NC}"

# Выводим дерево проекта
echo -e "\n${YELLOW}Структура проекта:${NC}"
find . -type f -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.txt" -o -name "*.json" -o -name "*.sh" -o -name "*.yml" -o -name "Dockerfile" -o -name "README.md" -o -name ".gitignore" | sort | head -30

echo -e "\n${YELLOW}Команды для продолжения:${NC}"
echo "1. Установите зависимости: pip install -r requirements.txt"
echo "2. Запустите приложение: python app.py"
echo "3. Или используйте Docker: ./deploy.sh"
echo -e "\n${YELLOW}Проверьте настройки в файлах:${NC}"
echo "- networks.json - список сетей для сканирования"
echo "- .env.example - пример переменных окружения"
echo -e "\n${GREEN}Готово! Проект подготовлен для разработки.${NC}"