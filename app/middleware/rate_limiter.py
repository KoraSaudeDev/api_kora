import redis
from flask import request, jsonify
from datetime import datetime
from celery_worker import log_request_to_db

r = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

MAX_REQUESTS = 10
WINDOW_SECONDS = 1
BLOCK_DURATION = 2 * 60 * 60 # duas horas 

def rate_limit():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    block_key = f"block:{ip}"
    count_key = f"count:{ip}"

    if r.exists(block_key):
        _log_blocked_request(ip, request.path, 429)
        return jsonify({"error": "IP bloqueado por excesso de requisições. Tente novamente mais tarde."}), 429

    current = r.incr(count_key)
    if current == 1:
        r.expire(count_key, WINDOW_SECONDS)

    if current > MAX_REQUESTS:
        r.setex(block_key, BLOCK_DURATION, 1)
        _log_blocked_request(ip, request.path, 429)
        return jsonify({"error": "IP bloqueado por excesso de requisições. Tente novamente mais tarde."}), 429

    return None

def _log_blocked_request(ip, endpoint, status_code):
    try:
        username = "IP Bloqueado"
        ts = datetime.utcnow()
        log_request_to_db.delay(username, endpoint, status_code, ts.isoformat(), ip)
        print(f"[RATE LIMIT] Log enviado para Celery: {username} {endpoint} {status_code}")
    except Exception as e:
        import logging
        logging.exception("Erro ao logar requisição bloqueada")