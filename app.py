"""
app.py
======
Servidor web Flask para el proyecto TLF.
Expone una API REST que conecta el frontend con los autómatas
implementados en automatas.py.

Herramientas usadas (recomendadas por el enunciado):
  - Python 3.x
  - Flask  (servidor web ligero)
  - json   (serialización de respuestas)

Rutas:
  GET  /                          → sirve la interfaz HTML
  POST /api/validar               → valida un campo individual
  POST /api/extraer               → extrae patrones de un texto libre
  GET  /api/referencia            → devuelve tabla de autómatas

Autores: Jean K. Méndez · Jhony A. Perea · Santiago Orozco
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
import pdfplumber
from docx import Document

from automatas import VALIDADORES, extraer_patrones

# ── Inicialización ──────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder='static',
    template_folder='template'
)
# ── Configuración para carga de archivos ────────────────────────────
CARPETA_UPLOADS = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(CARPETA_UPLOADS, exist_ok=True)
app.config['UPLOAD_FOLDER'] = CARPETA_UPLOADS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max
EXTENSIONES_PERMITIDAS = {'pdf', 'docx'}
# ── Datos de referencia de autómatas (para el panel /api/referencia) ────
REFERENCIA = [
    {
        "nombre":  "Correo Electrónico",
        "er":      "(A|S)⁺ @ D '.' E",
        "valido":  "profe@u.edu.co",
        "invalido":"user@com, @dom.co",
        "estados": "q0→q1(local)→q2(@)→q3(dominio)→q4(.)→q5(ext)*",
    },
    {
        "nombre":  "Número Telefónico",
        "er":      "3 D D '-' D⁷",
        "valido":  "310-1234567",
        "invalido":"310-123456, 31-1234567, 310 1234567",
        "estados": "q0→q1(3)→q2(D)→q3(D)→q4(-)→q5-q10(7 dígitos)*",
    },
    {
        "nombre":  "Fecha DD/MM/AAAA",
        "er":      "DD '/' MM '/' AAAA",
        "valido":  "25/12/2024",
        "invalido":"32/01/2024, 12-12-24",
        "estados": "q0→q1(d1)→q2(d2)→q3(/)→q4(m1)→q5(m2)→q6(/)→q7-q10(año)*",
    },
    {
        "nombre":  "Identificador / Código",
        "er":      "L⁺ D D D D D",
        "valido":  "ID12345, CODE54321",
        "invalido":"12345ID, ID123",
        "estados": "q0→q1(L)→q1(L*)→q2(d1)→q3→q4→q5→q6*",
    },
    {
        "nombre":  "Dirección URL",
        "er":      "P s* '://' (S'.')* D '.' E",
        "valido":  "https://google.com",
        "invalido":"www.google, http:/url.com",
        "estados": "q0(protocolo)→q1(://)→q2(www.)→q3(dom)→q4(.ext)*",
    },
    {
        "nombre":  "Placa de Vehículo",
        "er":      "L L L ('-'|' ') D D D",
        "valido":  "AAA-123",
        "invalido":"AA-1234, abc-123",
        "estados": "q0→q1→q2→q3(LLL)→q4(sep)→q5→q6→q7(DDD)*",
    },
    {
        "nombre":  "Dirección IPv4",
        "er":      "N '.' N '.' N '.' N   (N ∈ [0,255])",
        "valido":  "192.168.1.1",
        "invalido":"256.0.0.1, 192.168.1",
        "estados": "q0→q1(bloque1)→q2(.)→q3(bloque2)→…→q7(bloque4)*",
    },
    {
        "nombre":  "Monto Monetario",
        "er":      "'$' N⁺ ('.' N{3})* ',' N⁺",
        "valido":  "$ 1.500,00",
        "invalido":"1500, $ 1.50,0",
        "estados": "q0($)→q1(N)→q2(miles.)→q6(,)→q7(decimales)*",
    },
    {
        "nombre":  "Etiqueta HTML/XML",
        "er":      "'<' ('/')? N '>'",
        "valido":  "<div>, </div>",
        "invalido":"<3tag>, <>",
        "estados": "q0(<)→q1(/ o alfa)→q3(nombre)→q4(>)*",
    },
]


# ── Funciones auxiliares para procesar archivos ──────────────────────
def extensión_permitida(filename: str) -> bool:
    """Valida que la extensión del archivo sea permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

def extraer_texto_pdf(ruta_archivo: str) -> str:
    """Extrae texto de un archivo PDF."""
    texto = ""
    try:
        with pdfplumber.open(ruta_archivo) as pdf:
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ""
                texto += "\n"
    except Exception as e:
        return f"Error al procesar PDF: {str(e)}"
    return texto

