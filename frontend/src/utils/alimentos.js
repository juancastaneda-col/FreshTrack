import { colores } from '../theme/theme';

// Días que faltan para considerar un producto "por vencer".
export const DIAS_POR_VENCER = 5;

function normalizar(texto) {
  return String(texto || '')
    .toLowerCase()
    .replace(/[áàä]/g, 'a')
    .replace(/[éèë]/g, 'e')
    .replace(/[íìï]/g, 'i')
    .replace(/[óòö]/g, 'o')
    .replace(/[úùü]/g, 'u')
    .replace(/ñ/g, 'n');
}

// El orden importa: "papaya" debe revisarse antes que "papa".
const EMOJIS_ALIMENTO = [
  ['papaya', '🍈'], ['banano', '🍌'], ['banana', '🍌'], ['platano', '🍌'],
  ['manzana', '🍎'], ['pera', '🍐'], ['naranja', '🍊'], ['mandarina', '🍊'],
  ['limon', '🍋'], ['fresa', '🍓'], ['pina', '🍍'], ['mango', '🥭'],
  ['maracuya', '🥭'], ['uva', '🍇'], ['sandia', '🍉'], ['melon', '🍈'],
  ['durazno', '🍑'], ['cereza', '🍒'], ['kiwi', '🥝'], ['coco', '🥥'],
  ['mora', '🫐'], ['lulo', '🍊'], ['aguacate', '🥑'], ['tomate', '🍅'],
  ['pepino', '🥒'], ['cebolla', '🧅'], ['zanahoria', '🥕'], ['pimenton', '🫑'],
  ['brocoli', '🥦'], ['habichuela', '🥬'], ['lechuga', '🥬'], ['repollo', '🥬'],
  ['espinaca', '🥬'], ['cilantro', '🌿'], ['yuca', '🍠'], ['arracacha', '🥔'],
  ['papa', '🥔'], ['remolacha', '🟣'], ['mazorca', '🌽'], ['maiz', '🌽'],
  ['ajo', '🧄'], ['berenjena', '🍆'], ['champi', '🍄'],
];

export function emojiAlimento(nombre) {
  const n = normalizar(nombre);
  const hallado = EMOJIS_ALIMENTO.find(([clave]) => n.includes(clave));
  return hallado ? hallado[1] : '🥗';
}

const EMOJIS_RECETA = [
  ['batido', '🥤'], ['jugo', '🥤'], ['limonada', '🍋'], ['guacamole', '🥑'],
  ['pico de gallo', '🍅'], ['gazpacho', '🍅'], ['tostada', '🍞'], ['avena', '🥣'],
  ['parfait', '🍨'], ['bowl', '🥣'], ['salpicon', '🍉'], ['patacones', '🍌'],
  ['yuca', '🍠'], ['papas', '🥔'], ['pimentones', '🫑'], ['habichuelas', '🥬'],
  ['repollo', '🥬'], ['sancocho', '🍲'], ['sopa', '🍲'], ['crema', '🍲'],
  ['ensalada', '🥗'], ['salsa', '🌶️'], ['salteado', '🥘'],
];

export function emojiReceta(titulo) {
  const t = normalizar(titulo);
  const hallado = EMOJIS_RECETA.find(([clave]) => t.includes(clave));
  return hallado ? hallado[1] : '🍽️';
}

const FONDOS_RECETA = ['#FFE8CC', '#E3F6D2', '#FFE0E3', '#FFF3BF', '#DFF1FF', '#F1E4FF'];

export function colorReceta(id) {
  return FONDOS_RECETA[Math.abs(Number(id) || 0) % FONDOS_RECETA.length];
}

// Días hasta el vencimiento. 0 = vence hoy, negativo = ya venció.
export function diasParaVencer(fecha) {
  if (!fecha) return null;
  const [anio, mes, dia] = String(fecha).slice(0, 10).split('-').map(Number);
  if (!anio || !mes || !dia) return null;
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const vence = new Date(anio, mes - 1, dia);
  return Math.round((vence - hoy) / 86400000);
}

export function esPorVencer(dias) {
  return dias !== null && dias >= 0 && dias <= DIAS_POR_VENCER;
}

function textoDias(dias) {
  if (dias === 0) return 'Vence hoy';
  if (dias === 1) return 'Vence mañana';
  return `Vence en ${dias} días`;
}

export function estadoVencimiento(dias) {
  if (dias === null) {
    return { clave: 'sinfecha', color: '#9AA39B', texto: '#FFFFFF', etiqueta: 'Sin fecha' };
  }
  if (dias < 0) {
    const atras = Math.abs(dias);
    return {
      clave: 'vencido',
      color: colores.tomate,
      texto: '#FFFFFF',
      etiqueta: atras === 1 ? 'Venció ayer' : `Venció hace ${atras} días`,
    };
  }
  if (dias <= 2) {
    return { clave: 'urgente', color: '#E8590C', texto: '#FFFFFF', etiqueta: textoDias(dias) };
  }
  if (dias <= DIAS_POR_VENCER) {
    return { clave: 'pronto', color: colores.mango, texto: colores.selva, etiqueta: textoDias(dias) };
  }
  return { clave: 'fresco', color: colores.hoja, texto: '#FFFFFF', etiqueta: `Fresco · ${dias} días` };
}

// Parte el texto de preparación en pasos cortos y legibles.
export function pasosDeReceta(texto) {
  if (!texto) return [];
  const partes = String(texto).match(/[^.;!?]+[.;!?]*/g) || [String(texto)];
  return partes
    .map((p) => p.trim().replace(/[;]+$/, '').trim())
    .filter(Boolean)
    .map((p) => {
      const conMayuscula = p.charAt(0).toUpperCase() + p.slice(1);
      return /[.!?]$/.test(conMayuscula) ? conMayuscula : `${conMayuscula}.`;
    });
}