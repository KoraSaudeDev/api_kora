from flask import request, jsonify
from datetime import datetime
from celery_worker import log_request_to_db
from collections import defaultdict
import time
import threading

# Armazenamento em memória (volátil)
request_counts = defaultdict(list)
blocked_ips = {}
lock = threading.Lock()

# Limites padrão
MAX_REQUESTS_DEFAULT = 10
WINDOW_SECONDS_DEFAULT = 1
BLOCK_DURATION = 30 * 60  # 30 minutos

# Lista branca de IPs e limites especiais
WHITELISTED_IPS = {
    "136.248.89.4": {"max_requests": 80, "window_seconds": 1},
    "20.122.114.244": {"max_requests": 80, "window_seconds": 1},
}

def rate_limit():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    now = time.time()

    # Seleciona limites conforme IP
    limits = WHITELISTED_IPS.get(ip, {
        "max_requests": MAX_REQUESTS_DEFAULT,
        "window_seconds": WINDOW_SECONDS_DEFAULT
    })

    max_requests = limits["max_requests"]
    window_seconds = limits["window_seconds"]

    with lock:
        # Verifica se IP está bloqueado
        if ip in blocked_ips:
            unblock_time = blocked_ips[ip]
            if now < unblock_time:
                _log_blocked_request(ip, request.path, 429)
                return jsonify({"error": "IP bloqueado por excesso de requisições. Tente novamente mais tarde."}), 429
            else:
                del blocked_ips[ip]

        # Registra timestamps recentes
        request_times = request_counts[ip]
        request_times = [t for t in request_times if now - t < window_seconds]
        request_times.append(now)
        request_counts[ip] = request_times

        if len(request_times) > max_requests:
            blocked_ips[ip] = now + BLOCK_DURATION
            del request_counts[ip]
            _log_blocked_request(ip, request.path, 429)
            return jsonify({"error": "IP bloqueado por excesso de requisições. Tente novamente mais tarde."}), 429

    return None

def _log_blocked_request(ip, endpoint, status_code):
    try:
        username = "IP Bloqueado"
        ts = datetime.utcnow()
        log_request_to_db.delay(username, endpoint, status_code, ts.isoformat(), ip)
        print(f"[RATE LIMIT] Log enviado para Celery: {username} {endpoint} {status_code}")
    except Exception:
        import logging
        logging.exception("Erro ao logar requisição bloqueada")
