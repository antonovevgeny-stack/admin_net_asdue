#!/usr/bin/env python3
"""
Модуль сканирования сети для АСДУЕ
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
    
    def ping_host(self, ip):
        """Проверка доступности хоста через ping"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def get_hostname(self, ip):
        """Получение имени хоста"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            try:
                # Попытка через обратный DNS
                hostname = socket.getfqdn(ip)
                if hostname != ip:
                    return hostname
            except:
                pass
        return ""
    
    def get_mac_vendor(self, ip):
        """Получение MAC адреса и производителя через ARP"""
        try:
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
                                return mac.upper(), vendor
        except Exception as e:
            self.logger.error(f"ARP error for {ip}: {e}")
        
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
        self.logger.info(f"Начало сканирования сети: {network}")
        print(f"[NMAP] Сканируем сеть: {network}")
        
        try:
            # Быстрое сканирование хостов
            self.nm.scan(hosts=network, arguments='-sn -T4')
            
            hosts = []
            for host in self.nm.all_hosts():
                if self.nm[host].state() == 'up':
                    self.logger.info(f"Найден активный хост: {host}")
                    host_info = self.get_host_details(host)
                    hosts.append(host_info)
            
            self.logger.info(f"Сеть {network}: найдено {len(hosts)} устройств")
            return hosts
            
        except Exception as e:
            error_msg = f"Ошибка nmap для сети {network}: {e}"
            self.logger.error(error_msg)
            print(error_msg)
            return []
    
    def get_host_details(self, ip):
        """Получение детальной информации о хосте"""
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
                self.logger.info(f"Хост {ip}: имя хоста = {hostname}")
            
            # Получаем MAC и производителя
            mac, vendor = self.get_mac_vendor(ip)
            host_info['mac'] = mac
            host_info['vendor'] = vendor
            
            if mac != "Unknown":
                self.logger.info(f"Хост {ip}: MAC = {mac}, производитель = {vendor}")
            
            # Быстрое сканирование портов и ОС
            try:
                self.nm.scan(hosts=ip, arguments='-O -F')
                
                if ip in self.nm.all_hosts():
                    # Определение ОС
                    if 'osmatch' in self.nm[ip]:
                        if self.nm[ip]['osmatch']:
                            os_info = self.nm[ip]['osmatch'][0]
                            host_info['os'] = f"{os_info['name']} (accuracy: {os_info['accuracy']}%)"
                            self.logger.info(f"Хост {ip}: ОС = {host_info['os']}")
                    
                    # Открытые порты
                    if 'tcp' in self.nm[ip]:
                        for port in self.nm[ip]['tcp']:
                            port_info = self.nm[ip]['tcp'][port]
                            host_info['ports'].append({
                                'port': port,
                                'state': port_info['state'],
                                'service': port_info['name']
                            })
                        
                        if host_info['ports']:
                            self.logger.info(f"Хост {ip}: найдено {len(host_info['ports'])} открытых портов")
            
            except Exception as e:
                self.logger.warning(f"Детальное сканирование {ip} не удалось: {e}")
        
        except Exception as e:
            self.logger.error(f"Ошибка получения деталей для {ip}: {e}")
        
        return host_info
    
    def scan_network_simple(self, network_cidr):
        """Простое сканирование сети (без nmap, если он не работает)"""
        self.logger.info(f"Начало простого сканирования: {network_cidr}")
        print(f"[SIMPLE] Сканируем сеть: {network_cidr}")
        
        hosts = []
        
        try:
            # Парсим CIDR
            network = ipaddress.ip_network(network_cidr, strict=False)
            
            # Сканируем только первые 20 адресов для теста
            max_hosts = 20
            count = 0
            
            for ip in network.hosts():
                if count >= max_hosts:
                    break
                
                ip_str = str(ip)
                self.logger.debug(f"Проверка {ip_str}...")
                
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
                    self.logger.info(f"Найден хост: {ip_str}")
                    print(f"  ✓ Найден хост: {ip_str}")
                
                count += 1
                time.sleep(0.1)  # Чтобы не перегружать сеть
        
        except Exception as e:
            error_msg = f"Ошибка простого сканирования: {e}"
            self.logger.error(error_msg)
            print(error_msg)
        
        self.logger.info(f"Простое сканирование {network_cidr}: найдено {len(hosts)} устройств")
        return hosts
    
    def scan_network(self, network_cidr):
        """Основной метод сканирования сети"""
        try:
            return self.scan_network_nmap(network_cidr)
        except Exception as e:
            error_msg = f"nmap не сработал, используем простой метод: {e}"
            self.logger.warning(error_msg)
            print(error_msg)
            return self.scan_network_simple(network_cidr)