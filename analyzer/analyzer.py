import tkinter as tk
from tkinter import ttk, messagebox
from scapy.all import sniff, IP, TCP, ICMP, send
from collections import defaultdict
import time
import threading
import requests

class TrafficMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Traffic Monitor")
        self.root.geometry("550x500")
        
        self.is_monitoring = False
        self.suspicious_ips = set()
        self.ip_stats = defaultdict(lambda: {'ports': set(), 'count': 0, 'first_seen': 0})
        self.ip_event_count = defaultdict(int)
        self.last_event_time = time.time()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Настройки обнаружения
        settings_frame = ttk.LabelFrame(self.root, text="Параметры обнаружения", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Чекбоксы правил
        self.size_check = tk.BooleanVar(value=True)
        self.port_check = tk.BooleanVar(value=True)
        self.repeat_check = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(settings_frame, text="Большие пакеты", variable=self.size_check).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(settings_frame, text="Сканирование портов", variable=self.port_check).grid(row=0, column=1, sticky=tk.W, padx=20)
        ttk.Checkbutton(settings_frame, text="Повторяющиеся запросы", variable=self.repeat_check).grid(row=0, column=2, sticky=tk.W)
        
        # Параметры
        params_frame = ttk.Frame(settings_frame)
        params_frame.grid(row=1, column=0, columnspan=3, pady=5, sticky=tk.W)
        
        ttk.Label(params_frame, text="Макс. размер:").grid(row=0, column=0)
        self.max_size = tk.IntVar(value=500)
        ttk.Entry(params_frame, textvariable=self.max_size, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(params_frame, text="Порог портов:").grid(row=0, column=2)
        self.port_thresh = tk.IntVar(value=3)
        ttk.Entry(params_frame, textvariable=self.port_thresh, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(params_frame, text="Порог запросов:").grid(row=0, column=4)
        self.repeat_thresh = tk.IntVar(value=10)
        ttk.Entry(params_frame, textvariable=self.repeat_thresh, width=8).grid(row=0, column=5, padx=5)
        
        # Кнопки управления
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="Начать сканирование", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Блокировать выбранные", command=self.block_ips).pack(side=tk.LEFT, padx=5)
        
        # Список подозрительных IP
        list_frame = ttk.LabelFrame(self.root, text="Подозрительные IP-адреса")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.ip_list = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=8)
        scrollbar = ttk.Scrollbar(list_frame, command=self.ip_list.yview)
        self.ip_list.config(yscrollcommand=scrollbar.set)
        
        self.ip_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Лог событий
        log_frame = ttk.LabelFrame(self.root, text="Журнал событий")
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log = tk.Text(log_frame, height=6)
        self.log.pack(fill=tk.X, padx=5, pady=5)
        
    def log_msg(self, msg):
        self.log.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log.see(tk.END)
        
    def get_isp_info(self, ip):
        """Получение информации о провайдере"""
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
            data = response.json()
            if data.get('status') == 'success':
                return f"{data.get('isp', 'Unknown')} ({data.get('country', 'Unknown')})"
        except:
            pass
        return "Unknown ISP"
        
    def packet_handler(self, packet):
        if not packet.haslayer(IP) or not packet.haslayer(TCP):
            return
            
        src_ip = packet[IP].src
        dst_port = packet[TCP].dport
        packet_size = len(packet)
        current_time = time.time()
        
        # Инициализация статистики IP
        if src_ip not in self.ip_stats:
            self.ip_stats[src_ip]['first_seen'] = current_time
        
        ip_info = self.ip_stats[src_ip]
        
        # Проверка большого пакета
        if self.size_check.get() and packet_size > self.max_size.get():
            if src_ip not in self.suspicious_ips:
                self.suspicious_ips.add(src_ip)
                isp_info = self.get_isp_info(src_ip)
                self.ip_list.insert(tk.END, f"{src_ip} - {isp_info} - Large packet")
                self.log_msg(f"Обнаружен: {src_ip} - Большой пакет ({packet_size} bytes)")
        
        # Проверка сканирования портов
        if self.port_check.get():
            ip_info['ports'].add(dst_port)
            if len(ip_info['ports']) > self.port_thresh.get():
                if src_ip not in self.suspicious_ips:
                    self.suspicious_ips.add(src_ip)
                    isp_info = self.get_isp_info(src_ip)
                    self.ip_list.insert(tk.END, f"{src_ip} - {isp_info} - Port scan")
                    self.log_msg(f"Обнаружен: {src_ip} - Сканирование портов ({len(ip_info['ports'])} портов)")
        
        # Проверка повторяющихся запросов
        if self.repeat_check.get():
            self.ip_event_count[src_ip] += 1
            
            # Проверка в временном окне 5 секунд
            if (self.ip_event_count[src_ip] > self.repeat_thresh.get() and 
                (current_time - self.last_event_time) < 5):
                if src_ip not in self.suspicious_ips:
                    self.suspicious_ips.add(src_ip)
                    isp_info = self.get_isp_info(src_ip)
                    self.ip_list.insert(tk.END, f"{src_ip} - {isp_info} - Repeated requests")
                    self.log_msg(f"Обнаружен: {src_ip} - Повторяющиеся запросы")
                    self.last_event_time = current_time
        
        ip_info['count'] += 1
    
    def start(self):
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        
        # Очистка предыдущих результатов
        self.suspicious_ips.clear()
        self.ip_stats.clear()
        self.ip_event_count.clear()
        self.ip_list.delete(0, tk.END)
        
        def sniff_thread():
            self.log_msg("Сканирование запущено на 15 секунд...")
            sniff(prn=self.packet_handler, store=0, timeout=15)
            self.root.after(0, self.on_sniff_end)
            
        threading.Thread(target=sniff_thread, daemon=True).start()
        
    def on_sniff_end(self):
        if self.is_monitoring:
            self.is_monitoring = False
            self.start_btn.config(state=tk.NORMAL)
            self.log_msg("Сканирование завершено")
            messagebox.showinfo("Готово", f"Найдено подозрительных IP: {len(self.suspicious_ips)}")
        
    def block_ips(self):
        selections = self.ip_list.curselection()
        if not selections:
            messagebox.showwarning("Внимание", "Выберите IP для блокировки")
            return
            
        blocked_ips = []
        for index in selections:
            ip_text = self.ip_list.get(index)
            ip = ip_text.split(' - ')[0]
            
            try:
                import subprocess
                # Прямое выполнение iptables в WSL (без wsl команды)
                result1 = subprocess.run([
                    'sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'
                ], check=True)
                
                result2 = subprocess.run([
                    'sudo', 'iptables', '-A', 'OUTPUT', '-d', ip, '-j', 'DROP'
                ], check=True)
                
                blocked_ips.append(ip)
                self.log_msg(f"Заблокирован: {ip}")
                
            except subprocess.CalledProcessError:
                self.log_msg(f"Ошибка прав для {ip} - уже запущено с sudo?")
            except Exception as e:
                self.log_msg(f"Ошибка блокировки {ip}: {e}")
                    
        if blocked_ips:
            messagebox.showinfo("Успех", f"Заблокировано IP: {len(blocked_ips)}")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = TrafficMonitor()
    app.run()