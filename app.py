from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from werkzeug.utils import secure_filename
import os
from database import (
    init_db, crear_usuario, buscar_usuario_por_correo, verificar_contrasena,
    crear_reporte, obtener_reportes, obtener_reporte_por_id,
    actualizar_estado_reporte, actualizar_categoria_reporte, eliminar_reporte, obtener_estadisticas
)

app = Flask(__name__)

# Clave secreta para firmar las cookies de sesiÃ³n
app.secret_key = 'cambiar_esto_en_produccion_por_una_clave_segura'
app.config['PROPAGATE_EXCEPTIONS'] = True

# Configuracion de uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Crear carpeta de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Verifica si el archivo tiene una extensiÃ³n permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── DECORADORES DE PROTECCIÓN ────────────────────────────────────────────

def login_requerido(f):
    """Redirige a login si el usuario no estÃ¡ autenticado."""
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
    return redirect(url_for('index_publico'))


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
            error = 'Correo o contraseÃ±a incorrectos.'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_requerido
def logout():
    session.clear()
    return redirect(url_for('index_publico'))

@app.route('/index')
def index_publico():
    return render_template(
        'index.html',
        correo=session.get('correo'),
        rol=session.get('rol')
    )

@app.route('/dashboard')
@login_requerido
def dashboard():
    """Pagina principal para cualquier usuario autenticado."""
    return render_template('index.html', correo=session['correo'], rol=session['rol'])


@app.route('/admin')
@rol_admin_requerido
def admin():
    """Pagina exclusiva para administradores."""
    return render_template('index.html', correo=session['correo'], rol=session['rol'])


# ─── RUTAS DE REPORTES (API) ────────────────────────────────────────────────

@app.route('/api/reportes', methods=['GET'])
def listar_reportes():
    """Obtiene todos los reportes, opcionalmente filtrados por estado."""
    estado = request.args.get('estado', 'Todos')
    reportes = obtener_reportes(estado)
    
    # Si no es admin, ocultar emails
    if session.get('rol') != 'admin':
        for reporte in reportes:
            if 'email' in reporte:
                reporte['email'] = None
    
    return jsonify(reportes)


@app.route('/api/reportes', methods=['POST'])
@login_requerido
def crear_nuevo_reporte():
    try:
        # ─── CAMPOS DE TEXTO ───
        ubicacion  = request.form.get('ubicacion', '').strip()
        comentario = request.form.get('comentario', '').strip()
        email      = request.form.get('email', '').strip() or None

        # ─── COORDENADAS (MAPA) ───
        lat = request.form.get('lat')
        lng = request.form.get('lng')

        if not lat or not lng:
            return jsonify({'error': 'Debe marcar la ubicaciÃ³n en el mapa'}), 400

        # ─── VALIDACIONES ───
        if not ubicacion or len(ubicacion) < 5:
            return jsonify({'error': 'La dirección debe tener al menos 5 caracteres'}), 400

        if not comentario or len(comentario) < 10:
            return jsonify({'error': 'El comentario debe tener al menos 10 caracteres'}), 400

        # ─── FOTO ───
        if 'foto' not in request.files:
            return jsonify({'error': 'Falta la foto'}), 400

        foto = request.files['foto']

        if foto.filename == '':
            return jsonify({'error': 'No se seleccionÃ³ ningÃºn archivo'}), 400

        if not allowed_file(foto.filename):
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400

        filename = secure_filename(foto.filename)
        from datetime import datetime
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # ------- BD --------
        reporte_id = crear_reporte(
            ubicacion=ubicacion,
            comentario=comentario,
            foto=filename,
            email=email,
            lat=float(lat),
            lng=float(lng),
            usuario_correo=session.get('correo')
        )

        return jsonify({'success': True, 'message': 'Reporte enviado correctamente', 'id': reporte_id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/<int:reporte_id>', methods=['GET'])
@login_requerido
def obtener_reporte(reporte_id):
    """Obtiene un reporte específico por ID."""
    reporte = obtener_reporte_por_id(reporte_id)
    if reporte:
        # Si no es admin, ocultar email
        if session.get('rol') != 'admin' and 'email' in reporte:
            reporte['email'] = None
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
            return jsonify({'error': 'Estado no vÃ¡lido'}), 400
        
        # Si es rechazado, verificar que haya razón
        if nuevo_estado == 'Rechazado':
            if not razon_rechazo or len(razon_rechazo.strip()) < 10:
                return jsonify({'error': 'Debe proporcionar una razÃ³n de rechazo de al menos 10 caracteres'}), 400
        
        # Actualizar estado
        actualizar_estado_reporte(reporte_id, nuevo_estado, razon_rechazo)
        
        return jsonify({
            'success': True,
            'message': f'Estado actualizado a {nuevo_estado}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al actualizar estado: {str(e)}'}), 500


@app.route('/api/reportes/<int:reporte_id>/categoria', methods=['PUT'])
@rol_admin_requerido
def cambiar_categoria_reporte(reporte_id):
    """Cambia la categoría de un reporte (solo admin)."""
    try:
        data = request.get_json()
        nueva_categoria = data.get('categoria')
        
        # Validar categoría
        categorias_validas = [
            'Vías y Tránsito',
            'Alumbrado Público',
            'Agua y Saneamiento',
            'Residuos y Limpieza',
            'Parques y Espacios Públicos',
            'Electricidad y Telecomunicaciones',
            'Edificaciones Públicas',
            'Seguridad Urbana',
            'Transporte Público',
            'Otros'
        ]
        
        if nueva_categoria not in categorias_validas:
            return jsonify({'error': 'Categoría no válida'}), 400
        
        # Actualizar categoría
        actualizar_categoria_reporte(reporte_id, nueva_categoria)
        
        return jsonify({
            'success': True,
            'message': f'Categoría actualizada a {nueva_categoria}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al actualizar categoría: {str(e)}'}), 500


@app.route('/api/reportes/<int:reporte_id>', methods=['DELETE'])
@rol_admin_requerido
def eliminar_reporte_ruta(reporte_id):
    """Elimina un reporte (solo admin, requiere comentario)."""
    try:
        data = request.get_json()
        comentario = data.get('comentario', '').strip()
        
        # Validar que haya comentario
        if not comentario or len(comentario) < 10:
            return jsonify({'error': 'Debe proporcionar un comentario de al menos 10 caracteres explicando por qué elimina este reporte'}), 400
        
        # Verificar que el reporte existe
        reporte = obtener_reporte_por_id(reporte_id)
        if not reporte:
            return jsonify({'error': 'Reporte no encontrado'}), 404
        
        # Eliminar reporte
        eliminado = eliminar_reporte(reporte_id)
        
        if eliminado:
            return jsonify({
                'success': True,
                'message': f'Reporte eliminado. Razón: {comentario}'
            })
        else:
            return jsonify({'error': 'No se pudo eliminar el reporte'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Error al eliminar reporte: {str(e)}'}), 500


@app.route('/api/estadisticas', methods=['GET'])
@rol_admin_requerido
def obtener_estadisticas_reportes():
    """Obtiene estadÃ­sticas de reportes (solo admin)."""
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
    print("   admin   â†’ admin@ejemplo.com / admin123")
    print("   normal  â†’ usuario@ejemplo.com / usuario123")
    print("=" * 50)

    app.run(debug=True)