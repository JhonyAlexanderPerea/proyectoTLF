"""
automatas.py
============
Módulo de autómatas finitos deterministas (AFD) para validación y
extracción de patrones. Implementados manualmente, sin usar la
librería 're' de Python.

Cada función recibe una cadena y retorna un dict:
    { "valido": bool, "mensaje": str }

Autores: Jean K. Méndez · Jhony A. Perea · Santiago Orozco
Materia: Teoría de Lenguajes Formales
"""

# ── Helpers ────────────────────────────────────────────────────────────────

def _es_alfa(c: str) -> bool:
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z')

def _es_digito(c: str) -> bool:
    return '0' <= c <= '9'

def _es_alfanum(c: str) -> bool:
    return _es_alfa(c) or _es_digito(c)

def _es_mayuscula(c: str) -> bool:
    return 'A' <= c <= 'Z'

def _es_minuscula(c: str) -> bool:
    return 'a' <= c <= 'z'

def _es_dom_char(c: str) -> bool:
    """Carácter válido en un nombre de dominio."""
    return _es_alfanum(c) or c == '-'

def _ok(msg: str = "Válido") -> dict:
    return {"valido": True, "mensaje": msg}

def _err(msg: str) -> dict:
    return {"valido": False, "mensaje": msg}


# ══════════════════════════════════════════════════════════════════════════
# 1. CORREO ELECTRÓNICO
#    ER: (A|S)+ @ D "." E
#    Estados: q0→q1(local)→q2(@)→q3(dominio)→q4(.)→q5(extensión)*
# ══════════════════════════════════════════════════════════════════════════

def validar_correo(cadena: str) -> dict:
    """
    Valida un correo electrónico mediante AFD.

    Alfabeto:
        A = caracteres alfanuméricos
        S = caracteres especiales permitidos: . _ - +
        D = caracteres de dominio (alfanum + guión)
        E = letras (extensión)

    Transiciones:
        q0 --(A|S)--> q1
        q1 --(A|S)--> q1   (self-loop parte local)
        q1 --(@)---> q2
        q2 --(D)---> q3
        q3 --(D)---> q3    (self-loop dominio)
        q3 --(.)---> q4
        q4 --(E)---> q5
        q5 --(E)---> q5    (self-loop extensión)
        q5 --(.)---> q4    (dominio compuesto: .edu.co)
    Estado de aceptación: q5 (extensión ≥ 2 caracteres)
    """
    if not cadena:
        return _err("Campo vacío")

    ESPECIALES = set("._-+")
    estado = 0
    ext_len = 0

    for i, c in enumerate(cadena):
        if estado == 0:
            if _es_alfanum(c) or c in ESPECIALES:
                estado = 1
            else:
                return _err(f"Carácter inválido al inicio: '{c}'")

        elif estado == 1:
            if _es_alfanum(c) or c in ESPECIALES:
                pass  # se queda en q1
            elif c == '@':
                estado = 2
            else:
                return _err(f"Carácter inválido en parte local: '{c}'")

        elif estado == 2:
            if _es_dom_char(c):
                estado = 3
            else:
                return _err("Se esperaba nombre de dominio tras '@'")

        elif estado == 3:
            if _es_dom_char(c):
                pass  # se queda en q3
            elif c == '.':
                estado = 4
            else:
                return _err(f"Carácter inválido en dominio: '{c}'")

        elif estado == 4:
            if _es_alfa(c):
                estado = 5
                ext_len = 1
            else:
                return _err("Se esperaba extensión tras el punto")

        elif estado == 5:
            if _es_alfa(c):
                ext_len += 1
            elif c == '.':
                estado = 4   # dominio compuesto (.edu.co)
            else:
                return _err(f"Carácter inválido en extensión: '{c}'")

    # Verificar estado final
    if estado == 5 and ext_len >= 2:
        return _ok("Correo electrónico válido")
    if estado == 1:
        return _err("Falta el símbolo '@'")
    if estado == 2:
        return _err("Falta el nombre de dominio")
    if estado == 3:
        return _err("Falta la extensión (.com, .edu.co…)")
    if estado == 4:
        return _err("Extensión incompleta tras el punto")
    if estado == 5 and ext_len < 2:
        return _err("La extensión debe tener al menos 2 letras")
    return _err("Formato de correo inválido")


