# app/config/env.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "10.27.254.161"),
    "port": int(os.getenv("DB_PORT", 3307)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Kora@2024"),
    "database": os.getenv("DB_NAME", "verzo")
}

ORACLE_CONFIG = {
    "cariacica": {
        "host": "ODASC1-REDEMERI",
        "port": 1521,
        "service_name": "mvmcvip.hospitalmeridional.local",
        "user": "RAFAELVS_DB",
        "password": "a2!S82hnVY"
    },
    "serra": {
        "host": "ODASC1-REDEMERI",
        "port": 1521,
        "service_name": "mvmsvip.hospitalmeridional.local",
        "user": "RAFAELVS_DB",
        "password": "a2!S82hnVY"
    },
    "praia_da_costa": {
        "host": "ODASC1-REDEMERI",
        "port": 1521,
        "service_name": "mvmpcvip.hospitalmeridional.local",
        "user": "RAFAELVS_DB",
        "password": "a2!S82hnVY"
    },
    "anchieta": {
        "host": "10.0.0.129",
        "port": 1521,
        "service_name": "oramvpra",
        "user": "RAFAELVS_DB",
        "password": "a2!S82hnVY"
    },
    "neurologia_goiania": {
        "host": "1940db.cloudmv.com.br",
        "port": 1521,
        "service_name": "prd1940prd.db1940.mv1940vcn.oraclevcn.com",
        "user": "RAFAELVS_DB",
        "password": "a2!S82hnVY"
    },
    "sao_matheus": {
        "host": "192.168.70.217",
        "port": 1521,
        "service_name": "slrmvip.hospitalmeridional.local",
        "user": "RAFAELVS_DB",
        "password": "a2!S82hnVY"
    }
}
