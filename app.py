#!/usr/bin/env python3
"""
Минимальная версия для тестирования сканера сети АСДУЕ
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import threading
import time
from datetime import datetime
import socket
import subprocess
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['NETWORKS_FILE'] = 'networks.json'

# Создаем необходимые директории
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Глобальные переменные для статуса
scan_status = {
    'is_scanning': False,
    'progress': 0,
    'current_network': '',
    'total_networks': 0,
    'scanned_networks': 0,
    'results': [],
    'start_time': None
}

class SimpleNetworkScanner:
    """Упрощенный сканер для тестирования"""
    
    def scan_network(self, network_cidr):
        """Тестовое сканирование - возвращает mock данные"""
        print(f"[TEST] Сканируем сеть: {network_cidr}")
        time.sleep(2)  # Имитация работы
        
        # Mock данные для теста
        mock_hosts = []
        base_ip = network_cidr.split('/')[0]
        ip_parts = base_ip.split('.')
        
        for i in range(1, 6):  # 5 тестовых устройств
            ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{i + 10}"
            host_info = {
                'ip': ip,
                'hostnames': [f'device-{i}.local'],
                'mac': f'00:11:22:33:44:{i:02d}',
                'vendor': ['VMware', 'Dell', 'HP', 'Cisco', 'TP-Link'][i % 5],
                'os': ['Linux', 'Windows 10', 'Windows Server', 'Ubuntu', 'MacOS'][i % 5],
                'status': 'Online',
                'last_seen': datetime.now().isoformat()
            }
            mock_hosts.append(host_info)
        
        return mock_hosts

@app.route('/')
def index():
    """Главная страница АСДУЕ"""
    modules = [
        {'name': 'Сканирование сети', 'url': '/scan', 'icon': 'radar', 'desc': 'Запуск аудита сети'},
        {'name': 'Настройка сетей', 'url': '/networks', 'icon': 'gear', 'desc': 'Управление подсетями'},
        {'name': 'Результаты', 'url': '/results', 'icon': 'table', 'desc': 'Просмотр и выгрузка'},
        {'name': 'Документация', 'url': '/docs', 'icon': 'book', 'desc': 'Инструкции'},
    ]
    return render_template('index.html', 
                         title="Аудит сети АСДУЕ",
                         modules=modules,
                         version="1.0.0")

@app.route('/networks', methods=['GET', 'POST'])
def networks():
    """Управление сетями для сканирования"""
    networks_file = 'networks.json'
    
    if request.method == 'POST':
        if 'network' in request.form:
            network = request.form['network'].strip()
            if network:
                # Загружаем текущий список
                if os.path.exists(networks_file):
                    with open(networks_file, 'r') as f:
                        networks_list = json.load(f)
                else:
                    networks_list = []
                
                # Добавляем новую сеть
                if network not in networks_list:
                    networks_list.append(network)
                    with open(networks_file, 'w') as f:
                        json.dump(networks_list, f, indent=2)
    
    # Загружаем список сетей
    if os.path.exists(networks_file):
        with open(networks_file, 'r') as f:
            networks_list = json.load(f)
    else:
        networks_list = ["192.168.1.0/24", "10.0.0.0/24"]
        with open(networks_file, 'w') as f:
            json.dump(networks_list, f, indent=2)
    
    return render_template('networks.html', networks=networks_list)

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    """Страница сканирования"""
    if request.method == 'POST':
        if not scan_status['is_scanning']:
            # Запускаем сканирование в отдельном потоке
            thread = threading.Thread(target=start_scanning, daemon=True)
            thread.start()
            return jsonify({'status': 'started'})
    
    # Загружаем список сетей
    networks_file = 'networks.json'
    if os.path.exists(networks_file):
        with open(networks_file, 'r') as f:
            networks_list = json.load(f)
    else:
        networks_list = []
    
    return render_template('scan.html', 
                         networks=networks_list,
                         is_scanning=scan_status['is_scanning'])

@app.route('/scan/status')
def scan_status_api():
    """API для получения статуса сканирования"""
    return jsonify(scan_status)

@app.route('/results')
def results():
    """Страница с результатами"""
    return render_template('results.html', 
                         results=scan_status['results'],
                         scan_count=len(scan_status['results']))

@app.route('/api/scan/stop', methods=['POST'])
def stop_scan():
    """Остановка сканирования"""
    if scan_status['is_scanning']:
        scan_status['is_scanning'] = False
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'idle'})

def start_scanning():
    """Запуск сканирования (в отдельном потоке)"""
    global scan_status
    
    # Загружаем список сетей
    networks_file = 'networks.json'
    if os.path.exists(networks_file):
        with open(networks_file, 'r') as f:
            networks_list = json.load(f)
    else:
        networks_list = []
    
    # Настраиваем статус
    scan_status['is_scanning'] = True
    scan_status['progress'] = 0
    scan_status['results'] = []
    scan_status['start_time'] = datetime.now().isoformat()
    scan_status['total_networks'] = len(networks_list)
    scan_status['scanned_networks'] = 0
    
    # Сканируем каждую сеть
    scanner = SimpleNetworkScanner()
    
    for i, network in enumerate(networks_list):
        if not scan_status['is_scanning']:
            break
            
        scan_status['current_network'] = network
        print(f"Сканирование сети: {network}")
        
        try:
            # Сканируем сеть
            results = scanner.scan_network(network)
            scan_status['results'].extend(results)
        except Exception as e:
            print(f"Ошибка при сканировании {network}: {e}")
        
        # Обновляем прогресс
        scan_status['scanned_networks'] = i + 1
        scan_status['progress'] = int((i + 1) / len(networks_list) * 100) if networks_list else 0
        
        # Небольшая пауза между сетями
        time.sleep(1)
    
    scan_status['is_scanning'] = False
    print("Сканирование завершено!")

@app.route('/health')
def health():
    """Проверка работоспособности"""
    return jsonify({
        'status': 'ok',
        'service': 'network-audit-asdue',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Аудит сети АСДУЕ - Тестовая версия")
    print("=" * 50)
    print(f"Сервер запускается на http://127.0.0.1:5000")
    print(f"Доступные эндпоинты:")
    print(f"  /          - Главная страница")
    print(f"  /networks  - Настройка сетей")
    print(f"  /scan      - Сканирование сети")
    print(f"  /results   - Результаты")
    print(f"  /health    - Проверка здоровья")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)