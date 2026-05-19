# TLF PatternEngine
**Búsqueda y Validación de Patrones en Textos y Sistemas Interactivos**

> Jean Kenneth Méndez Cuaran · Jhony Alexander Perea Perea · Santiago Orozco Zuluaga
> Teoría de Lenguajes Formales

---

## Estructura del proyecto

```
proyectoTLF/
├── app.py           # Servidor Flask — rutas y API REST
├── automatas.py     # 9 AFD implementados manualmente
├── requirements.txt # Dependencias Python
├── templates/
│   └── index.html   # Interfaz web (consume la API)
└── static/          # Archivos estáticos (vacío por ahora)
```

---

## Instalación y ejecución

### 1. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar el servidor
```bash
python app.py
```

Abre `http://localhost:5000` en tu navegador.

---

## API REST

| Método | Ruta              | Descripción                              |
|--------|-------------------|------------------------------------------|
| GET    | `/`               | Sirve la interfaz web                    |
| GET    | `/api/health`     | Estado del servidor                      |
| POST   | `/api/validar`    | Valida un campo individual               |
| POST   | `/api/extraer`    | Extrae patrones de un texto libre        |
| GET    | `/api/referencia` | Tabla de autómatas (ER + ejemplos)       |

### POST /api/validar
```json
// Request
{ "tipo": "correo", "valor": "profe@u.edu.co" }

// Response
{ "valido": true, "mensaje": "Correo electrónico válido" }
```

**Tipos disponibles:** `correo`, `telefono`, `fecha`, `identificador`, `url`, `placa`, `ipv4`, `monto`, `html`

### POST /api/extraer
```json
// Request
{ "texto": "Contactar a juan@mail.com o al 310-1234567 antes del 15/08/2025" }

// Response
{
  "patrones": {
    "correos": ["juan@mail.com"],
    "telefonos": ["310-1234567"],
    "fechas": ["15/08/2025"],
    ...
  },
  "total": 3
}
```

---

## Autómatas implementados

| # | Patrón              | ER                              | Ejemplo válido     |
|---|---------------------|---------------------------------|--------------------|
| 1 | Correo electrónico  | `(A\|S)⁺ @ D "." E`            | `profe@u.edu.co`   |
| 2 | Número telefónico   | `3 N N ("-")? N⁷`              | `310-1234567`      |
| 3 | Fecha DD/MM/AAAA    | `DD "/" MM "/" AAAA`            | `25/12/2024`       |
| 4 | Identificador       | `L⁺ D D D D D`                 | `ID12345`          |
| 5 | URL                 | `P s* "://" (S".")* D "." E`   | `https://google.com` |
| 6 | Placa vehicular     | `L L L "-" D D D`              | `AAA-123`          |
| 7 | IPv4                | `N "." N "." N "." N`          | `192.168.1.1`      |
| 8 | Monto monetario     | `"$" N⁺ ("." N{3})* "," N⁺`   | `$ 1.500,00`       |
| 9 | Etiqueta HTML/XML   | `"<" ("/")? N ">"`             | `<div>`, `</div>`  |

> **Nota:** Todos los autómatas están en `automatas.py` y usan
> diccionarios de transición de estados, **sin importar la librería `re`**
> para el proceso de validación.