# ══════════════════════════════════════════════════════════════════════════
# 2. NÚMERO TELEFÓNICO
#    ER: 3 N N ("-"|" ")? N N N N N N N   (10 dígitos, separador opcional)
#    El primer dígito DEBE ser 3.
# ══════════════════════════════════════════════════════════════════════════

def validar_telefono(cadena: str) -> dict:
    """
    Valida un número telefónico colombiano (10 dígitos, inicia con 3).

    Transiciones (contando dígitos):
        q0  --('3')--> q1   (digitos=1)
        q1  --(D)-->   q1   (acumula dígitos)
        q1  --('-'|' ')--> q1  (separador único, solo tras 3 dígitos)
    Estado de aceptación: 10 dígitos totales contados.
    """
    if not cadena:
        return _err("Campo vacío")

    SEPARADORES = {'-', ' '}
    contador_digitos = 0
    separador_usado = False

    for i, c in enumerate(cadena):
        if _es_digito(c):
            contador_digitos += 1
            if contador_digitos == 1 and c != '3':
                return _err("El número debe iniciar con 3 (telefonía móvil colombiana)")
            if contador_digitos > 10:
                return _err("El número tiene más de 10 dígitos")
        elif c in SEPARADORES:
            if separador_usado:
                return _err("Solo se permite un separador")
            if contador_digitos != 3:
                return _err("El separador debe ir después del prefijo de 3 dígitos")
            separador_usado = True
        else:
            return _err(f"Carácter no permitido: '{c}'")

    if contador_digitos < 10:
        return _err(f"Número incompleto: {contador_digitos}/10 dígitos")
    return _ok("Número telefónico válido")


# ══════════════════════════════════════════════════════════════════════════
# 3. FECHA (DD/MM/AAAA)
#    Valida estructura y sentido cronológico (días por mes + bisiestos).
# ══════════════════════════════════════════════════════════════════════════

def _es_bisiesto(anio: int) -> bool:
    return (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)

