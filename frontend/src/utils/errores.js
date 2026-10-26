export function mensajeDeError(error) {
  if (!error || !error.response) {
    return 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.';
  }
  const detalle = error.response.data?.detail;
  if (Array.isArray(detalle)) return detalle.map((d) => d.msg).join(' · ');
  if (typeof detalle === 'string') return detalle;
  return `Error ${error.response.status}. Intenta de nuevo.`;
}