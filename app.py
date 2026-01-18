#!/usr/bin/env python3
"""
АСДУЕ - Веб-сканер сети с реальным сканированием
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import json
import os
import threading
import time
from datetime import datetime
import csv
from docx import Document
from scanner import scanner

app = Flask(__name__)

# Создаем директории
for folder in ['uploads', 'results', 'logs', 'static', 'templates']:
    os.makedirs(folder, exist_ok=True)

# Конфигурация
app.config['NETWORKS_FILE'] = 'networks.json'

# Глобальные переменные для статуса сканирования
scan_data = {
    'is_scanning': False,
    'progress': 0,
    'current_network': '',
    'total_networks': 0,
    'scanned_networks': 0,
    'hosts_found': 0,
    'results': [],
    'start_time': None,
    'end_time': None,
    'scan_thread': None
}

@app.route('/')
def index():
    """Главная страница АСДУЕ"""
    modules = [
        {'name': '📡 Сканирование сети', 'url': '/scan', 'desc': 'Запуск аудита сети', 'icon': 'radar'},
        {'name': '⚙️ Настройка сетей', 'url': '/networks', 'desc': 'Управление подсетями', 'icon': 'gear'},
        {'name': '📊 Результаты', 'url': '/results', 'desc': 'Просмотр и выгрузка', 'icon': 'table'},
        {'name': '📈 Статистика', 'url': '/stats', 'desc': 'Аналитика сети', 'icon': 'chart'},
    ]
    
    # Статистика
    stats = {
        'total_scans': len(scan_data['results']),
        'last_scan': scan_data['end_time'] if scan_data['end_time'] else 'Не выполнялось',
        'networks_count': len(load_networks())
    }
    
    return render_template('index.html', 
                         title="Аудит сети АСДУЕ",
                         modules=modules,
                         stats=stats,
                         is_scanning=scan_data['is_scanning'])

@app.route('/networks', methods=['GET', 'POST'])
def networks():
    """Управление сетями для сканирования"""
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'add':
            network = request.form.get('network', '').strip()
            if network:
                networks_list = load_networks()
                if network not in networks_list:
                    networks_list.append(network)
                    save_networks(networks_list)
        
        elif action == 'delete':
            network_to_delete = request.form.get('network_to_delete', '')
            if network_to_delete:
                networks_list = load_networks()
                if network_to_delete in networks_list:
                    networks_list.remove(network_to_delete)
                    save_networks(networks_list)
        
        elif action == 'clear':
            save_networks([])
        
        elif 'network_file' in request.files:
            file = request.files['network_file']
            if file.filename:
                content = file.read().decode('utf-8')
                new_networks = [line.strip() for line in content.split('\n') if line.strip()]
                networks_list = load_networks()
                networks_list.extend(new_networks)
                networks_list = list(set(networks_list))  # Убираем дубли
                save_networks(networks_list)
    
    networks_list = load_networks()
    return render_template('networks.html', networks=networks_list)

@app.route('/scan', methods=['GET', 'POST'])
def scan_page():
    """Страница сканирования"""
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        
        if action == 'start' and not scan_data['is_scanning']:
            # Запускаем сканирование в отдельном потоке
            scan_thread = threading.Thread(target=start_scanning, daemon=True)
            scan_thread.start()
            scan_data['scan_thread'] = scan_thread
            return jsonify({'status': 'started', 'message': 'Сканирование запущено'})
        
        elif action == 'stop' and scan_data['is_scanning']:
            scan_data['is_scanning'] = False
            return jsonify({'status': 'stopping', 'message': 'Остановка сканирования...'})
    
    networks_list = load_networks()
    return render_template('scan.html', 
                         networks=networks_list,
                         is_scanning=scan_data['is_scanning'],
                         scan_data=scan_data)

@app.route('/api/scan/status')
def scan_status():
    """API для получения статуса сканирования"""
    return jsonify(scan_data)

@app.route('/api/scan/start', methods=['POST'])
def api_start_scan():
    """API для запуска сканирования"""
    if scan_data['is_scanning']:
        return jsonify({'status': 'error', 'message': 'Сканирование уже выполняется'})
    
    scan_thread = threading.Thread(target=start_scanning, daemon=True)
    scan_thread.start()
    scan_data['scan_thread'] = scan_thread
    
    return jsonify({'status': 'success', 'message': 'Сканирование запущено'})

@app.route('/api/scan/stop', methods=['POST'])
def api_stop_scan():
    """API для остановки сканирования"""
    scan_data['is_scanning'] = False
    return jsonify({'status': 'success', 'message': 'Сканирование останавливается'})

@app.route('/results')
def results():
    """Страница с результатами сканирования"""
    return render_template('results.html', 
                         results=scan_data['results'],
                         hosts_count=len(scan_data['results']),
                         last_scan=scan_data['end_time'])

@app.route('/export/csv')
def export_csv():
    """Экспорт результатов в CSV"""
    if not scan_data['results']:
        return jsonify({'status': 'error', 'message': 'Нет данных для экспорта'}), 400
    
    filename = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join('results', filename)
    
    # Определяем все возможные ключи
    all_keys = set()
    for host in scan_data['results']:
        all_keys.update(host.keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(scan_data['results'])
    
    return send_file(filepath, as_attachment=True)

@app.route('/export/docx')
def export_docx():
    """Экспорт результатов в Word"""
    if not scan_data['results']:
        return jsonify({'status': 'error', 'message': 'Нет данных для экспорта'}), 400
    
    filename = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = os.path.join('results', filename)
    
    doc = Document()
    
    # Заголовок
    doc.add_heading('Результаты сканирования сети АСДУЕ', 0)
    
    # Общая информация
    doc.add_paragraph(f'Дата сканирования: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    doc.add_paragraph(f'Найдено устройств: {len(scan_data["results"])}')
    doc.add_paragraph(f'Время начала: {scan_data.get("start_time", "N/A")}')
    doc.add_paragraph(f'Время окончания: {scan_data.get("end_time", "N/A")}')
    
    doc.add_page_break()
    
    # Таблица с результатами
    doc.add_heading('Обнаруженные устройства', level=1)
    
    table = doc.add_table(rows=1, cols=7)
    table.style = 'Light Grid Accent 1'
    
    # Заголовки таблицы
    headers = table.rows[0].cells
    headers[0].text = 'IP адрес'
    headers[1].text = 'Имя хоста'
    headers[2].text = 'MAC адрес'
    headers[3].text = 'Производитель'
    headers[4].text = 'ОС'
    headers[5].text = 'Статус'
    headers[6].text = 'Время сканирования'
    
    # Данные
    for host in scan_data['results']:
        row_cells = table.add_row().cells
        row_cells[0].text = host.get('ip', '')
        row_cells[1].text = host.get('hostname', '')
        row_cells[2].text = host.get('mac', '')
        row_cells[3].text = host.get('vendor', '')
        row_cells[4].text = host.get('os', '')
        row_cells[5].text = host.get('status', '')
        row_cells[6].text = host.get('scan_time', '')
    
    doc.save(filepath)
    return send_file(filepath, as_attachment=True)

@app.route('/stats')
def stats():
    """Страница статистики"""
    stats_data = {
        'total_hosts': len(scan_data['results']),
        'vendors': {},
        'os_distribution': {},
        'scan_history': []
    }
    
    # Анализ производителей
    for host in scan_data['results']:
        vendor = host.get('vendor', 'Unknown')
        stats_data['vendors'][vendor] = stats_data['vendors'].get(vendor, 0) + 1
        
        os_name = host.get('os', 'Unknown')
        stats_data['os_distribution'][os_name] = stats_data['os_distribution'].get(os_name, 0) + 1
    
    return render_template('stats.html', stats=stats_data)

@app.route('/health')
def health():
    """Проверка здоровья сервиса"""
    return jsonify({
        'status': 'healthy',
        'service': 'network-audit-asdue',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'scanning': scan_data['is_scanning'],
        'hosts_in_memory': len(scan_data['results'])
    })

def load_networks():
    """Загрузка списка сетей"""
    networks_file = app.config['NETWORKS_FILE']
    if os.path.exists(networks_file):
        try:
            with open(networks_file, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_networks(networks):
    """Сохранение списка сетей"""
    with open(app.config['NETWORKS_FILE'], 'w') as f:
        json.dump(networks, f, indent=2)

def start_scanning():
    """Функция запуска сканирования (работает в отдельном потоке)"""
    global scan_data
    
    # Сброс предыдущих данных
    scan_data['is_scanning'] = True
    scan_data['progress'] = 0
    scan_data['results'] = []
    scan_data['current_network'] = ''
    scan_data['start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    scan_data['end_time'] = None
    scan_data['hosts_found'] = 0
    
    networks_list = load_networks()
    scan_data['total_networks'] = len(networks_list)
    scan_data['scanned_networks'] = 0
    
    if not networks_list:
        print("Нет сетей для сканирования!")
        scan_data['is_scanning'] = False
        return
    
    print(f"Начинаем сканирование {len(networks_list)} сетей...")
    
    # Сканируем каждую сеть
    all_results = []
    
    for i, network in enumerate(networks_list):
        if not scan_data['is_scanning']:
            print("Сканирование прервано пользователем")
            break
        
        scan_data['current_network'] = network
        scan_data['scanned_networks'] = i + 1
        scan_data['progress'] = int((i + 1) / len(networks_list) * 100)
        
        print(f"Сканируем сеть {i+1}/{len(networks_list)}: {network}")
        
        try:
            # Используем наш сканер
            scanner.is_scanning = True
            network_results = scanner.scan_network(network)
            
            all_results.extend(network_results)
            scan_data['results'] = all_results
            scan_data['hosts_found'] = len(all_results)
            
            print(f"  Найдено устройств в этой сети: {len(network_results)}")
            print(f"  Всего найдено: {len(all_results)} устройств")
            
        except Exception as e:
            print(f"Ошибка при сканировании сети {network}: {e}")
        
        # Небольшая пауза между сетями
        time.sleep(1)
    
    # Завершение сканирования
    scan_data['is_scanning'] = False
    scanner.is_scanning = False
    scan_data['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    scan_data['progress'] = 100
    
    print(f"Сканирование завершено! Найдено устройств: {len(all_results)}")
    
    # Сохраняем результаты в файл
    if all_results:
        save_results_to_file(all_results)

def save_results_to_file(results):
    """Сохранение результатов в JSON файл"""
    filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join('results', filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump({
                'scan_time': datetime.now().isoformat(),
                'total_hosts': len(results),
                'hosts': results
            }, f, indent=2, default=str)
        print(f"Результаты сохранены в {filepath}")
    except Exception as e:
        print(f"Ошибка сохранения результатов: {e}")

if __name__ == '__main__':
    # Создаем networks.json если его нет
    if not os.path.exists('networks.json'):
        with open('networks.json', 'w') as f:
            json.dump(["192.168.1.0/24", "10.0.0.0/24"], f, indent=2)
    
    print("=" * 60)
    print("АСДУЕ - Веб-сканер сети")
    print("=" * 60)
    print(f"Сервер запускается на http://127.0.0.1:5000")
    print("")
    print("Проверьте настройки:")
    print(f"  - networks.json содержит {len(load_networks())} сетей")
    print(f"  - nmap доступен: {'Да' if os.system('which nmap > /dev/null 2>&1') == 0 else 'Нет'}")
    print("")
    print("Для запуска сканирования:")
    print("  1. Откройте http://localhost:5000")
    print("  2. Нажмите 'Сканирование сети'")
    print("  3. Нажмите 'Начать сканирование'")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)