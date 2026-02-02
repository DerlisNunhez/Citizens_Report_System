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


def init_db():
    """Inicializa las tablas de la base de datos."""
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="usuarios"')
            tables = conn.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
            conn.close()
            if not tables:
                # archivo existe pero está vacío → eliminarlo
                os.remove(DB_PATH)
        except Exception:
            # cualquier error al leer → eliminarlo
            try:
                os.remove(DB_PATH)
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
            direccion       TEXT    NOT NULL,
            comentario      TEXT    NOT NULL,
            foto            TEXT    NOT NULL,
            email           TEXT,
            lat             REAL    NOT NULL,
            lng             REAL    NOT NULL,
            estado          TEXT    NOT NULL DEFAULT 'Pendiente',
            razon_rechazo   TEXT,
            fecha_creacion  TEXT    NOT NULL,
            usuario_correo  TEXT,
            FOREIGN KEY (usuario_correo) REFERENCES usuarios(correo)
        )
    ''')
    
    conn.commit()
    conn.close()


# ─── FUNCIONES DE USUARIOS ────────────────────────────────────────────

def crear_usuario(correo, contrasena, rol='usuario'):
    """
    Inserta un nuevo usuario.
    La contraseña se hashea automáticamente.
    Retorna True si se creó, False si el correo ya existe.
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
    """Compara la contraseña plana contra el hash."""
    return check_password_hash(hash_almacenado, contrasena)


# ─── FUNCIONES DE REPORTES ────────────────────────────────────────────

def crear_reporte(direccion, comentario, foto, email=None, lat=None, lng=None, usuario_correo=None):
    """
    Crea un nuevo reporte.
    Retorna el ID del reporte creado.
    """
    conn = get_db()
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor = conn.execute(
        '''INSERT INTO reportes 
           (direccion, comentario, foto, email, lat, lng, estado, fecha_creacion, usuario_correo)
           VALUES (?, ?, ?, ?, ?, ?, 'Pendiente', ?, ?)''',
        (direccion, comentario, foto, email, lat, lng, fecha, usuario_correo)
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
    Si el estado es 'Rechazado', debe incluir una razón.
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


def obtener_estadisticas():
    """
    Obtiene estadísticas de reportes por estado.
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