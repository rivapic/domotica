#!/usr/bin/env python3
"""Helpers for MariaDB connection and inserting device status JSON.

Usage: from db_mariadb import insert_status_db
"""
import json
import os
import pymysql

def get_db_config():
    db_defaults = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASS', ''),
        'db': os.getenv('DB_NAME', 'domotica'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'charset': 'utf8mb4',
    }
    try:
        with open('credentials.json', 'r') as cf:
            cj = json.load(cf)
            mariadb = cj.get('mariadb', {}) or {}
            if mariadb:
                db_defaults.update({
                    'host': mariadb.get('host', db_defaults['host']),
                    'user': mariadb.get('user', db_defaults['user']),
                    'password': mariadb.get('password', db_defaults['password']),
                    'db': mariadb.get('database', db_defaults['db']),
                    'port': int(mariadb.get('port', db_defaults['port'])),
                })
    except Exception:
        pass
    return db_defaults


def ensure_table(conn, table_name='device_status'):
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                device_name VARCHAR(255),
                ts DATETIME,
                status_json LONGTEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
    conn.commit()


def insert_status_db(device_name, status_obj, table_name='device_status'):
    db_conf = get_db_config()
    try:
        conn = pymysql.connect(host=db_conf['host'], user=db_conf['user'], password=db_conf['password'],
                               database=db_conf['db'], port=int(db_conf['port']), charset=db_conf.get('charset','utf8mb4'))
        try:
            ensure_table(conn, table_name)
            with conn.cursor() as cur:
                cur.execute(f"INSERT INTO {table_name} (device_name, ts, status_json) VALUES (%s, NOW(), %s)",
                            (device_name, json.dumps(status_obj)))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        # raise the exception to the caller to decide how to handle it
        raise
