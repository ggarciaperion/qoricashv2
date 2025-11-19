import os
import sys
from urllib.parse import urlparse

def masked(u):
    if not u:
        return None
    p = urlparse(u)
    user = p.username or ''
    host = p.hostname or ''
    port = p.port or ''
    path = p.path or ''
    return f"{p.scheme}://{user}:***@{host}:{port}{path}"

url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
print("URL encontrada (enmascarada):", masked(url))

if not url:
    print("ERROR: No se encontró SQLALCHEMY_DATABASE_URI ni DATABASE_URL en el entorno.")
    sys.exit(2)

try:
    import psycopg2
except Exception as e:
    print("ERROR: psycopg2 no está disponible:", e)
    sys.exit(3)

def try_connect(u):
    try:
        conn = psycopg2.connect(u)
        conn.close()
        print("Conexión psycopg2 OK con URL:", masked(u))
        return True
    except Exception as e:
        print("Error al conectar:", repr(e))
        return False

if try_connect(url):
    sys.exit(0)

if "sslmode" not in url:
    sep = "&" if "?" in url else "?"
    url2 = url + sep + "sslmode=require"
    print("Primer intento falló. Probando con sslmode=require...")
    if try_connect(url2):
        print("Conexión OK usando sslmode=require")
        sys.exit(0)
    else:
        print("Sigue fallando incluso con sslmode=require.")
        sys.exit(1)
else:
    print("La URL ya contenía sslmode y el intento falló.")
    sys.exit(1)
