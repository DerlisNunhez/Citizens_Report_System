from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from werkzeug.utils import secure_filename
import os
from database import (
    init_db, crear_usuario, buscar_usuario_por_correo, verificar_contrasena,
    crear_reporte, obtener_reportes, obtener_reporte_por_id,
    actualizar_estado_reporte, obtener_estadisticas
)

app = Flask(__name__)

# Clave secreta para firmar las cookies de sesión
app.secret_key = 'cambiar_esto_en_produccion_por_una_clave_segura'
app.config['PROPAGATE_EXCEPTIONS'] = True

# Configuración de uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Crear carpeta de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── DECORADORES DE PROTECCIÓN ────────────────────────────────────────────

def login_requerido(f):
    """Redirige a login si el usuario no está autenticado."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if 'correo' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorado


def rol_admin_requerido(f):
    """Solo permite acceso si el usuario tiene rol 'admin'."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if 'correo' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            return jsonify({'error': 'Sin permiso'}), 403
        return f(*args, **kwargs)
    return decorado


# ─── RUTAS DE AUTENTICACIÓN ────────────────────────────────────────────────

@app.route('/')
def home():
    """Raíz: si ya logueado va al dashboard, sino al login."""
    if 'correo' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        correo     = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '')

        # buscar usuario en la BD
        usuario = buscar_usuario_por_correo(correo)

        if usuario and verificar_contrasena(contrasena, usuario['contrasena']):
            # ─── LOGIN EXITOSO ───
            session['correo'] = usuario['correo']
            session['rol']    = usuario['rol']
            session.permanent = True

            # redirigir según rol
            if usuario['rol'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            error = 'Correo o contraseña incorrectos.'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_requerido
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_requerido
def dashboard():
    """Página principal para cualquier usuario autenticado."""
    return render_template('index.html', correo=session['correo'], rol=session['rol'])


@app.route('/admin')
@rol_admin_requerido
def admin():
    """Página exclusiva para administradores."""
    return render_template('index.html', correo=session['correo'], rol=session['rol'])


# ─── RUTAS DE REPORTES (API) ────────────────────────────────────────────────

@app.route('/api/reportes', methods=['GET'])
@login_requerido
def listar_reportes():
    """Obtiene todos los reportes, opcionalmente filtrados por estado."""
    estado = request.args.get('estado', 'Todos')
    reportes = obtener_reportes(estado)
    return jsonify(reportes)


@app.route('/api/reportes', methods=['POST'])
@login_requerido
def crear_nuevo_reporte():
    """Crea un nuevo reporte con la foto subida."""
    try:
        # Validar campos requeridos
        direccion = request.form.get('direccion', '').strip()
        comentario = request.form.get('comentario', '').strip()
        email = request.form.get('email', '').strip() or None
        
        if not direccion or len(direccion) < 5:
            return jsonify({'error': 'La dirección debe tener al menos 5 caracteres'}), 400
        
        if not comentario or len(comentario) < 10:
            return jsonify({'error': 'El comentario debe tener al menos 10 caracteres'}), 400
        
        # Validar y guardar foto
        if 'foto' not in request.files:
            return jsonify({'error': 'Falta la foto'}), 400
        
        foto = request.files['foto']
        
        if foto.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        if not allowed_file(foto.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Use JPG, PNG o WEBP'}), 400
        
        # Guardar archivo con nombre seguro
        filename = secure_filename(foto.filename)
        # Agregar timestamp para evitar colisiones
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(filepath)
        
        # Crear reporte en la BD
        reporte_id = crear_reporte(
            direccion=direccion,
            comentario=comentario,
            foto=filename,
            email=email,
            usuario_correo=session.get('correo')
        )
        
        return jsonify({
            'success': True,
            'message': 'Reporte creado exitosamente',
            'id': reporte_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Error al crear el reporte: {str(e)}'}), 500


@app.route('/api/reportes/<int:reporte_id>', methods=['GET'])
@login_requerido
def obtener_reporte(reporte_id):
    """Obtiene un reporte específico por ID."""
    reporte = obtener_reporte_por_id(reporte_id)
    if reporte:
        return jsonify(reporte)
    return jsonify({'error': 'Reporte no encontrado'}), 404


@app.route('/api/reportes/<int:reporte_id>/estado', methods=['PUT'])
@rol_admin_requerido
def cambiar_estado_reporte(reporte_id):
    """Cambia el estado de un reporte (solo admin)."""
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        razon_rechazo = data.get('razon_rechazo')
        
        # Validar estado
        estados_validos = ['Pendiente', 'Verificando', 'Solucionado', 'Rechazado']
        if nuevo_estado not in estados_validos:
            return jsonify({'error': 'Estado no válido'}), 400
        
        # Si es rechazado, verificar que haya razón
        if nuevo_estado == 'Rechazado':
            if not razon_rechazo or len(razon_rechazo.strip()) < 10:
                return jsonify({'error': 'Debe proporcionar una razón de rechazo de al menos 10 caracteres'}), 400
        
        # Actualizar estado
        actualizar_estado_reporte(reporte_id, nuevo_estado, razon_rechazo)
        
        return jsonify({
            'success': True,
            'message': f'Estado actualizado a {nuevo_estado}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al actualizar estado: {str(e)}'}), 500


@app.route('/api/estadisticas', methods=['GET'])
@rol_admin_requerido
def obtener_estadisticas_reportes():
    """Obtiene estadísticas de reportes (solo admin)."""
    stats = obtener_estadisticas()
    return jsonify(stats)


# ─── INICIALIZACIÓN ────────────────────────────────────────────────────────

# Crear tabla al importar
init_db()
crear_usuario('admin@ejemplo.com',  'admin123', rol='admin')
crear_usuario('usuario@ejemplo.com','usuario123', rol='usuario')

if __name__ == '__main__':
    from database import DB_PATH
    print("=" * 50)
    print(f" DB usada: {DB_PATH}")
    print(" Usuarios de prueba:")
    print("   admin   → admin@ejemplo.com / admin123")
    print("   normal  → usuario@ejemplo.com / usuario123")
    print("=" * 50)

    app.run(debug=True)