def extraer_texto_docx(ruta_archivo: str) -> str:
    """Extrae texto de un archivo DOCX."""
    texto = ""
    try:
        doc = Document(ruta_archivo)
        for párrafo in doc.paragraphs:
            texto += párrafo.text + "\n"
    except Exception as e:
        return f"Error al procesar DOCX: {str(e)}"
    return texto

# ════════════════════════════════════════════════════════════════════════
# RUTAS
# ════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Sirve la página principal."""
    return render_template('index.html')


# ── POST /api/validar ───────────────────────────────────────────────────
@app.route('/api/validar', methods=['POST'])
def api_validar():
    """
    Valida un campo individual contra su autómata.

    Body JSON:
        { "tipo": "correo", "valor": "test@email.com" }

    Respuesta:
        { "valido": true, "mensaje": "Correo válido" }
    """
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"error": "Se esperaba JSON"}), 400

    tipo  = datos.get("tipo", "").strip()
    valor = datos.get("valor", "")

    if tipo not in VALIDADORES:
        tipos_disponibles = list(VALIDADORES.keys())
        return jsonify({
            "error": f"Tipo '{tipo}' no reconocido",
            "tipos_disponibles": tipos_disponibles
        }), 400

    resultado = VALIDADORES[tipo](valor)
    return jsonify(resultado)


# ── POST /api/extraer ───────────────────────────────────────────────────
@app.route('/api/extraer', methods=['POST'])
def api_extraer():
    """
    Extrae todos los patrones reconocibles de un texto libre.

    Body JSON:
        { "texto": "Contactar a juan@email.com o al 310-1234567..." }

    Respuesta:
        {
          "correos": ["juan@email.com"],
          "telefonos": ["310-1234567"],
          ...
        }
    """
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"error": "Se esperaba JSON"}), 400

    texto = datos.get("texto", "")
    if not isinstance(texto, str):
        return jsonify({"error": "El campo 'texto' debe ser una cadena"}), 400

    resultado = extraer_patrones(texto)

    # Agregar conteo total para la UI
    total = sum(len(v) for v in resultado.values())
    return jsonify({"patrones": resultado, "total": total})


# ── GET /api/referencia ─────────────────────────────────────────────────
@app.route('/api/referencia', methods=['GET'])
def api_referencia():
    """Devuelve la tabla de referencia de todos los autómatas."""
    return jsonify(REFERENCIA)


# ── GET /api/health ─────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def api_health():
    """Endpoint de salud para verificar que el servidor está activo."""
    return jsonify({"estado": "activo", "version": "1.0.0"})


# ── POST /api/procesar-archivo ──────────────────────────────────────────
@app.route('/api/procesar-archivo', methods=['POST'])
def api_procesar_archivo():
    """
    Procesa un archivo PDF o DOCX y extrae los patrones.

    Form-Data:
        archivo: (file) PDF o DOCX

    Respuesta:
        {
          "archivo": "documento.pdf",
          "patrones": { "correos": [...], "telefonos": [...] },
          "total": N
        }
    """
    if 'archivo' not in request.files:
        return jsonify({"error": "No se envió archivo"}), 400

    archivo = request.files['archivo']
    
    if archivo.filename == '':
        return jsonify({"error": "Archivo sin nombre"}), 400

    if not extensión_permitida(archivo.filename):
        return jsonify({
            "error": f"Tipo de archivo no permitido. Solo se aceptan: {', '.join(EXTENSIONES_PERMITIDAS)}"
        }), 400

    try:
        # Guardar archivo temporalmente
        nombre_seguro = secure_filename(archivo.filename)
        ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], nombre_seguro)
        archivo.save(ruta_archivo)

        # Extraer texto según el tipo de archivo
        ext = nombre_seguro.rsplit('.', 1)[1].lower()
        if ext == 'pdf':
            texto = extraer_texto_pdf(ruta_archivo)
        elif ext == 'docx':
            texto = extraer_texto_docx(ruta_archivo)
        else:
            return jsonify({"error": "Tipo de archivo no soportado"}), 400

        # Verificar si hubo error en la extracción
        if texto.startswith("Error al procesar"):
            return jsonify({"error": texto}), 500

        # Eliminar archivo temporal
        os.remove(ruta_archivo)

        # Extraer patrones del texto
        resultado = extraer_patrones(texto)
        total = sum(len(v) for v in resultado.values())

        return jsonify({
            "archivo": nombre_seguro,
            "patrones": resultado,
            "total": total
        })

    except Exception as e:
        # Limpiar en caso de error
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
        return jsonify({"error": f"Error al procesar archivo: {str(e)}"}), 500


# ════════════════════════════════════════════════════════════════════════
# ARRANQUE
# ════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    print(f"\n  TLF PatternEngine corriendo en http://localhost:{puerto}\n")
    app.run(debug=True, host='0.0.0.0', port=puerto)
