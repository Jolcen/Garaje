from database.schema import initializeDatabase
from database.db import getDbPath
from modulos.frmLogin import LoginWindow


def iniciarAplicacion():
    try:
        print("Iniciando sistema de garaje...")
        print(f"Ruta de la base de datos: {getDbPath()}")

        initializeDatabase()

        print("Base de datos creada/verificada correctamente.")
        print("Abriendo ventana de inicio de sesión...")

        loApp = LoginWindow()
        loApp.run()

    except Exception as loError:
        print("Ocurrió un error al iniciar el sistema:")
        print(str(loError))


if __name__ == "__main__":
    iniciarAplicacion()