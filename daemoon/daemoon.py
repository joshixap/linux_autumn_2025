#!/usr/bin/env python3
import os
import time
import json
import shutil
import logging
from datetime import datetime
import signal
import sys
import argparse
import fnmatch

# Конфигурационные пути
CONFIG_DIR = "/home/joshi/.config/backup_daemon"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
LOG_FILE = "/home/joshi/backup_daemon.log"
PID_FILE = "/home/joshi/backup_daemon.pid"

is_running = False

def load_config(config_path):
    """Загрузить конфигурацию из файла.""" 
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

def setup_logging(log_file):
    """Настроить журналирование."""
    try:
        if os.path.isdir(log_file):
            log_file = os.path.join(log_file, "backup_daemon.log")  # Добавить имя файла к директории
        logging.basicConfig(filename=log_file, level=logging.INFO, 
                           format='%(asctime)s - %(levelname)s - %(message)s',
                           datefmt='%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error setting up logging: {e}")
        logging.basicConfig(level=logging.INFO,
                           format='%(asctime)s - %(message)s',
                           datefmt='%Y-%m-%d %H:%M:%S')

def cleanup_old_backups(backup_dir, max_backups=30):
    """Удалить старые резервные копии."""
    try:
        backups = []
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path) and item.startswith("backup_"):
                backups.append((item_path, os.path.getmtime(item_path)))
        
        backups.sort(key=lambda x: x[1], reverse=True)
        
        if len(backups) > max_backups:
            for backup_path, _ in backups[max_backups:]:
                shutil.rmtree(backup_path)
                logging.info(f"Removed old backup: {backup_path}")
                
    except Exception as e:
        logging.error(f"Error cleaning up old backups: {e}")

def backup_files(source_dir, backup_dir, max_backups=30):
    """Создать резервные копии файлов из исходного каталога в каталог резервных копий."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
    
    try:
        # Создать директорию для бэкапов если не существует
        os.makedirs(backup_dir, exist_ok=True)
        
        shutil.copytree(source_dir, backup_path)
        logging.info(f"Backup successful: {backup_path}")
        
        # Очистить старые бэкапы
        cleanup_old_backups(backup_dir, max_backups)
        
        return True
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        return False

def write_pid(pid_file):
    """Записать PID процесса в файл."""
    try:
        # Создать директорию если не существует
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logging.error(f"Error writing PID file: {e}")

def remove_pid(pid_file):
    """Удалить PID файл."""
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except Exception as e:
        logging.error(f"Error removing PID file: {e}")

def run_backup_daemon(config_path):
    """Запустить демон резервного копирования."""
    global is_running
    is_running = True

    config = load_config(config_path)
    source_dir = config['source_dir']
    backup_dir = config['backup_dir']
    interval = config['interval_seconds']
    log_file = config.get('log_file', LOG_FILE)
    max_backups = config.get('max_backups', 30)
    
    setup_logging(log_file)
    write_pid(PID_FILE)  # Записать pid
    
    logging.info("Starting backup daemon...")
    print("Backup daemon started. Use Ctrl+C to stop.")
    
    # Обработка сигналов для корректного завершения
    def signal_handler(sig, frame):
        global is_running
        logging.info(f"Received signal {sig}, stopping daemon...")
        is_running = False
        remove_pid(PID_FILE) # очищает PID файл
        print("\nStopping daemon...")
        sys.exit(0)  # Немедленный выход
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while is_running:
        try:
            success = backup_files(source_dir, backup_dir, max_backups)
            if success:
                print(f"Backup completed at {datetime.now()}")
            
            # Ждать интервал с проверкой флага
            for _ in range(interval * 10):
                if not is_running:
                    break
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"Error in backup loop: {e}")
            time.sleep(60)

    logging.info("Daemon stopped.")
    print("Daemon stopped.")

import signal

def stop_daemon():
    if not os.path.exists(PID_FILE):
        print("PID file not found. Daemon may not be running.")
        return
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read())
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to daemon pid {pid}")
    except Exception as e:
        print(f"Error stopping daemon: {e}")

def create_config():
    """Создать конфигурационный файл."""
    print("=== Backup Daemon Configuration ===")
    
    config = {
        "source_dir": input("Source directory: ").strip(),
        "backup_dir": input("Backup directory: ").strip(),
        "interval_seconds": int(input("Backup interval (seconds): ").strip() or "3600"),
        "max_backups": int(input("Max backups to keep (default: 30): ").strip() or "30"),
        "log_file": input("Log file (default: /var/log/backup_daemon.log): ").strip() or LOG_FILE
    }
    
    # Создать директорию конфигурации
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    # Установить безопасные права
    os.chmod(CONFIG_FILE, 0o600)
    print(f"Configuration saved to {CONFIG_FILE}")

def show_status():
    """Показать статус демона."""
    if not os.path.exists(PID_FILE):
        print("Daemon status: STOPPED")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read())
        
        # Проверяем реальное существование процесса
        os.kill(pid, 0)  # Не убивает, только проверяет существование
        print(f"Daemon status: RUNNING (PID: {pid})")
    except (OSError, ValueError):
        print("Daemon status: STOPPED (PID file exists but process is dead)")
        # Очищаем битый PID файл
        remove_pid(PID_FILE)

def show_logs():
    """Показать логи."""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                print(f.read())
        else:
            print("No log file found")
    except Exception as e:
        print(f"Error reading logs: {e}")

def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(description='Backup Daemon Service')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'config', 'logs', 'run'],
                       help='start: start daemon, stop: stop daemon, status: check status, config: create config, logs: show logs, run: run in foreground')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        if not os.path.exists(CONFIG_FILE):
            print("Configuration file not found. Run 'backup-daemon config' first.")
            return
        
        # Запустить в отдельном процессе
        import subprocess
        subprocess.Popen([sys.executable, __file__, 'run'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("Daemon started in background")
        
    elif args.command == 'stop':
        stop_daemon()
        print("Stop command sent")
        
    elif args.command == 'status':
        show_status()
        
    elif args.command == 'config':
        create_config()
        
    elif args.command == 'logs':
        show_logs()
        
    elif args.command == 'run':
        if not os.path.exists(CONFIG_FILE):
            print("Configuration file not found. Run 'backup-daemon config' first.")
            return
        run_backup_daemon(CONFIG_FILE)

if __name__ == "__main__":
    main()