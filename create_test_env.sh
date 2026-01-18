#!/bin/bash
# create_test_env.sh - Создание тестового окружения АСДУЕ

echo "Создание тестового окружения АСДУЕ..."

# Создаем структуру
mkdir -p templates static/uploads static/results

# Создаем базовый конфиг сетей
cat > networks.json << EOF
[
    "192.168.1.0/24",
    "10.0.0.0/24"
]
EOF

# Создаем requirements.txt
cat > requirements.txt << EOF
Flask==2.3.3
python-nmap==0.7.1
ping3==4.0.4
pandas==2.0.3
openpyxl==3.1.2
python-docx==0.8.11
EOF

echo "Структура создана!"
echo "Теперь установите зависимости: pip install -r requirements.txt"
echo "Запустите приложение: python app.py"