def validar_fecha(cadena: str) -> dict:
    """
    Valida fecha en formato DD/MM/AAAA mediante AFD de 10 estados.

    Estados: q0→q1(d1)→q2(d2)→q3(/)→q4(m1)→q5(m2)→q6(/)→q7(a1)→q8(a2)→q9(a3)→q10(a4)*
    """
    if not cadena:
        return _err("Campo vacío")

    # Tabla de estados: esperamos exactamente 10 caracteres con / en pos 2 y 5
    estado = 0
    buf = []

    for c in cadena:
        if estado in (0, 1):          # dígitos del día
            if not _es_digito(c):
                return _err(f"Se esperaba dígito para el día, encontrado '{c}'")
            buf.append(c)
            estado += 1

        elif estado == 2:              # primer separador /
            if c != '/':
                return _err(f"Se esperaba '/' tras el día, encontrado '{c}'")
            estado = 3

        elif estado in (3, 4):         # dígitos del mes
            if not _es_digito(c):
                return _err(f"Se esperaba dígito para el mes, encontrado '{c}'")
            buf.append(c)
            estado += 1

        elif estado == 5:              # segundo separador /
            if c != '/':
                return _err(f"Se esperaba '/' tras el mes, encontrado '{c}'")
            estado = 6

        elif estado in (6, 7, 8, 9):  # 4 dígitos del año
            if not _es_digito(c):
                return _err(f"Se esperaba dígito para el año, encontrado '{c}'")
            buf.append(c)
            estado += 1

        elif estado == 10:
            return _err("Fecha demasiado larga (se esperaba DD/MM/AAAA)")

    if estado < 10:
        return _err("Fecha incompleta (formato esperado: DD/MM/AAAA)")

    dd   = int(buf[0] + buf[1])
    mm   = int(buf[2] + buf[3])
    aaaa = int(buf[4] + buf[5] + buf[6] + buf[7])

    if mm < 1 or mm > 12:
        return _err(f"Mes inválido: {mm} (debe estar entre 01 y 12)")
    if dd < 1:
        return _err("El día no puede ser 0")
    if aaaa < 1:
        return _err("El año no puede ser 0")

    bisiesto = _es_bisiesto(aaaa)
    dias_en_mes = [0, 31, 29 if bisiesto else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if dd > dias_en_mes[mm]:
        extra = " (año bisiesto)" if bisiesto and mm == 2 else ""
        return _err(f"El mes {mm:02d} no tiene {dd} días{extra}")

    nota = " (año bisiesto)" if bisiesto and mm == 2 and dd == 29 else ""
    return _ok(f"Fecha válida{nota}")


# ══════════════════════════════════════════════════════════════════════════
# 4. IDENTIFICADOR / CÓDIGO
#    ER: L+ D D D D D   (≥1 letra mayúscula seguida de exactamente 5 dígitos)
# ══════════════════════════════════════════════════════════════════════════

def validar_identificador(cadena: str) -> dict:
    """
    Valida un código de la forma: una o más letras mayúsculas + 5 dígitos.

    Transiciones:
        q0 --(L)--> q1
        q1 --(L)--> q1   (self-loop letras adicionales)
        q1 --(D)--> q2
        q2 --(D)--> q3
        q3 --(D)--> q4
        q4 --(D)--> q5
        q5 --(D)--> q6*  (estado de aceptación)
    """
    if not cadena:
        return _err("Campo vacío")

    estado = 0

    for c in cadena:
        if estado == 0:
            if _es_mayuscula(c):
                estado = 1
            elif _es_minuscula(c):
                return _err("Las letras deben ser mayúsculas")
            elif _es_digito(c):
                return _err("Debe comenzar con al menos una letra mayúscula")
            else:
                return _err(f"Carácter inválido: '{c}'")

        elif estado == 1:
            if _es_mayuscula(c):
                pass  # más letras, se queda en q1
            elif _es_digito(c):
                estado = 2
            else:
                return _err(f"Carácter inválido tras las letras: '{c}'")

        elif estado in (2, 3, 4, 5):
            if _es_digito(c):
                estado += 1
            else:
                return _err(f"Se esperaba dígito, encontrado '{c}'")

        elif estado == 6:
            return _err("El código debe tener exactamente 5 dígitos")

    if estado == 6:
        return _ok("Identificador válido")
    if estado in (0, 1):
        return _err("Faltan los 5 dígitos numéricos")
    faltan = 6 - estado
    return _err(f"Faltan {faltan} dígito(s)")


# ══════════════════════════════════════════════════════════════════════════
# 5. DIRECCIÓN URL
#    ER: P s* "://" (S".")* D "." E
# ══════════════════════════════════════════════════════════════════════════

def validar_url(cadena: str) -> dict:
    """
    Valida una URL con protocolo http o https.

    Transiciones (por índice manual):
        q0: leer protocolo 'http' o 'https'
        q1: leer '://'
        q2: opcional 'www.'
        q3: leer nombre de dominio (≥1 char)
        q4: leer '.' + extensión (≥2 letras)
    """
    if not cadena:
        return _err("Campo vacío")

    idx = 0
    n = len(cadena)

    # q0: protocolo
    if cadena[idx:idx+8] == 'https://':
        idx += 8
    elif cadena[idx:idx+7] == 'http://':
        idx += 7
    else:
        return _err("Debe iniciar con 'http://' o 'https://'")

    # q2: subdominio www. (opcional)
    if cadena[idx:idx+4] == 'www.':
        idx += 4

    # q3: nombre de dominio principal (al menos 1 carácter)
    inicio_dom = idx
    while idx < n and (_es_dom_char(cadena[idx])):
        idx += 1

    if idx == inicio_dom:
        return _err("Falta el nombre de dominio")

    # q4: debe haber al menos un punto con extensión
    if idx >= n or cadena[idx] != '.':
        return _err("Falta el punto y la extensión del dominio")

    idx += 1  # consumir el punto
    inicio_ext = idx
    while idx < n and _es_alfa(cadena[idx]):
        idx += 1

    ext_len = idx - inicio_ext
    if ext_len < 2:
        return _err("La extensión del dominio debe tener al menos 2 letras")

    # El resto (ruta, query, etc.) se acepta libremente
    return _ok("URL válida")


# ══════════════════════════════════════════════════════════════════════════
# 6. PLACA DE VEHÍCULO
#    ER: L L L ("-"|" ") D D D
# ══════════════════════════════════════════════════════════════════════════

def validar_placa(cadena: str) -> dict:
    """
    Valida placas vehiculares colombianas: 3 letras mayúsculas + separador + 3 dígitos.

    Transiciones:
        q0 --(L)--> q1
        q1 --(L)--> q2
        q2 --(L)--> q3
        q3 --('-'|' ')--> q4
        q4 --(D)--> q5
        q5 --(D)--> q6
        q6 --(D)--> q7*
    """
    if not cadena:
        return _err("Campo vacío")

    SEPARADORES = {'-', ' '}
    estado = 0

    for c in cadena:
        if estado in (0, 1, 2):
            if _es_mayuscula(c):
                estado += 1
            elif _es_minuscula(c):
                return _err("Las letras de la placa deben ser mayúsculas")
            else:
                return _err(f"Se esperaba letra mayúscula, encontrado '{c}'")

        elif estado == 3:
            if c in SEPARADORES:
                estado = 4
            else:
                return _err(f"Se esperaba '-' o espacio como separador, encontrado '{c}'")

        elif estado in (4, 5, 6):
            if _es_digito(c):
                estado += 1
            else:
                return _err(f"Se esperaba dígito, encontrado '{c}'")

        elif estado == 7:
            return _err("La placa debe tener exactamente 3 dígitos")

    if estado == 7:
        return _ok("Placa de vehículo válida")
    if estado < 3:
        return _err(f"Faltan letras ({estado}/3)")
    if estado == 3:
        return _err("Falta el separador y los 3 dígitos")
    return _err(f"Faltan {7 - estado} dígito(s)")


# ══════════════════════════════════════════════════════════════════════════
# 7. DIRECCIÓN IPv4
#    ER: N "." N "." N "." N   donde N ∈ [0, 255]
# ══════════════════════════════════════════════════════════════════════════

def validar_ipv4(cadena: str) -> dict:
    """
    Valida una dirección IPv4 con 4 bloques numéricos separados por puntos.

    Transiciones:
        q0 --(D)--> q1   (primer bloque)
        q1 --(D)--> q1   (self-loop)
        q1 --(.)---> q2  (siguiente bloque)
        ... repite 3 veces
        q7*  estado de aceptación (4 bloques leídos)
    """
    if not cadena:
        return _err("Campo vacío")

    bloques = []
    bloque_actual = ""

    for c in cadena:
        if _es_digito(c):
            bloque_actual += c
            if len(bloque_actual) > 3:
                return _err(f"Bloque demasiado largo: '{bloque_actual}'")
        elif c == '.':
            if bloque_actual == '':
                return _err("Bloque vacío antes del punto")
            bloques.append(bloque_actual)
            bloque_actual = ""
            if len(bloques) > 3:
                return _err("Una IPv4 tiene exactamente 3 puntos")
        else:
            return _err(f"Carácter inválido: '{c}'")

    if bloque_actual:
        bloques.append(bloque_actual)

    if len(bloques) != 4:
        return _err(f"Se necesitan 4 bloques, se encontraron {len(bloques)}")

    for b in bloques:
        n = int(b)
        if n < 0 or n > 255:
            return _err(f"Bloque '{b}' fuera de rango (0–255)")
        if len(b) > 1 and b[0] == '0':
            return _err(f"Cero inicial inválido en bloque '{b}'")

    return _ok("Dirección IPv4 válida")


# ══════════════════════════════════════════════════════════════════════════
# 8. MONTO MONETARIO
#    ER: "$" (" ")? N+ ("." N{3})* "," N+
#    Formato: $ 1.500,00  o  $1500,00
# ══════════════════════════════════════════════════════════════════════════

def validar_monto(cadena: str) -> dict:
    """
    Valida montos monetarios con separador de miles (.) y decimales (,).

    Transiciones:
        q0 --('$')--> q1
        q1 --(' ')--> q1   (espacio opcional)
        q1 --(D)-->   q2   (dígitos parte entera)
        q2 --(D)-->   q2   (self-loop)
        q2 --('.')--> q3   (separador de miles)
        q3 --(D)-->   q4   (3 dígitos de grupo)
        q4 --(D)-->   q5
        q5 --(D)-->   q2   (vuelve a aceptar miles)
        q2 --(',')-->  q6   (parte decimal)
        q6 --(D)-->   q7*
        q7 --(D)-->   q7   (self-loop)
    """
    if not cadena:
        return _err("Campo vacío")

    idx = 0
    n = len(cadena)

    # q0→q1: símbolo $
    if idx >= n or cadena[idx] != '$':
        return _err("Debe comenzar con el símbolo '$'")
    idx += 1

    # Espacio opcional
    if idx < n and cadena[idx] == ' ':
        idx += 1

    # Al menos un dígito
    if idx >= n or not _es_digito(cadena[idx]):
        return _err("Se esperaba un número tras '$'")

    # Leer dígitos enteros
    while idx < n and _es_digito(cadena[idx]):
        idx += 1

    # Separadores de miles: grupos de exactamente 3 dígitos
    while idx < n and cadena[idx] == '.':
        idx += 1
        grupo = 0
        while idx < n and _es_digito(cadena[idx]):
            idx += 1
            grupo += 1
        if grupo != 3:
            return _err(f"Los grupos de miles deben tener exactamente 3 dígitos, encontrados {grupo}")

    # Parte decimal obligatoria: ,XX
    if idx >= n or cadena[idx] != ',':
        return _err("Falta la coma decimal (ej. ,00)")
    idx += 1

    decimales = 0
    while idx < n and _es_digito(cadena[idx]):
        idx += 1
        decimales += 1

    if decimales < 1:
        return _err("Se esperaban dígitos decimales tras la coma")
    if idx < n:
        return _err(f"Carácter inesperado al final: '{cadena[idx]}'")

    return _ok("Monto monetario válido")


# ══════════════════════════════════════════════════════════════════════════
# 9. ETIQUETAS HTML/XML
#    ER: "<" ("/")? N ">"
# ══════════════════════════════════════════════════════════════════════════

def validar_html(cadena: str) -> dict:
    """
    Valida etiquetas HTML/XML de apertura <tag> y cierre </tag>.

    Transiciones:
        q0 --('<')-->   q1
        q1 --('/')-->   q2   (etiqueta de cierre)
        q1 --(alfa)-->  q3   (etiqueta de apertura)
        q2 --(alfa)-->  q3
        q3 --(alfanum)→ q3   (self-loop nombre)
        q3 --('>')-->   q4*
    """
    if not cadena:
        return _err("Campo vacío")

    estado = 0
    es_cierre = False

    for c in cadena:
        if estado == 0:
            if c == '<':
                estado = 1
            else:
                return _err(f"Debe comenzar con '<', encontrado '{c}'")

        elif estado == 1:
            if c == '/':
                es_cierre = True
                estado = 2
            elif _es_alfa(c):
                estado = 3
            else:
                return _err(f"Carácter inválido tras '<': '{c}'")

        elif estado == 2:
            if _es_alfa(c):
                estado = 3
            else:
                return _err(f"Se esperaba el nombre de etiqueta, encontrado '{c}'")

        elif estado == 3:
            if _es_alfanum(c) or c in ('_', '-'):
                pass  # se queda en q3
            elif c == '>':
                estado = 4
            else:
                return _err(f"Carácter inválido en nombre de etiqueta: '{c}'")

        elif estado == 4:
            return _err("Contenido extra tras el cierre '>'")

    if estado == 4:
        tipo = "cierre" if es_cierre else "apertura"
        return _ok(f"Etiqueta de {tipo} válida")
    if estado == 3:
        return _err("Falta el cierre '>'")
    return _err("Etiqueta incompleta")


# ══════════════════════════════════════════════════════════════════════════
# MOTOR DE BÚSQUEDA — extrae patrones de un texto libre
# ══════════════════════════════════════════════════════════════════════════

import re as _re  # Solo para tokenizar el texto (split), NO para validar patrones

def extraer_patrones(texto: str) -> dict:
    """
    Escanea un texto libre y extrae todas las coincidencias de cada patrón.
    Los autómatas son los que deciden si cada token es válido.
    El módulo 're' se usa ÚNICAMENTE para tokenizar y extraer patrones complejos.
    """
    if not texto or not texto.strip():
        return {k: [] for k in [
            "correos", "telefonos", "fechas", "identificadores",
            "urls", "placas", "ips", "montos", "etiquetas"
        ]}

    encontrados = {
        "correos":        [],
        "telefonos":      [],
        "fechas":         [],
        "identificadores":[],
        "urls":           [],
        "placas":         [],
        "ips":            [],
        "montos":         [],
        "etiquetas":      [],
    }

    # PASO 1: Extraer montos ANTES de dividir (porque contienen comas)
    # Patrón: $ (opcionalmente seguido de espacio) + dígitos + (puntos + 3 dígitos)* + coma + dígitos
    montos_pattern = r'\$\s*\d+(?:\.\d{3})*,\d+'
    for monto in _re.findall(montos_pattern, texto):
        if validar_monto(monto)["valido"]:
            encontrados["montos"].append(monto)
    
    # Remover los montos del texto para no procesarlos de nuevo
    texto_limpio = _re.sub(montos_pattern, '', texto)

    # PASO 2: Dividir el texto restante en tokens por espacios/saltos/comas/punto y coma
    tokens_raw = _re.split(r'[\s,;\n\r\t]+', texto_limpio)
    tokens = [t.strip() for t in tokens_raw if t.strip()]

    for token in tokens:
        # Correo: debe contener @
        if '@' in token and validar_correo(token)["valido"]:
            encontrados["correos"].append(token)

        # Teléfono: empieza con 3
        elif token and token[0] == '3' and validar_telefono(token)["valido"]:
            encontrados["telefonos"].append(token)

        # Fecha: tiene formato numérico con /
        if len(token) == 10 and token[2:3] == '/' and token[5:6] == '/':
            if validar_fecha(token)["valido"]:
                encontrados["fechas"].append(token)

        # Identificador: empieza con mayúscula
        if token and _es_mayuscula(token[0]) and not '@' in token:
            if validar_identificador(token)["valido"]:
                encontrados["identificadores"].append(token)

        # URL: empieza con http
        if token.startswith('http'):
            if validar_url(token)["valido"]:
                encontrados["urls"].append(token)

        # Placa: 7 caracteres con separador en pos 3
        if len(token) == 7 and token[3] in ('-', ' '):
            if validar_placa(token)["valido"]:
                encontrados["placas"].append(token)

        # IPv4: tiene 3 puntos entre dígitos
        if token.count('.') == 3 and token[0].isdigit():
            if validar_ipv4(token)["valido"]:
                encontrados["ips"].append(token)

        # HTML tag: empieza con <
        if token.startswith('<'):
            if validar_html(token)["valido"]:
                encontrados["etiquetas"].append(token)

    # Deduplicar manteniendo orden
    for clave in encontrados:
        visto = set()
        unicos = []
        for item in encontrados[clave]:
            if item not in visto:
                visto.add(item)
                unicos.append(item)
        encontrados[clave] = unicos

    return encontrados


# ── Mapa público: nombre → función validadora ──────────────────────────

VALIDADORES = {
    "correo":        validar_correo,
    "telefono":      validar_telefono,
    "fecha":         validar_fecha,
    "identificador": validar_identificador,
    "url":           validar_url,
    "placa":         validar_placa,
    "ipv4":          validar_ipv4,
    "monto":         validar_monto,
    "html":          validar_html,
}
