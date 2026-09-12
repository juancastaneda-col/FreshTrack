"""
Paginas HTML de prueba para validar el backend desde el navegador o el celular.

NO forma parte del contrato de la API. El frontend real (app movil o SPA)
reemplaza estas paginas y consume directamente los endpoints /api/v1/*.
Sirvieron para validar el flujo end-to-end (auth, escaneo OCR, confirmacion,
agregar manual, inventario) mientras el frontend estaba en construccion.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(include_in_schema=False)


@router.get("/registro", response_class=HTMLResponse)
def pagina_registro():
  """Formulario independiente para crear una cuenta."""
  return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FreshTrack — Crear cuenta</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 20px;
           background: #f5f6f8; color: #1a1a1a; }
    h1 { font-size: 20px; }
    .caja { max-width: 480px; background: #fff; border-radius: 12px; padding: 16px;
            margin: 0 auto 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    button { width: 100%; padding: 14px; font-size: 16px; border: 0;
             border-radius: 10px; background: #1a4fd6; color: #fff; }
    button:disabled { background: #9aa5b8; }
    label { display: block; font-size: 13px; margin: 10px 0 4px; }
    input { box-sizing: border-box; width: 100%; padding: 12px;
            border: 1px solid #c8ceda; border-radius: 8px; font-size: 16px; }
    .secundario { display: block; box-sizing: border-box; background: #e5e9f2;
                  color: #1a1a1a; margin-top: 8px; text-align: center;
                  text-decoration: none; }
    .error { color: #b3261e; margin-top: 10px; }
  </style>
</head>
<body>
  <div class="caja">
    <h1>FreshTrack</h1>
    <h2>Crear cuenta</h2>
    <label for="correo">Correo electronico</label>
    <input type="email" id="correo" autocomplete="email" required>
    <label for="password">Contrasena</label>
    <input type="password" id="password" minlength="8" autocomplete="new-password" required>
    <button id="crear">Crear cuenta</button>
    <a class="secundario" href="/">Volver a iniciar sesion</a>
    <div class="error" id="error-registro" role="alert"></div>
  </div>

<script>
const botonCrear = document.getElementById('crear');
const errorRegistro = document.getElementById('error-registro');

botonCrear.onclick = async () => {
  errorRegistro.textContent = '';
  botonCrear.disabled = true;
  try {
    const respuesta = await fetch('/api/v1/auth/registro', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({correo: document.getElementById('correo').value,
                            password: document.getElementById('password').value})
    });
    const json = await respuesta.json();
    if (!respuesta.ok) throw new Error(json.detail || 'No fue posible crear la cuenta');
    window.location.href = '/';
  } catch (error) {
    errorRegistro.textContent = error.message;
    botonCrear.disabled = false;
  }
};
</script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def pagina_prueba():
    """Pagina minima para probar el escaneo desde el celular."""
    return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FreshTrack — Mi inventario</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 20px;
           background: #f5f6f8; color: #1a1a1a; }
    h1 { font-size: 20px; }
    .caja { background: #fff; border-radius: 12px; padding: 16px;
            margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    button { width: 100%; padding: 14px; font-size: 16px; border: 0;
             border-radius: 10px; background: #1a4fd6; color: #fff; }
    button:disabled { background: #9aa5b8; }
    input[type=file] { width: 100%; margin-bottom: 12px; }
    .item { border-bottom: 1px solid #eee; padding: 10px 0; }
    .item:last-child { border-bottom: 0; }
    .nombre { font-weight: 600; }
    .crudo { color: #777; font-size: 12px; }
    .conf { font-size: 12px; }
    .alta { color: #1a7f37; } .baja { color: #b35c00; } .nula { color: #b3261e; }
    .fila { display: grid; grid-template-columns: 1fr 90px 90px; gap: 8px; align-items: center; margin: 8px 0; }
    .fila input, .fila select { min-width: 0; padding: 9px; border: 1px solid #c8ceda; border-radius: 6px; }
    .fila button { padding: 9px; font-size: 13px; }
    .acciones { display: flex; gap: 8px; margin-top: 12px; }
    .acciones button { flex: 1; }
    .aviso { background: #fff4e5; border-left: 4px solid #e08b00;
             padding: 10px; border-radius: 6px; margin-bottom: 12px; }
    #resultados-catalogo { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    #resultados-catalogo .resultado { width: auto; padding: 8px 12px; font-size: 14px; }
    #formulario-manual { margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee; }
    #producto-seleccionado { font-weight: 600; color: #1a1a1a; margin-bottom: 6px; }
    .fuera-catalogo { background: #fff4e5; border-left: 3px solid #e08b00;
             padding: 6px 8px; border-radius: 4px; margin-top: 6px;
             font-size: 12px; grid-column: 1 / -1; }
    .fuera-catalogo label { display: inline; margin-left: 6px; font-size: 12px; }
    .item.excluido { opacity: 0.55; }
    .oculto { display: none; }
    .error { color: #b3261e; margin-top: 10px; }
    .secundario { background: #e5e9f2; color: #1a1a1a; margin-top: 8px; }
    label { display: block; font-size: 13px; margin: 10px 0 4px; }
    input[type=email], input[type=password] { box-sizing: border-box; width: 100%;
      padding: 12px; border: 1px solid #c8ceda; border-radius: 8px; font-size: 16px; }
  </style>
</head>
<body>
  <h1>FreshTrack</h1>

  <div class="caja" id="acceso">
    <h2>Tu inventario, solo tuyo</h2>
    <label for="correo">Correo electronico</label>
    <input type="email" id="correo" autocomplete="email">
    <label for="password">Contrasena</label>
    <input type="password" id="password" minlength="8" autocomplete="current-password">
    <button id="iniciar">Iniciar sesion</button>
    <button class="secundario" id="registrar">Crear cuenta</button>
    <div class="error" id="error-acceso" role="alert"></div>
  </div>

  <div class="caja oculto" id="cuenta">
    <b id="usuario"></b>
    <button class="secundario" id="salir">Cerrar sesion</button>
  </div>

  <div class="caja oculto" id="escaneo">
    <h2>Escanear factura</h2>
    <input type="file" id="archivo" accept="image/*">
    <button id="enviar">Procesar factura</button>
  </div>

  <div class="caja oculto" id="agregar-manual">
    <h2>Agregar producto</h2>
    <label for="buscar-catalogo">Buscar en el catalogo</label>
    <input type="text" id="buscar-catalogo" autocomplete="off" placeholder="Ej: tomate">
    <div id="resultados-catalogo"></div>
    <div id="formulario-manual" class="oculto">
      <div id="producto-seleccionado" class="crudo"></div>
      <label for="cantidad-manual">Cantidad</label>
      <input type="number" id="cantidad-manual" min="0.001" step="0.001" value="1">
      <label for="unidad-manual">Unidad</label>
      <select id="unidad-manual">
        <option value="UND">Unidad</option>
        <option value="KG">Kilogramo</option>
        <option value="G">Gramo</option>
        <option value="LB">Libra</option>
        <option value="MANOJO">Manojo</option>
      </select>
      <label for="condicion-manual">Ubicacion</label>
      <select id="condicion-manual">
        <option value="fuera">Fuera de nevera</option>
        <option value="nevera">Nevera</option>
      </select>
      <button id="guardar-manual">Guardar en inventario</button>
      <button id="cancelar-manual" class="secundario" type="button">Cancelar</button>
      <div id="mensaje-manual"></div>
    </div>
  </div>

  <div id="salida"></div>

  <div class="caja oculto" id="inventario">
    <h2>Mi inventario</h2>
    <div id="lista-inventario">Cargando...</div>
  </div>

<script>
const boton = document.getElementById('enviar');
const entrada = document.getElementById('archivo');
const salida = document.getElementById('salida');
const acceso = document.getElementById('acceso');
const cuenta = document.getElementById('cuenta');
const escaneo = document.getElementById('escaneo');
const errorAcceso = document.getElementById('error-acceso');

async function autenticar(ruta) {
  errorAcceso.textContent = '';
  const respuesta = await fetch(ruta, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({correo: document.getElementById('correo').value,
                          password: document.getElementById('password').value})
  });
  const json = await respuesta.json();
  if (!respuesta.ok) throw new Error(json.detail || 'No fue posible autenticarte');
  mostrarSesion(json.correo);
}

function mostrarSesion(correo) {
  acceso.classList.add('oculto');
  cuenta.classList.remove('oculto');
  escaneo.classList.remove('oculto');
  document.getElementById('agregar-manual').classList.remove('oculto');
  document.getElementById('inventario').classList.remove('oculto');
  document.getElementById('usuario').textContent = correo;
  cargarInventario();
}

async function cargarInventario() {
  const contenedor = document.getElementById('lista-inventario');
  try {
    const respuesta = await fetch('/api/v1/inventario');
    if (!respuesta.ok) { contenedor.textContent = 'No se pudo cargar el inventario'; return; }
    const json = await respuesta.json();
    if (!json.items.length) { contenedor.textContent = 'Aun no tienes productos guardados.'; return; }
    contenedor.innerHTML = json.items.map(item =>
      '<div class="item"><span class="nombre">' + item.nombre + '</span> &middot; ' +
      item.cantidad + ' ' + item.unidad +
      ' <span class="crudo">(' + (item.condicion === 'nevera' ? 'nevera' : 'fuera de nevera') + ')</span></div>'
    ).join('');
  } catch (e) {
    contenedor.textContent = 'Error de conexion: ' + e.message;
  }
}

const buscador = document.getElementById('buscar-catalogo');
const resultadosCatalogo = document.getElementById('resultados-catalogo');
const formularioManual = document.getElementById('formulario-manual');
const mensajeManual = document.getElementById('mensaje-manual');
let alimentoSeleccionado = null;
let temporizadorBusqueda = null;

function mostrarFormularioProducto(alimento) {
  alimentoSeleccionado = alimento;
  const etiqueta = alimento.id_alimento
    ? alimento.nombre
    : alimento.nombre + ' (fuera del catalogo)';
  document.getElementById('producto-seleccionado').textContent = 'Producto: ' + etiqueta;
  formularioManual.classList.remove('oculto');
  resultadosCatalogo.innerHTML = '';
  buscador.value = '';
  mensajeManual.textContent = '';
}

async function ejecutarBusqueda() {
  const q = buscador.value.trim();
  if (q.length < 2) { resultadosCatalogo.innerHTML = ''; return; }
  const respuesta = await fetch('/api/v1/catalogo?q=' + encodeURIComponent(q));
  if (!respuesta.ok) { resultadosCatalogo.innerHTML = ''; return; }
  const json = await respuesta.json();
  if (!json.resultados.length) {
    resultadosCatalogo.innerHTML =
      '<div class="aviso">No se encontro en el catalogo. Puedes agregarlo igual, ' +
      'pero no se calculara fecha de vencimiento.</div>' +
      '<button id="agregar-libre" class="secundario" type="button">' +
      'Agregar "' + q.replace(/"/g, '&quot;') + '" sin catalogo</button>';
    document.getElementById('agregar-libre').onclick = () =>
      mostrarFormularioProducto({id_alimento: null, nombre: q});
    return;
  }
  resultadosCatalogo.innerHTML = json.resultados.map(r =>
    '<button type="button" class="secundario resultado" data-id="' + r.id_alimento +
    '" data-nombre="' + r.nombre.replace(/"/g, '&quot;') + '">' + r.nombre + '</button>'
  ).join('');
  document.querySelectorAll('.resultado').forEach(btn => btn.onclick = () =>
    mostrarFormularioProducto({id_alimento: Number(btn.dataset.id), nombre: btn.dataset.nombre})
  );
}

buscador.oninput = () => {
  clearTimeout(temporizadorBusqueda);
  temporizadorBusqueda = setTimeout(ejecutarBusqueda, 200);
};

document.getElementById('cancelar-manual').onclick = () => {
  formularioManual.classList.add('oculto');
  alimentoSeleccionado = null;
  mensajeManual.textContent = '';
};

document.getElementById('guardar-manual').onclick = async () => {
  if (!alimentoSeleccionado) return;
  mensajeManual.textContent = '';
  const respuesta = await fetch('/api/v1/inventario', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      id_alimento: alimentoSeleccionado.id_alimento,
      nombre: alimentoSeleccionado.nombre,
      cantidad: Number(document.getElementById('cantidad-manual').value),
      unidad: document.getElementById('unidad-manual').value,
      condicion: document.getElementById('condicion-manual').value
    })
  });
  const json = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    mensajeManual.textContent = 'Error: ' + (json.detail || 'no se pudo agregar');
    return;
  }
  let msg = 'Producto agregado al inventario';
  if (json.fecha_vencimiento_est) msg += '. Vence el ' + json.fecha_vencimiento_est;
  if (json.aviso) msg += '. ' + json.aviso;
  mensajeManual.textContent = msg;
  formularioManual.classList.add('oculto');
  alimentoSeleccionado = null;
  cargarInventario();
};

document.getElementById('iniciar').onclick = () => autenticar('/api/v1/auth/login')
  .catch(error => errorAcceso.textContent = error.message);
document.getElementById('registrar').onclick = () => window.location.href = '/registro';
document.getElementById('salir').onclick = async () => {
  await fetch('/api/v1/auth/logout', {method: 'POST'});
  window.location.reload();
};

fetch('/api/v1/auth/me').then(respuesta => {
  if (respuesta.ok) return respuesta.json();
  throw new Error();
}).then(usuario => mostrarSesion(usuario.correo)).catch(() => {});

boton.onclick = async () => {
  if (!entrada.files.length) { alert('Seleccione una foto primero'); return; }

  boton.disabled = true;
  boton.textContent = 'Procesando...';
  salida.innerHTML = '';

  const datos = new FormData();
  datos.append('archivo', entrada.files[0]);

  try {
    const respuesta = await fetch('/api/v1/facturas/escanear', {
      method: 'POST', body: datos
    });
    const json = await respuesta.json();

    if (!respuesta.ok) {
      salida.innerHTML = '<div class="caja">Error: ' + (json.detail || 'desconocido') + '</div>';
      return;
    }

    const escaneo = await (await fetch('/api/v1/escaneos/' + json.id_escaneo)).json();
    renderizarEscaneo(json, escaneo.lineas);

  } catch (e) {
    salida.innerHTML = '<div class="caja">Error de conexion: ' + e.message + '</div>';
  } finally {
    boton.disabled = false;
    boton.textContent = 'Procesar factura';
  }
};

function renderizarEscaneo(resumen, lineas) {
  let html = '';
  if (resumen.advertencia) html += '<div class="aviso">' + resumen.advertencia + '</div>';
  html += '<div class="caja"><b>Revisa tus productos</b> &middot; confianza OCR ' +
          (resumen.confianza_ocr * 100).toFixed(0) + '% &middot; ' + resumen.segundos + 's</div>';
  html += '<div class="caja"><div id="lineas">';
  for (const linea of lineas) {
    const clase = linea.confianza >= 0.85 ? 'alta' : (linea.confianza >= 0.55 ? 'baja' : 'nula');
    const fueraCatalogo = linea.en_catalogo === false;
    const claseItem = fueraCatalogo ? 'item fila excluido' : 'item fila';
    html += '<div class="' + claseItem + '" data-linea="' + linea.id_linea + '" data-unidad="' + linea.unidad + '" data-catalogo="' + (linea.en_catalogo ? '1' : '0') + '">' +
      '<input class="nombre" value="' + linea.nombre.replace(/"/g, '&quot;') + '">' +
      '<input class="cantidad" type="number" min="0.001" step="0.001" value="' + linea.cantidad + '">' +
      '<select class="condicion"><option value="fuera" ' + (linea.condicion === 'fuera' ? 'selected' : '') + '>Fuera</option>' +
      '<option value="nevera" ' + (linea.condicion === 'nevera' ? 'selected' : '') + '>Nevera</option></select>' +
      '<button class="eliminar" type="button">Eliminar</button>' +
      (fueraCatalogo
        ? '<div class="fuera-catalogo">No es fruta ni verdura del catalogo. <label><input type="checkbox" class="incluir"> Incluir de todos modos</label></div>'
        : '') +
      '<div class="crudo">Detectado: ' + linea.texto_crudo + ' &middot; ' +
      '<span class="conf ' + clase + '">' + (linea.confianza * 100).toFixed(0) + '%</span></div></div>';
  }
  html += '</div><button id="agregar" class="secundario" type="button">Agregar producto</button>' +
          '<button id="confirmar" type="button">Confirmar productos</button><div id="mensaje"></div></div>';
  salida.innerHTML = html;
  const idEscaneo = resumen.id_escaneo;
  document.querySelectorAll('.eliminar').forEach(boton => boton.onclick = async () => {
    const fila = boton.closest('[data-linea]');
    await fetch('/api/v1/escaneos/' + idEscaneo + '/lineas/' + fila.dataset.linea, {method: 'DELETE'});
    fila.remove();
  });
  document.querySelectorAll('.incluir').forEach(cb => cb.onchange = () => {
    cb.closest('[data-linea]').classList.toggle('excluido', !cb.checked);
  });
  document.getElementById('agregar').onclick = async () => {
    const respuesta = await fetch('/api/v1/escaneos/' + idEscaneo + '/lineas', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({nombre: 'Nuevo producto', cantidad: 1, unidad: 'UND', condicion: 'fuera'})
    });
    if (respuesta.ok) { const actualizado = await (await fetch('/api/v1/escaneos/' + idEscaneo)).json(); renderizarEscaneo(resumen, actualizado.lineas); }
  };
  document.getElementById('confirmar').onclick = async () => {
    const filasExcluidas = [...document.querySelectorAll('[data-catalogo="0"]')].filter(fila => {
      const cb = fila.querySelector('.incluir');
      return !cb || !cb.checked;
    });
    for (const fila of filasExcluidas) {
      await fetch('/api/v1/escaneos/' + idEscaneo + '/lineas/' + fila.dataset.linea, {method: 'DELETE'});
      fila.remove();
    }
    const lineasActuales = [...document.querySelectorAll('[data-linea]')].map(fila => ({
      nombre: fila.querySelector('.nombre').value, cantidad: Number(fila.querySelector('.cantidad').value),
      unidad: fila.dataset.unidad || 'UND', condicion: fila.querySelector('.condicion').value
    }));
    if (!lineasActuales.length) {
      document.getElementById('mensaje').textContent = 'No hay productos para agregar al inventario';
      return;
    }
    const respuesta = await fetch('/api/v1/escaneos/' + idEscaneo + '/confirmar', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({lineas: lineasActuales})
    });
    const json = await respuesta.json().catch(() => ({}));
    document.getElementById('mensaje').textContent = respuesta.ok
      ? ('Se agregaron ' + (json.items_creados || lineasActuales.length) + ' productos a tu inventario')
      : 'No se pudieron confirmar los productos';
    if (respuesta.ok) cargarInventario();
  };
}
</script>
</body>
</html>
"""
