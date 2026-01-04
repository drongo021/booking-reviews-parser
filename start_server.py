#!/usr/bin/env python3
"""
Скрипт запуска для Railway
Читает PORT из переменных окружения
"""
import os
import subprocess
import sys

def main():
    port = os.environ.get('PORT', '5000')
    
    # Запускаем gunicorn
    cmd = [
        'gunicorn',
        'app:app',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--timeout', '120'
    ]
    
    print(f"Starting gunicorn on port {port}...")
    sys.exit(subprocess.call(cmd))

if __name__ == '__main__':
    main()

