import mysql.connector
import cx_Oracle
import psycopg2
import sqlite3
import pyodbc
from sqlalchemy import create_engine
from hdbcli import dbapi
import redis
from pymongo import MongoClient
from cassandra.cluster import Cluster
import json
import logging
from app.utils.security import decrypt_password
import firebase_admin
from dotenv import load_dotenv
import os

# Configuração do logger
logging.basicConfig(level=logging.INFO)

# Carregar variáveis do .env
load_dotenv()

class DatabaseService:
    @staticmethod
    def create_connection(db_type, host=None, port=None, username=None, password=None, 
                          database=None, service_name=None, sid=None, extra_params=None):
        """
        Cria uma conexão com o banco de dados baseado no tipo.
        """
        try:
            logging.info(f"Tentando conectar ao banco {db_type} em {host}:{port}...")

            if db_type.lower() == "mysql":
                return mysql.connector.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database
                )
            elif db_type.lower() == "mariadb":
                return mysql.connector.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database
                )
            elif db_type.lower() == "oracle":
                if service_name:
                    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
                elif sid:
                    dsn = cx_Oracle.makedsn(host, port, sid=sid)
                else:
                    raise ValueError("Oracle requer 'service_name' ou 'sid'.")
                return cx_Oracle.connect(user=username, password=password, dsn=dsn)
            elif db_type.lower() == "postgres":
                return psycopg2.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    dbname=database
                )
            elif db_type.lower() == "sqlite":
                if not database:
                    raise ValueError("SQLite requer o caminho do arquivo de banco de dados.")
                return sqlite3.connect(database)
            elif db_type.lower() == "sap":
                if not extra_params:
                    raise ValueError("Conexões SAP requerem parâmetros adicionais em 'extra_params'.")
                params = json.loads(extra_params)
                dsn = params.get("dsn")
                if not dsn:
                    raise ValueError("Conexões SAP requerem um DSN configurado.")
                return pyodbc.connect(f"DSN={dsn};UID={username};PWD={password}")
            elif db_type.lower() == "sap_hana":
                return dbapi.connect(
                    address=host,
                    port=port,
                    user=username,
                    password=password,
                    databaseName=database,
                )
            elif db_type.lower() == "redis":
                return redis.StrictRedis(host=host, port=port, password=password)
            elif db_type.lower() == "mongodb":
                uri = f"mongodb://{username}:{password}@{host}:{port}/"
                return MongoClient(uri)
            elif db_type.lower() == "cassandra":
                cluster = Cluster([host], port=port)
                session = cluster.connect()
                if database:
                    session.set_keyspace(database)
                return session
            elif db_type.lower() == "mssql":
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};UID={username};PWD={password};DATABASE={database}"
                return pyodbc.connect(conn_str)
            elif db_type.lower() == "ibm_db2":
                conn_str = f"DATABASE={database};HOSTNAME={host};PORT={port};PROTOCOL=TCPIP;UID={username};PWD={password}"
                return pyodbc.connect(conn_str)
            elif db_type.lower() == "snowflake":
                from snowflake.connector import connect
                return connect(
                    user=username,
                    password=password,
                    account=host,
                    warehouse=extra_params.get("warehouse"),
                    database=database
                )
            elif db_type.lower() == "firebase":
                from firebase_admin import credentials
                cred = credentials.Certificate(extra_params["service_account_key"])
                return firebase_admin.initialize_app(cred)
            elif db_type.lower() == "elasticsearch":
                from elasticsearch import Elasticsearch
                return Elasticsearch(
                    hosts=[{"host": host, "port": port}],
                    http_auth=(username, password) if username and password else None
                )
            elif db_type.lower() == "dynamodb":
                import boto3
                return boto3.resource(
                    "dynamodb",
                    region_name=extra_params["region_name"],
                    aws_access_key_id=extra_params["access_key"],
                    aws_secret_access_key=extra_params["secret_key"]
                )
            else:
                raise ValueError(f"Tipo de banco de dados '{db_type}' não suportado.")
        except Exception as e:
            logging.error(f"Erro ao conectar ao banco {db_type}: {e}")
            raise ConnectionError(f"Erro ao conectar ao banco {db_type}: {e}")

    @staticmethod
    def test_connection(db_type, host=None, port=None, username=None, password=None, database=None, service_name=None, sid=None, extra_params=None):
        """
        Testa uma nova conexão.
        """
        try:
            DatabaseService.create_connection(
                db_type=db_type,
                host=host,
                port=port,
                username=username,
                password=password,
                database=database,
                service_name=service_name,
                sid=sid,
                extra_params=extra_params
            ).close()
            return {"status": "success", "message": "Conexão testada com sucesso."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def test_existing_connection(connection_data):
        """
        Testa uma conexão existente com base nos dados fornecidos.
        """
        try:
            password = decrypt_password(connection_data["password"])
            return DatabaseService.test_connection(
                db_type=connection_data["db_type"],
                host=connection_data.get("host"),
                port=connection_data.get("port"),
                username=connection_data.get("username"),
                password=password,
                database=connection_data.get("database_name"),
                service_name=connection_data.get("service_name"),
                sid=connection_data.get("sid"),
                extra_params=connection_data.get("extra_params"),
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def create_connection_itsm_tickets():
        """
        Cria uma conexão com o banco ITSM Tickets, configurado no arquivo .env.
        """
        db_type = os.getenv("ITSM_DB_TYPE")
        host = os.getenv("ITSM_DB_HOST")
        port = int(os.getenv("ITSM_DB_PORT"))
        user = os.getenv("ITSM_DB_USER")
        password = os.getenv("ITSM_DB_PASSWORD")
        database = os.getenv("ITSM_DB_DATABASE")
        service_name = os.getenv("ITSM_DB_SERVICE_NAME", None)
        sid = os.getenv("ITSM_DB_SID", None)

        try:
            if db_type.lower() == "mysql":
                return mysql.connector.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
            elif db_type.lower() == "oracle":
                if service_name:
                    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
                elif sid:
                    dsn = cx_Oracle.makedsn(host, port, sid=sid)
                else:
                    raise ValueError("Oracle requer 'service_name' ou 'sid'.")
                return cx_Oracle.connect(user=user, password=password, dsn=dsn)
            else:
                raise ValueError(f"Tipo de banco '{db_type}' não suportado para ITSM Tickets.")
        except Exception as e:
            logging.error(f"Erro ao conectar ao banco ITSM Tickets: {e}")
            raise ConnectionError(f"Erro ao conectar ao banco ITSM Tickets: {e}")