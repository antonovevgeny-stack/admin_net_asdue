from flask import Flask, jsonify, request, render_template_string
import os
import logging
from logging.handlers import RotatingFileHandler
import ipaddress
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY', 'dev-key-123')

# Настройка логирования
if os.getenv('LOG_FORMAT') == 'json':
    import json
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            return json.dumps(log_record)
    formatter = JsonFormatter()
else:
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

# Файловый логгер
if os.getenv('FLASK_ENV') == 'production':
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10000,
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

app.logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Глобальные переменные для метрик
metrics_data = {
    'requests_total': 0,
    'health_checks': 0,
    'ip_calculations': 0,
    'errors_total': 0
}

@app.route('/health')
def health():
    metrics_data['health_checks'] += 1
    return jsonify({
        'status': 'healthy',
        'service': 'IP Calculator API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'metrics': {
            'total_requests': metrics_data['requests_total'],
            'ip_calculations': metrics_data['ip_calculations']
        }
    }), 200

@app.route('/metrics')
def metrics():
    if os.getenv('ENABLE_METRICS', 'True').lower() == 'true':
        return jsonify(metrics_data), 200
    return jsonify({'error': 'Metrics disabled'}), 404

@app.route('/api/ip-calculator')
def ip_calculator_ui():
    html_template = '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IP Калькулятор - АСДУЕ</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #2c3e50; margin-bottom: 10px; }
            .back-btn { display: inline-block; margin-top: 20px; padding: 10px 20px; 
                       background: #667eea; color: white; text-decoration: none; 
                       border-radius: 5px; }
            .calculator { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
            .input-section, .output-section { background: white; padding: 30px; 
                                            border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: 600; }
            input, select { width: 100%; padding: 10px; border: 1px solid #ddd; 
                           border-radius: 5px; font-size: 16px; }
            button { background: #667eea; color: white; border: none; padding: 12px 30px;
                    border-radius: 5px; cursor: pointer; font-size: 16px; }
            .result-item { margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .result-label { font-weight: 600; color: #667eea; }
            .result-value { font-family: monospace; font-size: 14px; }
            @media (max-width: 768px) { .calculator { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-calculator"></i> IP Калькулятор</h1>
                <p>Расчет параметров сетей и подсетей</p>
                <a href="/" class="back-btn"><i class="fas fa-arrow-left"></i> На главную</a>
            </div>
            
            <div class="calculator">
                <div class="input-section">
                    <h2>Входные параметры</h2>
                    <div class="form-group">
                        <label>IP адрес:</label>
                        <input type="text" id="ip" placeholder="192.168.1.1" value="192.168.1.1">
                    </div>
                    <div class="form-group">
                        <label>Маска сети:</label>
                        <select id="mask">
                            <option value="24">24 (255.255.255.0)</option>
                            <option value="16">16 (255.255.0.0)</option>
                            <option value="8">8 (255.0.0.0)</option>
                            <option value="30">30 (255.255.255.252)</option>
                            <option value="26">26 (255.255.255.192)</option>
                        </select>
                    </div>
                    <button onclick="calculateIP()"><i class="fas fa-calculator"></i> Рассчитать</button>
                </div>
                
                <div class="output-section">
                    <h2>Результаты расчета</h2>
                    <div id="results">
                        <p>Введите параметры и нажмите "Рассчитать"</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
        <script>
            async function calculateIP() {
                const ip = document.getElementById('ip').value;
                const mask = document.getElementById('mask').value;
                
                try {
                    const response = await fetch('/api/calculate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ip: ip, mask: parseInt(mask) })
                    });
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        document.getElementById('results').innerHTML = `
                            <div style="color: red; padding: 20px; background: #ffe6e6; border-radius: 5px;">
                                <strong>Ошибка:</strong> ${data.error}
                            </div>
                        `;
                        return;
                    }
                    
                    document.getElementById('results').innerHTML = `
                        <div class="result-item">
                            <div class="result-label">Сеть:</div>
                            <div class="result-value">${data.network}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Широковещательный адрес:</div>
                            <div class="result-value">${data.broadcast}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Доступные хосты:</div>
                            <div class="result-value">${data.usable_hosts}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Первый адрес:</div>
                            <div class="result-value">${data.first_host}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Последний адрес:</div>
                            <div class="result-value">${data.last_host}</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Маска подсети:</div>
                            <div class="result-value">${data.netmask} (/${data.cidr})</div>
                        </div>
                        <div class="result-item">
                            <div class="result-label">Wildcard маска:</div>
                            <div class="result-value">${data.wildcard}</div>
                        </div>
                    `;
                    
                } catch (error) {
                    document.getElementById('results').innerHTML = `
                        <div style="color: red;">
                            Ошибка соединения с сервером
                        </div>
                    `;
                }
            }
            
            window.onload = calculateIP;
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/api/calculate', methods=['POST'])
def calculate():
    metrics_data['requests_total'] += 1
    
    try:
        data = request.get_json()
        
        if not data or 'ip' not in data or 'mask' not in data:
            metrics_data['errors_total'] += 1
            return jsonify({'error': 'Отсутствуют обязательные поля: ip и mask'}), 400
        
        ip_str = data['ip']
        mask = int(data['mask'])
        
        if mask < 0 or mask > 32:
            metrics_data['errors_total'] += 1
            return jsonify({'error': 'Маска должна быть в диапазоне 0-32'}), 400
        
        try:
            network = ipaddress.ip_network(f"{ip_str}/{mask}", strict=False)
            
            result = {
                'network': str(network.network_address),
                'broadcast': str(network.broadcast_address),
                'netmask': str(network.netmask),
                'wildcard': str(network.hostmask),
                'cidr': network.prefixlen,
                'total_hosts': network.num_addresses,
                'usable_hosts': network.num_addresses - 2 if network.num_addresses > 2 else network.num_addresses,
                'first_host': str(list(network.hosts())[0]) if network.num_addresses > 2 else 'N/A',
                'last_host': str(list(network.hosts())[-1]) if network.num_addresses > 2 else 'N/A',
                'ip_version': network.version,
                'is_private': network.is_private,
                'is_global': network.is_global,
                'network_with_cidr': f"{network.network_address}/{network.prefixlen}"
            }
            
            metrics_data['ip_calculations'] += 1
            app.logger.info(f'IP calculation successful: {ip_str}/{mask}')
            return jsonify(result), 200
            
        except ValueError as e:
            metrics_data['errors_total'] += 1
            app.logger.error(f'Invalid IP address: {ip_str}/{mask}')
            return jsonify({'error': f'Неверный формат IP адреса: {str(e)}'}), 400
            
    except Exception as e:
        metrics_data['errors_total'] += 1
        app.logger.error(f'Error in calculation: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
