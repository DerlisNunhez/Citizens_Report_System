import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Ruta absoluta al archivo de base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')


def get_db():
    """Conecta a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acceder por nombre de columna
    return conn


def migrar_columna_categoria():
    """Agrega la columna categoria si no existe (migraciÃ³n automÃ¡tica)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(reportes)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'categoria' not in columnas:
            print("„ Migrando base de datos: agregando columna 'categoria'...")
            cursor.execute('''
                ALTER TABLE reportes 
                ADD COLUMN categoria TEXT NOT NULL DEFAULT 'Otros'
            ''')
            conn.commit()
            print(" Columna 'categoria' agregada exitosamente")
        
        conn.close()
    except Exception as e:
        print(f" Error en migracion: {e}")


def init_db():
    """Inicializa las tablas de la base de datos."""
    db_existe = os.path.exists(DB_PATH)
    
    if db_existe:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="usuarios"')
            tables = conn.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
            conn.close()
            if not tables:
                # archivo existe pero estÃ¡ vacÃ­o â†’ eliminarlo
                os.remove(DB_PATH)
                db_existe = False
        except Exception:
            # cualquier error al leer → eliminarlo
            try:
                os.remove(DB_PATH)
                db_existe = False
            except Exception:
                pass

    conn = get_db()
    
    # Tabla de usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            correo    TEXT    UNIQUE NOT NULL,
            contrasena TEXT   NOT NULL,
            rol       TEXT    NOT NULL DEFAULT 'usuario'
        )
    ''')
    
    # Tabla de reportes
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ubicacion       TEXT    NOT NULL,
            comentario      TEXT    NOT NULL,
            foto            TEXT    NOT NULL,
            email           TEXT,
            categoria       TEXT    NOT NULL DEFAULT 'Otros',
            estado          TEXT    NOT NULL DEFAULT 'Pendiente',
            razon_rechazo   TEXT,
            lat             REAL    NOT NULL,
            lng             REAL    NOT NULL,
            fecha_creacion  TEXT    NOT NULL,
            usuario_correo  TEXT,
            FOREIGN KEY (usuario_correo) REFERENCES usuarios(correo)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Si la base de datos ya existi­a, ejecutar migraciones automÃ¡ticas
    if db_existe:
        migrar_columna_categoria()


# -------------FUNCIONES DE USUARIOS---------------------------------------------------------------------------------------------------------------

def crear_usuario(correo, contrasena, rol='usuario'):
    """
    Inserta un nuevo usuario.
    La contraseña se hashea automÃ¡ticamente.
    Retorna True si se crea, False si el correo ya existe.
    """
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO usuarios (correo, contrasena, rol) VALUES (?, ?, ?)',
            (correo, generate_password_hash(contrasena), rol)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # correo duplicado
        return False
    finally:
        conn.close()


def buscar_usuario_por_correo(correo):
    """Retorna la fila del usuario o None."""
    conn = get_db()
    usuario = conn.execute(
        'SELECT * FROM usuarios WHERE correo = ?', (correo,)
    ).fetchone()
    conn.close()
    return usuario


def verificar_contrasena(contrasena, hash_almacenado):
    """Compara la contraseÃ±a plana contra el hash."""
    return check_password_hash(hash_almacenado, contrasena)


#---------------FUNCIONES DE REPORTES---------------------------------------------------------------------------------------------------------

def crear_reporte(ubicacion, comentario, foto, lat=None, lng=None, categoria='Otros', email=None, usuario_correo=None):
    """
    Crea un nuevo reporte.
    Retorna el ID del reporte creado.
    """
    conn = get_db()
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor = conn.execute(
        '''INSERT INTO reportes 
           (ubicacion, comentario, foto, categoria, email, lat, lng, estado, fecha_creacion, usuario_correo)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?)''',
        (ubicacion, comentario, foto, categoria, email, lat, lng, fecha, usuario_correo)
    )
    conn.commit()
    reporte_id = cursor.lastrowid
    conn.close()
    return reporte_id


def obtener_reportes(estado=None):
    """
    Obtiene todos los reportes, opcionalmente filtrados por estado.
    Retorna una lista de diccionarios.
    """
    conn = get_db()
    
    if estado and estado != 'Todos':
        reportes = conn.execute(
            'SELECT * FROM reportes WHERE estado = ? ORDER BY fecha_creacion DESC',
            (estado,)
        ).fetchall()
    else:
        reportes = conn.execute(
            'SELECT * FROM reportes ORDER BY fecha_creacion DESC'
        ).fetchall()
    
    conn.close()
    
    # Convertir Row objects a diccionarios
    return [dict(r) for r in reportes]


def obtener_reporte_por_id(reporte_id):
    """Obtiene un reporte específico por su ID."""
    conn = get_db()
    reporte = conn.execute(
        'SELECT * FROM reportes WHERE id = ?',
        (reporte_id,)
    ).fetchone()
    conn.close()
    return dict(reporte) if reporte else None


def actualizar_estado_reporte(reporte_id, nuevo_estado, razon_rechazo=None):
    """
    Actualiza el estado de un reporte.
    Si el estado es 'Rechazado', debe incluir una razÃ³n.
    """
    conn = get_db()
    
    if nuevo_estado == 'Rechazado':
        conn.execute(
            'UPDATE reportes SET estado = ?, razon_rechazo = ? WHERE id = ?',
            (nuevo_estado, razon_rechazo, reporte_id)
        )
    else:
        conn.execute(
            'UPDATE reportes SET estado = ?, razon_rechazo = NULL WHERE id = ?',
            (nuevo_estado, reporte_id)
        )
    
    conn.commit()
    conn.close()


def actualizar_categoria_reporte(reporte_id, nueva_categoria):
    """
    Actualiza la categoria de un reporte (solo admin).
    """
    conn = get_db()
    conn.execute(
        'UPDATE reportes SET categoria = ? WHERE id = ?',
        (nueva_categoria, reporte_id)
    )
    conn.commit()
    conn.close()


def eliminar_reporte(reporte_id):
    """
    Elimina un reporte por su ID (solo admin).
    Retorna True si se eliminÃ³, False si no existÃ­a.
    """
    conn = get_db()
    cursor = conn.execute(
        'DELETE FROM reportes WHERE id = ?',
        (reporte_id,)
    )
    conn.commit()
    eliminado = cursor.rowcount > 0
    conn.close()
    return eliminado


def obtener_estadisticas():
    """
    Obtiene estadÃ­sticas de reportes por estado.
    Retorna un diccionario con el conteo de cada estado.
    """
    conn = get_db()
    
    stats = {
        'Pendiente': 0,
        'Verificando': 0,
        'Solucionado': 0,
        'Rechazado': 0,
        'Total': 0
    }
    
    # Contar reportes por estado
    resultados = conn.execute(
        '''SELECT estado, COUNT(*) as cantidad 
           FROM reportes 
           GROUP BY estado'''
    ).fetchall()
    
    for row in resultados:
        estado = row['estado']
        cantidad = row['cantidad']
        if estado in stats:
            stats[estado] = cantidad
        stats['Total'] += cantidad
    
    conn.close()
    return stats