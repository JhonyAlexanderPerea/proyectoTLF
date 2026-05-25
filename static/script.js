'use strict';

/* ── API helpers ──────────────────────────────────────────────────── */
const API = {
  base: '',  // mismo origen (Flask sirve el HTML)

  async post(ruta, cuerpo) {
    const res = await fetch(this.base + ruta, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  async get(ruta) {
    const res = await fetch(this.base + ruta);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
};

/* ── Escape HTML ─────────────────────────────────────────────────── */
function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/* ── Toast ───────────────────────────────────────────────────────── */
let toastTimer;
function showToast(msg, tipo = 'ok') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast toast-${tipo} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3500);
}

/* ── Health check ────────────────────────────────────────────────── */
async function checkHealth() {
  const dot = document.getElementById('server-dot');
  const label = document.getElementById('server-label');
  try {
    await API.get('/api/health');
    dot.className = 'server-dot online';
    label.textContent = 'Servidor activo';
  } catch {
    dot.className = 'server-dot offline';
    label.textContent = 'Sin conexión';
  }
}

checkHealth();
setInterval(checkHealth, 30000);

/* ── Tabs ────────────────────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'referencia') cargarReferencia();
  });
});

/* ════════════════════════════════════════════════════════════════════
   MÓDULO 1 — BÚSQUEDA
   ════════════════════════════════════════════════════════════════════ */

const LABELS = {
  correos: 'Correos Electrónicos',
  telefonos: 'Números Telefónicos',
  fechas: 'Fechas',
  identificadores: 'Identificadores / Códigos',
  urls: 'Direcciones URL',
  placas: 'Placas de Vehículos',
  ips: 'Direcciones IPv4',
  montos: 'Montos Monetarios',
  etiquetas: 'Etiquetas HTML/XML',
};

document.getElementById('btn-sample').addEventListener('click', () => {
  document.getElementById('txt-input').value = `Hola, te comparto mis datos de contacto:

Correo: juanperez@uniquindio.edu.co
Teléfono: 310-1234567
Fecha de nacimiento: 15/08/1998
Placa de mi carro: ABC-123
Código de estudiante: EST98765

Puedes visitar nuestra web en https://www.uniquindio.edu.co
También en http://portal.edu.co/inicio

El servidor tiene IP 192.168.0.1 y el router es 10.0.0.1

El pago total fue de $1.250.000,00 y el IVA es de $237.500,00

En el HTML usamos etiquetas como <div>, </div>, <span> y </span>`;
});

document.getElementById('btn-limpiar').addEventListener('click', () => {
  document.getElementById('txt-input').value = '';
  document.getElementById('results-container').innerHTML = '';
  limpiarArchivo();
});

/* ── Variable global para archivo seleccionado ─────────────────────── */
let selectedFile = null;

/* ── Render resultados (compartido entre texto y archivo) ─────────── */
function renderResultados(patrones, container) {
  const total = Object.values(patrones).reduce((s, arr) => s + arr.length, 0);
  if (total === 0) {
    container.innerHTML = '<p class="no-results">No se encontraron patrones reconocibles.</p>';
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'results-grid';

  for (const [clave, items] of Object.entries(patrones)) {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
      <div class="r-type">${LABELS[clave] || clave}</div>
      <div class="r-count">${items.length} coincidencia(s)</div>
      <div class="r-items">
        ${items.length
          ? items.map(it => `<div class="r-item">${esc(it)}</div>`).join('')
          : '<div style="font-size:.75rem;color:var(--muted);font-style:italic">Sin coincidencias</div>'}
      </div>`;
    grid.appendChild(card);
  }
  container.appendChild(grid);
  return total;
}

/* ── Botón Extraer: texto del textarea O archivo seleccionado ─────── */
document.getElementById('btn-extraer').addEventListener('click', async () => {
  const container = document.getElementById('results-container');
  const spinner = document.getElementById('sp-extraer');

  if (selectedFile) {
    /* ── Extraer desde archivo ─────────────────────────────────── */
    spinner.classList.add('active');
    container.innerHTML = '';

    try {
      const formData = new FormData();
      formData.append('archivo', selectedFile);

      const res = await fetch('/api/procesar-archivo', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.error || 'Error desconocido');
      }

      const data = await res.json();
      const { archivo: nombre, patrones } = data;
      const total = renderResultados(patrones, container);
      showToast(`${nombre}: ${total} patrón(es) encontrado(s)`, 'ok');

    } catch (err) {
      showToast(`Error: ${err.message}`, 'err');
      container.innerHTML = '<p class="no-results">Error al procesar el archivo.</p>';
    } finally {
      spinner.classList.remove('active');
    }

  } else {
    /* ── Extraer desde texto ───────────────────────────────────── */
    const texto = document.getElementById('txt-input').value;

    if (!texto.trim()) {
      showToast('Ingresa texto o selecciona un archivo', 'err');
      return;
    }

    spinner.classList.add('active');
    container.innerHTML = '';

    try {
      const data = await API.post('/api/extraer', { texto });
      const { patrones, total } = data;
      renderResultados(patrones, container);
      showToast(`${total} patrón(es) encontrado(s)`, 'ok');

    } catch (err) {
      showToast('Error al conectar con el servidor', 'err');
      container.innerHTML = '<p class="no-results">Error de conexión con el servidor.</p>';
    } finally {
      spinner.classList.remove('active');
    }
  }
});

document.getElementById('btn-limpiar').addEventListener('click', () => {
  document.getElementById('txt-input').value = '';
  document.getElementById('results-container').innerHTML = '';
  limpiarArchivo();
});

/* ── Drag and Drop para archivos ──────────────────────────────────── */
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

function mostrarArchivoEnZona(archivo) {
  document.getElementById('drop-empty').style.display = 'none';
  document.getElementById('drop-file-info').style.display = 'block';
  document.getElementById('file-name-display').textContent = archivo.name;
  document.getElementById('file-size-display').textContent = formatSize(archivo.size);
}

function limpiarArchivo() {
  selectedFile = null;
  fileInput.value = '';
  document.getElementById('drop-empty').style.display = 'block';
  document.getElementById('drop-file-info').style.display = 'none';
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function validarArchivo(archivo) {
  const ext = archivo.name.split('.').pop().toLowerCase();
  if (!['pdf', 'docx'].includes(ext)) {
    showToast('Solo se permiten archivos PDF o DOCX', 'err');
    return false;
  }
  if (archivo.size > 16 * 1024 * 1024) {
    showToast('El archivo es demasiado grande (máx 16 MB)', 'err');
    return false;
  }
  return true;
}

function seleccionarArchivo(archivo) {
  if (!validarArchivo(archivo)) return;
  selectedFile = archivo;
  mostrarArchivoEnZona(archivo);
  showToast(`Archivo listo: ${archivo.name}`, 'ok');
}

dropZone.addEventListener('click', (e) => {
  if (e.target.closest('.file-remove-btn')) return;
  fileInput.click();
});

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
  dropZone.addEventListener(evt, e => e.preventDefault());
  document.body.addEventListener(evt, e => e.preventDefault());
});

dropZone.addEventListener('dragenter', () => dropZone.classList.add('dragover'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));

dropZone.addEventListener('drop', e => {
  dropZone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0) seleccionarArchivo(files[0]);
});

fileInput.addEventListener('change', e => {
  if (e.target.files.length > 0) seleccionarArchivo(e.target.files[0]);
});

document.getElementById('file-remove-btn').addEventListener('click', (e) => {
  e.stopPropagation();
  limpiarArchivo();
});

/* ════════════════════════════════════════════════════════════════════
   MÓDULO 2 — FORMULARIO CON VALIDACIÓN VÍA API
   ════════════════════════════════════════════════════════════════════ */

const CAMPOS = [
  { id: 'f-correo', tipo: 'correo', msg: 'msg-correo', pill: 'Correo' },
  { id: 'f-telefono', tipo: 'telefono', msg: 'msg-telefono', pill: 'Teléfono' },
  { id: 'f-fecha', tipo: 'fecha', msg: 'msg-fecha', pill: 'Fecha' },
  { id: 'f-url', tipo: 'url', msg: 'msg-url', pill: 'URL' },
  { id: 'f-placa', tipo: 'placa', msg: 'msg-placa', pill: 'Placa' },
  { id: 'f-id', tipo: 'identificador', msg: 'msg-id', pill: 'ID' },
  { id: 'f-ipv4', tipo: 'ipv4', msg: 'msg-ipv4', pill: 'IPv4' },
  { id: 'f-monto', tipo: 'monto', msg: 'msg-monto', pill: 'Monto' },
];

/* Inicializar pills */
const pillsContainer = document.getElementById('pills-container');
CAMPOS.forEach(cfg => {
  const pill = document.createElement('span');
  pill.className = 'pill idle';
  pill.id = 'pill-' + cfg.id;
  pill.textContent = cfg.pill;
  pillsContainer.appendChild(pill);
});

function setPill(fieldId, estado) {
  const p = document.getElementById('pill-' + fieldId);
  if (p) p.className = 'pill ' + estado;
}

/* Debounce para no llamar al servidor en cada tecla */
function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/* Aplica resultado de validación al campo */
function aplicarResultado(fieldId, msgId, resultado) {
  const input = document.getElementById(fieldId);
  const msgEl = document.getElementById(msgId);
  const { valido, mensaje } = resultado;

  input.classList.toggle('valid', valido);
  input.classList.toggle('invalid', !valido);
  msgEl.textContent = (valido ? '✓ ' : '✕ ') + mensaje;
  msgEl.className = 'field-msg ' + (valido ? 'ok' : 'err');
  setPill(fieldId, valido ? 'ok' : 'err');
}

function limpiarCampo(fieldId, msgId) {
  const input = document.getElementById(fieldId);
  const msgEl = document.getElementById(msgId);
  input.classList.remove('valid', 'invalid');
  msgEl.textContent = '';
  msgEl.className = 'field-msg';
  setPill(fieldId, 'idle');
}

CAMPOS.forEach(cfg => {
  const input = document.getElementById(cfg.id);
  if (!input) return;

  const validar = debounce(async (valor) => {
    if (!valor) {
      limpiarCampo(cfg.id, cfg.msg);
      return;
    }

    // Llamada al servidor
    try {
      const resultado = await API.post('/api/validar', { tipo: cfg.tipo, valor });
      aplicarResultado(cfg.id, cfg.msg, resultado);
    } catch {
      const msgEl = document.getElementById(cfg.msg);
      msgEl.textContent = '⚠ Sin conexión al servidor';
      msgEl.className = 'field-msg err';
    }
  }, 350);  // 350 ms de debounce

  input.addEventListener('input', e => validar(e.target.value));
});

document.getElementById('btn-sample-form').addEventListener('click', () => {
  const ejemplos = {
    'f-correo': 'maria.garcia@uniquindio.edu.co',
    'f-telefono': '310-1234567',
    'f-fecha': '25/12/2024',
    'f-url': 'https://www.uniquindio.edu.co',
    'f-placa': 'ABC-123',
    'f-id': 'EST98765',
    'f-ipv4': '192.168.1.1',
    'f-monto': '$ 1.500,00',
  };

  for (const [id, valor] of Object.entries(ejemplos)) {
    const input = document.getElementById(id);
    if (input) {
      input.value = valor;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
  showToast('Formulario de ejemplo cargado', 'ok');
});

/* ════════════════════════════════════════════════════════════════════
   MÓDULO 3 — REFERENCIA (carga desde /api/referencia)
   ════════════════════════════════════════════════════════════════════ */

let referenciasCargadas = false;

async function cargarReferencia() {
  if (referenciasCargadas) return;
  const grid = document.getElementById('ref-grid');

  try {
    const datos = await API.get('/api/referencia');
    grid.innerHTML = '';
    datos.forEach(a => {
      const el = document.createElement('div');
      el.className = 'ref-item';
      el.innerHTML = `
        <div class="ri-name">${esc(a.nombre)}</div>
        <div class="ri-er">${esc(a.er)}</div>
        <div class="ri-ex">✓ <span>${esc(a.valido)}</span></div>
        <div class="ri-ex" style="color:var(--bad)">✕ <span style="color:var(--muted)">${esc(a.invalido)}</span></div>
        <div class="ri-states">${esc(a.estados)}</div>`;
      grid.appendChild(el);
    });
    referenciasCargadas = true;
  } catch {
    grid.innerHTML = '<div class="no-results">Error al cargar desde el servidor.</div>';
  }
}
