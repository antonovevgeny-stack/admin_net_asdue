#!/usr/bin/env python3
"""
Модуль сканирования сети для АСДУЕ с улучшенным логированием
"""

import nmap
import socket
import subprocess
import re
import time
from datetime import datetime
import ipaddress
import logging
import sys

class NetworkScanner:
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.results = []
        self.is_scanning = False
        self.progress = 0
        self.current_network = ""
        self.scanned_hosts = 0
        self.web_log_callback = None  # Callback для веб-логирования
        
        # Настройка логирования
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем логгер
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Создаем обработчик для файла
        file_handler = logging.FileHandler('logs/scanner.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Создаем обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчики к логгеру
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def set_web_log_callback(self, callback):
        """Установка callback для веб-логирования"""
        self.web_log_callback = callback
    
    def log_to_web(self, message, level='info'):
        """Логирование для веб-интерфейса"""
        if self.web_log_callback:
            try:
                self.web_log_callback(message, level)
            except Exception as e:
                self.logger.error(f"Ошибка в web log callback: {e}")
        # Дублируем в файловый лог
        if level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'success':
            self.logger.info(f"✓ {message}")
        else:
            self.logger.info(message)
    
    def ping_host(self, ip):
        """Проверка доступности хоста через ping"""
        try:
            self.log_to_web(f"Проверка доступности: {ip}", 'info')
            
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            
            is_available = result.returncode == 0
            if is_available:
                self.log_to_web(f"✓ Хост активен: {ip}", 'success')
            else:
                self.log_to_web(f"✗ Хост не отвечает: {ip}", 'info')
            
            return is_available
        except subprocess.TimeoutExpired:
            self.log_to_web(f"✗ Таймаут при проверке: {ip}", 'info')
            return False
        except Exception as e:
            self.log_to_web(f"✗ Ошибка ping для {ip}: {e}", 'warning')
            return False
    
    def get_hostname(self, ip):
        """Получение имени хоста"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            self.log_to_web(f"Определено имя хоста {ip}: {hostname}", 'info')
            return hostname
        except:
            try:
                # Попытка через обратный DNS
                hostname = socket.getfqdn(ip)
                if hostname != ip:
                    self.log_to_web(f"Определено имя хоста {ip} (DNS): {hostname}", 'info')
                    return hostname
            except:
                pass
        self.log_to_web(f"Имя хоста не определено для {ip}", 'info')
        return ""
    
    def get_mac_vendor(self, ip):
        """Получение MAC адреса и производителя через ARP"""
        try:
            self.log_to_web(f"Получение MAC-адреса для {ip}...", 'info')
            
            result = subprocess.run(
                ['arp', '-n', ip],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if ip in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            mac = parts[2]
                            if re.match(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', mac):
                                # Определение производителя по OUI
                                vendor = self.get_vendor_by_mac(mac)
                                self.log_to_web(f"MAC {ip}: {mac}, производитель: {vendor}", 'info')
                                return mac.upper(), vendor
            else:
                self.log_to_web(f"ARP не вернул данных для {ip}", 'info')
        except Exception as e:
            self.log_to_web(f"Ошибка ARP для {ip}: {e}", 'warning')
        
        return "Unknown", "Unknown"
    
    def get_vendor_by_mac(self, mac):
        """Определение производителя по MAC"""
        oui_db = {
            '00:0C:29': 'VMware',
            '00:50:56': 'VMware',
            '00:1C:42': 'Parallels',
            '08:00:27': 'VirtualBox',
            '00:15:5D': 'Microsoft Hyper-V',
            '00:1A:4B': 'ASUS',
            '00:1D:0F': 'Cisco',
            '00:24:81': 'D-Link',
            '00:26:B8': 'Huawei',
            '00:50:F1': 'Intel',
            '00:E0:4C': 'Realtek',
            '00:23:AE': 'TP-Link',
            '00:1F:3B': 'Dell',
            '00:21:5A': 'HP',
            '00:25:90': 'Apple',
        }
        
        mac_prefix = mac[:8].upper()
        for oui, vendor in oui_db.items():
            if mac_prefix.startswith(oui):
                return vendor
        
        return "Unknown"
    
    def scan_network_nmap(self, network):
        """Сканирование сети с помощью nmap"""
        self.log_to_web(f"Начинаем сканирование сети: {network} (метод: nmap)", 'info')
        print(f"[NMAP] Сканируем сеть: {network}")
        
        try:
            # Логируем параметры сканирования
            self.log_to_web(f"Используем аргументы nmap: -sn -T4", 'info')
            
            # Быстрое сканирование хостов
            self.nm.scan(hosts=network, arguments='-sn -T4')
            
            hosts = []
            all_hosts = self.nm.all_hosts()
            self.log_to_web(f"Найдено {len(all_hosts)} хостов для проверки в сети {network}", 'info')
            
            for i, host in enumerate(all_hosts):
                if self.nm[host].state() == 'up':
                    self.log_to_web(f"Хост {host} активен (статус: up)", 'success')
                    host_info = self.get_host_details(host)
                    hosts.append(host_info)
                else:
                    self.log_to_web(f"Хост {host} не активен (статус: {self.nm[host].state()})", 'info')
                
                # Логируем прогресс каждые 10 хостов
                if (i + 1) % 10 == 0:
                    self.log_to_web(f"Прогресс: проверено {i + 1}/{len(all_hosts)} хостов", 'info')
            
            self.log_to_web(f"Сеть {network}: найдено {len(hosts)} активных устройств", 'success')
            return hosts
            
        except Exception as e:
            error_msg = f"Ошибка nmap для сети {network}: {e}"
            self.log_to_web(error_msg, 'error')
            print(error_msg)
            return []
    
    def get_host_details(self, ip):
        """Получение детальной информации о хосте"""
        self.log_to_web(f"Сбор детальной информации о хосте {ip}...", 'info')
        
        host_info = {
            'ip': ip,
            'hostname': '',
            'mac': 'Unknown',
            'vendor': 'Unknown',
            'os': 'Unknown',
            'status': 'Online',
            'ports': [],
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Получаем имя хоста
            hostname = self.get_hostname(ip)
            if hostname:
                host_info['hostname'] = hostname
            
            # Получаем MAC и производителя
            mac, vendor = self.get_mac_vendor(ip)
            host_info['mac'] = mac
            host_info['vendor'] = vendor
            
            # Быстрое сканирование портов и ОС
            try:
                self.log_to_web(f"Детальное сканирование хоста {ip} (порты и ОС)...", 'info')
                self.nm.scan(hosts=ip, arguments='-O -F')
                
                if ip in self.nm.all_hosts():
                    # Определение ОС
                    if 'osmatch' in self.nm[ip]:
                        if self.nm[ip]['osmatch']:
                            os_info = self.nm[ip]['osmatch'][0]
                            host_info['os'] = f"{os_info['name']} (accuracy: {os_info['accuracy']}%)"
                            self.log_to_web(f"ОС хоста {ip}: {host_info['os']}", 'info')
                    
                    # Открытые порты
                    if 'tcp' in self.nm[ip]:
                        port_count = len(self.nm[ip]['tcp'])
                        self.log_to_web(f"Найдено {port_count} открытых портов у {ip}", 'info')
                        
                        for port in self.nm[ip]['tcp']:
                            port_info = self.nm[ip]['tcp'][port]
                            host_info['ports'].append({
                                'port': port,
                                'state': port_info['state'],
                                'service': port_info['name']
                            })
            
            except Exception as e:
                self.log_to_web(f"Детальное сканирование {ip} не удалось: {e}", 'warning')
        
        except Exception as e:
            self.log_to_web(f"Ошибка получения деталей для {ip}: {e}", 'warning')
        
        self.log_to_web(f"Информация о хосте {ip} собрана", 'success')
        return host_info
    
    def scan_network_simple(self, network_cidr):
        """Простое сканирование сети (без nmap, если он не работает)"""
        self.log_to_web(f"Начинаем простое сканирование сети: {network_cidr}", 'info')
        print(f"[SIMPLE] Сканируем сеть: {network_cidr}")
        
        hosts = []
        
        try:
            # Парсим CIDR
            network = ipaddress.ip_network(network_cidr, strict=False)
            total_hosts = sum(1 for _ in network.hosts())
            self.log_to_web(f"Сеть {network_cidr} содержит {total_hosts} возможных адресов", 'info')
            
            # Ограничиваем количество сканируемых адресов для теста
            max_hosts = min(50, total_hosts)  # Увеличили лимит для лучшего покрытия
            count = 0
            found_hosts = 0
            
            self.log_to_web(f"Будет проверено до {max_hosts} адресов", 'info')
            
            for ip in network.hosts():
                if count >= max_hosts:
                    break
                
                ip_str = str(ip)
                count += 1
                
                # Логируем прогресс каждые 5 адресов
                if count % 5 == 0:
                    self.log_to_web(f"Прогресс: проверено {count}/{max_hosts} адресов, найдено {found_hosts} хостов", 'info')
                
                if self.ping_host(ip_str):
                    host_info = {
                        'ip': ip_str,
                        'hostname': self.get_hostname(ip_str),
                        'mac': 'Unknown',
                        'vendor': 'Unknown',
                        'os': 'Unknown',
                        'status': 'Online',
                        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Получаем MAC если доступно
                    mac, vendor = self.get_mac_vendor(ip_str)
                    host_info['mac'] = mac
                    host_info['vendor'] = vendor
                    
                    hosts.append(host_info)
                    found_hosts += 1
                    self.log_to_web(f"Найден хост: {ip_str} (всего найдено: {found_hosts})", 'success')
                
                time.sleep(0.05)  # Уменьшили паузу для ускорения
        
        except Exception as e:
            error_msg = f"Ошибка простого сканирования {network_cidr}: {e}"
            self.log_to_web(error_msg, 'error')
            print(error_msg)
        
        self.log_to_web(f"Простое сканирование {network_cidr} завершено: найдено {len(hosts)} устройств", 'success')
        return hosts
    
    def scan_network(self, network_cidr):
        """Основной метод сканирования сети"""
        self.log_to_web(f"Начинаем сканирование сети: {network_cidr}", 'info')
        start_time = time.time()
        
        try:
            results = self.scan_network_nmap(network_cidr)
            end_time = time.time()
            scan_duration = end_time - start_time
            
            if results:
                self.log_to_web(f"Сканирование {network_cidr} успешно завершено за {scan_duration:.1f} секунд", 'success')
            else:
                self.log_to_web(f"В сети {network_cidr} не найдено активных устройств", 'info')
            
            return results
        except Exception as e:
            error_msg = f"Nmap не сработал для сети {network_cidr}: {e}"
            self.log_to_web(error_msg, 'warning')
            print(error_msg)
            
            self.log_to_web(f"Используем простой метод сканирования для сети {network_cidr}", 'info')
            results = self.scan_network_simple(network_cidr)
            
            end_time = time.time()
            scan_duration = end_time - start_time
            self.log_to_web(f"Сканирование {network_cidr} завершено за {scan_duration:.1f} секунд", 'success')
            
            return results