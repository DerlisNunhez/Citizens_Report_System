# Citizens Report System

Sistema web para la gestión de reportes ciudadanos sobre problemas de infraestructura urbana. Permite a los usuarios reportar baches, alumbrado público defectuoso, problemas de agua y saneamiento, entre otros, con geolocalización y evidencia fotográfica.

## Descripción

Aplicación web desarrollada con Flask que facilita la comunicación entre ciudadanos y autoridades municipales mediante un sistema de reportes categorizados. Incluye autenticación de usuarios, panel administrativo, visualización en mapas interactivos y análisis estadístico de reportes.

## Tecnologías Utilizadas

**Backend:**
- Python 3.x
- Flask 3.0.0
- SQLite3
- Werkzeug 3.0.1 (seguridad y hash de contraseñas)
- Gunicorn 21.2.0 (servidor WSGI para producción)

**Frontend:**
- HTML5
- CSS3
- JavaScript (ES6+)
- Leaflet.js (mapas interactivos)

**Base de Datos:**
- SQLite con migraciones automáticas

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno (Chrome, Firefox, Edge, Safari)

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/Citizens_Report_System.git
cd Citizens_Report_System
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

## Configuración

### Variables de Entorno

Modificar la clave secreta en `app.py` antes de desplegar en producción:
```python
app.secret_key = 'tu_clave_secreta_aqui'
```

### Base de Datos

La base de datos se inicializa automáticamente al ejecutar la aplicación por primera vez. El archivo `db.sqlite3` se creará en el directorio raíz del proyecto.

### Directorio de Uploads

El sistema crea automáticamente la carpeta `static/uploads/` para almacenar las fotografías de los reportes.

## Ejecución

### Modo Desarrollo
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

### Modo Producción
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Credenciales de Prueba

El sistema incluye dos usuarios de prueba creados automáticamente:

**Administrador:**
- Correo: `admin@ejemplo.com`
- Contraseña: `admin123`

**Usuario Regular:**
- Correo: `usuario@ejemplo.com`
- Contraseña: `usuario123`

## Características Principales

### Para Usuarios Autenticados

- Creación de reportes con geolocalización
- Carga de evidencia fotográfica (hasta 25MB)
- Categorización de problemas (10 categorías disponibles)
- Visualización de reportes propios y públicos
- Mapa interactivo con todos los reportes
- Filtrado por estado (Pendiente, Verificando, Solucionado, Rechazado)

### Para Administradores

- Gestión completa de reportes
- Cambio de estado de reportes
- Reasignación de categorías
- Panel de analíticas con estadísticas en tiempo real
- Gráficos de distribución por estado
- Eliminación de reportes (con justificación obligatoria)
- Acceso a información de contacto de reportantes

### Sistema de Categorías

- Vías y Tránsito
- Alumbrado Público
- Agua y Saneamiento
- Residuos y Limpieza
- Parques y Espacios Públicos
- Electricidad y Telecomunicaciones
- Edificaciones Públicas
- Seguridad Urbana
- Transporte Público
- Otros

## Estructura del Proyecto
```
Citizens_Report_System/
│
├── app.py                  # Aplicación Flask principal
├── database.py             # Capa de acceso a datos
├── requirements.txt        # Dependencias del proyecto
├── .gitignore             # Archivos ignorados por Git
├── README.md              # Documentación del proyecto
│
├── static/                # Archivos estáticos
│   ├── styles.css         # Estilos principales
│   ├── login_style.css    # Estilos de autenticación
│   ├── script.js          # Lógica del frontend
│   └── uploads/           # Fotografías de reportes
│
└── templates/             # Plantillas HTML
    ├── index.html         # Dashboard principal
    ├── login.html         # Página de login
    └── register.html      # Página de registro
```

## API Endpoints

### Reportes

- `GET /api/reportes` - Listar todos los reportes
- `GET /api/reportes?estado=<estado>` - Filtrar por estado
- `GET /api/reportes/<id>` - Obtener reporte específico
- `POST /api/reportes` - Crear nuevo reporte (autenticado)
- `PUT /api/reportes/<id>/estado` - Actualizar estado (admin)
- `PUT /api/reportes/<id>/categoria` - Actualizar categoría (admin)
- `DELETE /api/reportes/<id>` - Eliminar reporte (admin)

### Estadísticas

- `GET /api/estadisticas` - Obtener estadísticas generales (admin)

## Seguridad

- Autenticación basada en sesiones
- Hash de contraseñas con Werkzeug
- Validación de archivos subidos
- Protección contra inyección SQL (parametrización de consultas)
- Sanitización de HTML en el frontend
- Control de acceso basado en roles

## Consideraciones de Producción

1. Cambiar `app.secret_key` por una clave segura generada aleatoriamente
2. Configurar HTTPS
3. Implementar rate limiting
4. Configurar backups automáticos de la base de datos
5. Establecer políticas de retención de imágenes
6. Configurar logs de aplicación
7. Implementar monitoreo de errores

## Licencia

Este proyecto es de código abierto. Consultar el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, crear un issue para discutir cambios mayores antes de enviar un pull request.
