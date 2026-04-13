import os
import sqlite3
import sys


gcAppFolder = "GarageData"
gcDbName = "garage.db"


def getBaseDir():
    """
    Devuelve la carpeta base de la aplicación.

    - En desarrollo: raíz del proyecto
    - En ejecutable (.exe): carpeta donde está el ejecutable
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def getAppPath():
    """
    Devuelve la carpeta donde se guardarán los datos de la app.
    Si no existe, la crea.
    """
    lcAppPath = os.path.join(getBaseDir(), gcAppFolder)
    os.makedirs(lcAppPath, exist_ok=True)
    return lcAppPath


def getDbPath():
    """
    Devuelve la ruta completa del archivo de base de datos.
    """
    return os.path.join(getAppPath(), gcDbName)


def getConnection():
    """
    Crea y devuelve una conexión a SQLite.
    Activa soporte para foreign keys y permite acceder
    a las columnas por nombre.
    """
    lcDbPath = getDbPath()

    loConn = sqlite3.connect(lcDbPath, timeout=10)
    loConn.execute("PRAGMA foreign_keys = ON;")
    loConn.row_factory = sqlite3.Row

    return loConn