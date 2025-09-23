# ultimate_test.py
import socket
import requests
import time
import threading

def ultimate_test():
    print("=== ULTIMATE DETECTION TEST ===")
    time.sleep(2)  # Ждем запуск анализатора
    
    # 1. Массовое сканирование портов
    def port_scan():
        print("1. MASS PORT SCAN...")
        target = "scanme.nmap.org"
        # Сканируем много портов быстро
        for port in range(80, 95):  # 15 портов
            try:
                s = socket.socket()
                s.settimeout(0.5)
                s.connect((target, port))
                s.close()
                print(f"   PORT {port}: OPEN")
            except:
                print(f"   PORT {port}: closed")
            time.sleep(0.05)  # Очень быстро!
    
    # 2. Очень быстрые HTTP запросы
    def http_flood():
        print("2. HTTP FLOOD...")
        for i in range(15):  # 15 очень быстрых запросов
            try:
                requests.get("http://httpbin.org/get", timeout=1)
                print(f"   REQUEST {i+1}: OK")
            except:
                print(f"   REQUEST {i+1}: FAIL")
            time.sleep(0.1)  # Супер быстро!
    
    # Запускаем оба теста параллельно
    t1 = threading.Thread(target=port_scan)
    t2 = threading.Thread(target=http_flood)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    print("=== ULTIMATE TEST COMPLETE ===")

if __name__ == "__main__":
    ultimate_test()