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

from automatas import VALIDADORES, extraer_patrones

# ── Inicialización ──────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder='static',
    template_folder='template'
)

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


# ════════════════════════════════════════════════════════════════════════
# ARRANQUE
# ════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    puerto = int(os.environ.get('PORT', 5000))
    print(f"\n  TLF PatternEngine corriendo en http://localhost:{puerto}\n")
    app.run(debug=True, host='0.0.0.0', port=puerto)
