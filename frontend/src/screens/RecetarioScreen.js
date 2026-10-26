import { useState, useCallback, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, ActivityIndicator, Platform } from 'react-native';
import { Button, Searchbar, Snackbar } from 'react-native-paper';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../services/api';
import { colores, fuentes, sombras } from '../theme/theme';
import {
  DIAS_POR_VENCER,
  diasParaVencer,
  esPorVencer,
  estadoVencimiento,
  emojiAlimento,
  emojiReceta,
  colorReceta,
  pasosDeReceta,
} from '../utils/alimentos';
import { mensajeDeError } from '../utils/errores';

function totalIngredientes(receta) {
  return (receta.ingredientes || []).length;
}

function tengoIngredientes(receta) {
  return Math.max(totalIngredientes(receta) - (receta.faltantes || []).length, 0);
}

function TarjetaReceta({ receta, onPress }) {
  const total = totalIngredientes(receta);
  const tengo = tengoIngredientes(receta);
  const porcentaje = Math.round((receta.cobertura || 0) * 100);
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.tarjeta, pressed && { opacity: 0.85 }]}
      accessibilityRole="button"
      accessibilityLabel={`Ver receta ${receta.titulo}`}
    >
      <View style={[styles.tarjetaEmoji, { backgroundColor: colorReceta(receta.id_receta) }]}>
        <Text style={styles.tarjetaEmojiTexto}>{emojiReceta(receta.titulo)}</Text>
      </View>
      <View style={styles.tarjetaInfo}>
        <Text style={styles.tarjetaTitulo} numberOfLines={2}>{receta.titulo}</Text>
        <Text style={styles.tarjetaMeta}>
          ⏱ {receta.minutos_prep} min · 🍽 {receta.porciones} {receta.porciones === 1 ? 'porción' : 'porciones'}
        </Text>

        <View style={styles.barraFondo}>
          <View
            style={[
              styles.barraRelleno,
              { width: `${porcentaje}%`, backgroundColor: porcentaje === 100 ? colores.hoja : colores.mango },
            ]}
          />
        </View>
        <Text style={styles.tarjetaCobertura}>
          {porcentaje === 100 ? '¡Tienes todo!' : `Tienes ${tengo} de ${total} ingredientes`}
        </Text>

        {receta.urgentes > 0 && (
          <View style={styles.etiquetaUrgente}>
            <Text style={styles.etiquetaUrgenteTexto}>
              🔥 Usa {receta.urgentes} que {receta.urgentes === 1 ? 'vence' : 'vencen'} pronto
            </Text>
          </View>
        )}
      </View>
    </Pressable>
  );
}

function DetalleReceta({ receta, idsPorVencer, onVolver, onAccion, accionando }) {
  const ingredientes = receta.ingredientes || [];
  const faltantes = receta.faltantes || [];
  const ids = receta.ingrediente_ids || [];
  const alineados = ids.length === ingredientes.length;
  const pasos = pasosDeReceta(receta.pasos);

  return (
    <View>
      <Button
        icon="arrow-left"
        mode="text"
        onPress={onVolver}
        textColor={colores.hoja}
        style={styles.volver}
        labelStyle={styles.botonEtiqueta}
      >
        Todas las recetas
      </Button>

      <View style={[styles.detalleHero, { backgroundColor: colorReceta(receta.id_receta) }]}>
        <Text style={styles.detalleEmoji}>{emojiReceta(receta.titulo)}</Text>
        <Text style={styles.detalleTitulo}>{receta.titulo}</Text>
        <View style={styles.detalleMetas}>
          <Text style={styles.detalleMeta}>⏱ {receta.minutos_prep} min</Text>
          <Text style={styles.detalleMeta}>🍽 {receta.porciones} {receta.porciones === 1 ? 'porción' : 'porciones'}</Text>
        </View>
      </View>

      <Text style={styles.seccion}>🧺 Ingredientes</Text>
      <View style={styles.caja}>
        {ingredientes.map((nombre, i) => {
          const falta = faltantes.includes(nombre);
          const urgente = alineados && !falta && idsPorVencer.has(ids[i]);
          return (
            <View key={`${nombre}-${i}`} style={styles.ingrediente}>
              <Text style={styles.ingredienteIcono}>{falta ? '🛒' : '✅'}</Text>
              <Text style={[styles.ingredienteNombre, falta && styles.ingredienteFalta]}>
                {emojiAlimento(nombre)} {nombre}
              </Text>
              {urgente && (
                <View style={[styles.etiquetaUrgente, { marginTop: 0, marginLeft: 8 }]}>
                  <Text style={styles.etiquetaUrgenteTexto}>vence pronto</Text>
                </View>
              )}
              {falta && <Text style={styles.ingredienteNota}>te falta</Text>}
            </View>
          );
        })}
      </View>

      <Text style={styles.seccion}>👩‍🍳 Preparación</Text>
      <View style={styles.caja}>
        {pasos.map((paso, i) => (
          <View key={i} style={styles.paso}>
            <View style={styles.pasoNumero}>
              <Text style={styles.pasoNumeroTexto}>{i + 1}</Text>
            </View>
            <Text style={styles.pasoTexto}>{paso}</Text>
          </View>
        ))}
      </View>

      <Button
        mode="contained"
        icon="chef-hat"
        onPress={() => onAccion(receta, 'usada')}
        disabled={accionando}
        loading={accionando}
        style={styles.botonPrincipal}
        contentStyle={{ height: 50 }}
        labelStyle={styles.botonEtiquetaGrande}
      >
        ¡Ya la cociné!
      </Button>
      <Button
        mode="outlined"
        onPress={() => onAccion(receta, 'descartada')}
        disabled={accionando}
        textColor={colores.suave}
        style={styles.botonSecundario}
        labelStyle={styles.botonEtiqueta}
      >
        No me interesa esta receta
      </Button>
    </View>
  );
}

export default function RecetarioScreen({ navigation, route }) {
  const scrollRef = useRef(null);
  const [items, setItems] = useState([]);
  const [recetas, setRecetas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [busqueda, setBusqueda] = useState('');
  const [filtro, setFiltro] = useState(null); // { id, nombre } del producto elegido
  const [seleccionada, setSeleccionada] = useState(null);
  const [ocultas, setOcultas] = useState([]);
  const [accionando, setAccionando] = useState(false);
  const [aviso, setAviso] = useState({ texto: '', irInventario: false });

  const cargar = useCallback(async (q, idItem) => {
    setCargando(true);
    setError(null);
    try {
      const params = {};
      if (q && q.trim()) params.q = q.trim();
      if (idItem) params.id_item = idItem;
      const [inventario, listado] = await Promise.all([
        api.get('/api/v1/inventario'),
        api.get('/api/v1/recetas', { params }),
      ]);
      setItems(inventario.data.items || []);
      setRecetas(listado.data.recetas || []);
    } catch (err) {
      if (idItem && err.response?.status === 404) {
        // el producto ya no está activo: quitamos el filtro y se recarga solo
        setFiltro(null);
        return;
      }
      setError(mensajeDeError(err));
    } finally {
      setCargando(false);
    }
  }, []);

  // Llega desde Inventario con { idItem, nombre } al tocar "Ver recetas con ...".
  const idItemParam = route?.params?.idItem;
  const nombreParam = route?.params?.nombre;
  useEffect(() => {
    if (idItemParam) {
      setFiltro({ id: idItemParam, nombre: nombreParam });
      setSeleccionada(null);
      setBusqueda('');
      navigation.setParams({ idItem: undefined, nombre: undefined });
    }
  }, [idItemParam]);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Recetas · FreshTrack';
      const espera = setTimeout(() => cargar(busqueda, filtro?.id), busqueda ? 350 : 0);
      return () => clearTimeout(espera);
    }, [busqueda, filtro?.id, cargar])
  );

  const conDias = items.map((item) => ({ ...item, dias: diasParaVencer(item.fecha_vencimiento_est) }));
  const porVencer = conDias
    .filter((i) => esPorVencer(i.dias))
    .sort((a, b) => a.dias - b.dias);
  const idsPorVencer = new Set(porVencer.map((i) => i.id_alimento).filter((id) => id != null));

  // Primero las recetas que aprovechan lo que está por vencer.
  const lista = recetas
    .filter((r) => !ocultas.includes(r.id_receta))
    .map((r) => ({ ...r, urgentes: (r.ingrediente_ids || []).filter((id) => idsPorVencer.has(id)).length }))
    .sort(
      (a, b) =>
        b.urgentes - a.urgentes ||
        (b.cobertura || 0) - (a.cobertura || 0) ||
        (a.faltantes || []).length - (b.faltantes || []).length
    );

  const abrirReceta = (receta) => {
    setSeleccionada(receta);
    scrollRef.current?.scrollTo({ y: 0, animated: false });
    // registrar que se vio; si no hay ingredientes activos el backend responde 422 y se ignora
    api.post(`/api/v1/recetas/${receta.id_receta}/accion`, { accion: 'vista' }).catch(() => {});
  };

  const registrarAccion = async (receta, accion) => {
    setAccionando(true);
    try {
      await api.post(`/api/v1/recetas/${receta.id_receta}/accion`, { accion });
      if (accion === 'usada') {
        setAviso({ texto: '¡Buen provecho! 🍽️ Marca lo que usaste como consumido en tu inventario.', irInventario: true });
      } else {
        setOcultas((prev) => [...prev, receta.id_receta]);
        setAviso({ texto: 'Listo, no te la volveremos a mostrar en esta sesión.', irInventario: false });
      }
      setSeleccionada(null);
    } catch (err) {
      setAviso({ texto: mensajeDeError(err), irInventario: false });
    } finally {
      setAccionando(false);
    }
  };

  const quitarFiltro = () => {
    setFiltro(null);
    setSeleccionada(null);
  };

  const chipsPorVencer = (
    <View>
      <Text style={styles.seccion}>⏳ Rescátalos primero</Text>
      {porVencer.length === 0 ? (
        <View style={styles.cajaTranquila}>
          <Text style={styles.cajaTranquilaTexto}>
            No tienes productos por vencer en los próximos {DIAS_POR_VENCER} días. ¡Tu despensa está al día! 🎉
          </Text>
        </View>
      ) : (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
          {porVencer.map((item) => {
            const estado = estadoVencimiento(item.dias);
            const activo = filtro?.id === item.id_item;
            return (
              <Pressable
                key={item.id_item}
                onPress={() => {
                  setSeleccionada(null);
                  setBusqueda('');
                  setFiltro(activo ? null : { id: item.id_item, nombre: item.nombre });
                }}
                style={[
                  styles.chip,
                  { borderColor: estado.color },
                  activo && { backgroundColor: estado.color },
                ]}
                accessibilityRole="button"
                accessibilityLabel={`Recetas con ${item.nombre}`}
              >
                <Text style={styles.chipEmoji}>{emojiAlimento(item.nombre)}</Text>
                <View>
                  <Text style={[styles.chipNombre, activo && { color: estado.texto }]} numberOfLines={1}>
                    {item.nombre}
                  </Text>
                  <Text style={[styles.chipDias, activo && { color: estado.texto }]}>{estado.etiqueta}</Text>
                </View>
              </Pressable>
            );
          })}
        </ScrollView>
      )}
    </View>
  );

  return (
    <View style={styles.raiz}>
      <ScrollView ref={scrollRef} contentContainerStyle={styles.contenido} keyboardShouldPersistTaps="handled">
        {seleccionada ? (
          <DetalleReceta
            receta={seleccionada}
            idsPorVencer={idsPorVencer}
            onVolver={() => setSeleccionada(null)}
            onAccion={registrarAccion}
            accionando={accionando}
          />
        ) : (
          <>
            <View style={styles.hero}>
              <View style={[styles.heroCirculo, styles.heroCirculoA]} />
              <View style={[styles.heroCirculo, styles.heroCirculoB]} />
              <Text style={styles.heroEtiqueta}>RECETARIO</Text>
              <Text style={styles.heroTitulo}>Cocina lo que ya tienes</Text>
              <Text style={styles.heroMano}>antes de que se dañe, ¡a la olla!</Text>
            </View>

            <Searchbar
              placeholder="Busca una receta o ingrediente"
              value={busqueda}
              onChangeText={setBusqueda}
              style={styles.buscador}
              inputStyle={styles.buscadorTexto}
              iconColor={colores.hoja}
            />

            {chipsPorVencer}

            {filtro && (
              <View style={styles.filtro}>
                <Text style={styles.filtroTexto} numberOfLines={2}>
                  Mostrando recetas con <Text style={styles.filtroNombre}>{filtro.nombre}</Text>
                </Text>
                <Button compact mode="text" onPress={quitarFiltro} textColor={colores.hoja} labelStyle={styles.botonEtiqueta}>
                  Ver todas
                </Button>
              </View>
            )}

            <Text style={styles.seccion}>
              🍽 {filtro ? 'Recetas para aprovecharlo' : 'Recetas para ti'}
              {!cargando && !error ? ` (${lista.length})` : ''}
            </Text>

            {cargando && lista.length === 0 && (
              <ActivityIndicator size="large" color={colores.hoja} style={{ marginTop: 20 }} />
            )}

            {error && (
              <View style={styles.vacio}>
                <Text style={styles.vacioEmoji}>🔌</Text>
                <Text style={styles.vacioTitulo}>No pudimos cargar las recetas</Text>
                <Text style={styles.vacioTexto}>{error}</Text>
                <Button mode="contained" onPress={() => cargar(busqueda, filtro?.id)} style={styles.vacioBoton}>
                  Reintentar
                </Button>
              </View>
            )}

            {!cargando && !error && lista.length === 0 && (
              <View style={styles.vacio}>
                <Text style={styles.vacioEmoji}>🥣</Text>
                <Text style={styles.vacioTitulo}>No encontramos recetas</Text>
                <Text style={styles.vacioTexto}>
                  {filtro
                    ? 'Por ahora no tenemos recetas con ese producto. Prueba con otro o mira todas.'
                    : busqueda
                      ? 'Prueba con otra palabra, por ejemplo "tomate" o "ensalada".'
                      : 'Agrega frutas o verduras a tu inventario para recibir ideas.'}
                </Text>
                {filtro && (
                  <Button mode="contained" onPress={quitarFiltro} style={styles.vacioBoton}>
                    Ver todas las recetas
                  </Button>
                )}
                {!filtro && !busqueda && items.length === 0 && (
                  <Button mode="contained" icon="plus" onPress={() => navigation.navigate('Anadir')} style={styles.vacioBoton}>
                    Añadir productos
                  </Button>
                )}
              </View>
            )}

            {!error && lista.map((receta) => (
              <TarjetaReceta key={receta.id_receta} receta={receta} onPress={() => abrirReceta(receta)} />
            ))}
          </>
        )}
      </ScrollView>

      <Snackbar
        visible={!!aviso.texto}
        onDismiss={() => setAviso({ texto: '', irInventario: false })}
        duration={4500}
        action={aviso.irInventario ? { label: 'Inventario', onPress: () => navigation.navigate('Inventario') } : undefined}
      >
        {aviso.texto}
      </Snackbar>
    </View>
  );
}

const styles = StyleSheet.create({
  raiz: { flex: 1, backgroundColor: colores.fondo },
  contenido: { padding: 16, paddingBottom: 32 },

  hero: {
    backgroundColor: colores.papaya,
    borderRadius: 26,
    padding: 20,
    overflow: 'hidden',
    boxShadow: sombras.media,
  },
  heroCirculo: { position: 'absolute', borderRadius: 999 },
  heroCirculoA: { width: 170, height: 170, right: -40, top: -60, backgroundColor: 'rgba(255, 183, 3, 0.55)' },
  heroCirculoB: { width: 100, height: 100, right: 50, bottom: -45, backgroundColor: 'rgba(255, 255, 255, 0.22)' },
  heroEtiqueta: { fontFamily: fuentes.textoExtra, fontSize: 12, letterSpacing: 2, color: colores.selva },
  heroTitulo: { fontFamily: fuentes.titulo, fontSize: 30, color: colores.blanco, lineHeight: 36, marginTop: 2 },
  heroMano: { fontFamily: fuentes.mano, fontSize: 23, color: colores.selva, marginTop: 2 },

  buscador: { marginTop: 14, borderRadius: 16, backgroundColor: colores.blanco, boxShadow: sombras.suave },
  buscadorTexto: { fontFamily: fuentes.texto, fontSize: 15 },

  seccion: { fontFamily: fuentes.subtitulo, fontSize: 19, color: colores.selva, marginTop: 22, marginBottom: 10 },

  chips: { gap: 10, paddingRight: 8 },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colores.blanco,
    borderWidth: 2,
    borderRadius: 18,
    paddingVertical: 8,
    paddingHorizontal: 12,
    gap: 8,
  },
  chipEmoji: { fontSize: 26 },
  chipNombre: { fontFamily: fuentes.textoExtra, fontSize: 14, color: colores.tinta, maxWidth: 110 },
  chipDias: { fontFamily: fuentes.textoMedio, fontSize: 12, color: colores.suave },

  cajaTranquila: { backgroundColor: colores.menta, borderRadius: 16, padding: 14 },
  cajaTranquilaTexto: { fontFamily: fuentes.textoMedio, fontSize: 14, color: colores.selva },

  filtro: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF3D6',
    borderRadius: 14,
    paddingLeft: 14,
    paddingRight: 4,
    paddingVertical: 4,
    marginTop: 16,
  },
  filtroTexto: { flex: 1, fontFamily: fuentes.textoMedio, fontSize: 14, color: colores.tinta },
  filtroNombre: { fontFamily: fuentes.textoExtra },

  tarjeta: {
    flexDirection: 'row',
    backgroundColor: colores.blanco,
    borderRadius: 22,
    padding: 12,
    marginBottom: 12,
    boxShadow: sombras.suave,
  },
  tarjetaEmoji: { width: 78, borderRadius: 18, alignItems: 'center', justifyContent: 'center', minHeight: 96 },
  tarjetaEmojiTexto: { fontSize: 40 },
  tarjetaInfo: { flex: 1, marginLeft: 12 },
  tarjetaTitulo: { fontFamily: fuentes.subtitulo, fontSize: 18, color: colores.tinta, lineHeight: 22 },
  tarjetaMeta: { fontFamily: fuentes.textoMedio, fontSize: 13, color: colores.suave, marginTop: 4 },
  barraFondo: { height: 8, backgroundColor: '#E8EEE6', borderRadius: 999, marginTop: 10, overflow: 'hidden' },
  barraRelleno: { height: 8, borderRadius: 999 },
  tarjetaCobertura: { fontFamily: fuentes.textoMedio, fontSize: 12, color: colores.suave, marginTop: 4 },
  etiquetaUrgente: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFE3D1',
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 3,
    marginTop: 8,
  },
  etiquetaUrgenteTexto: { fontFamily: fuentes.textoExtra, fontSize: 12, color: '#B8430A' },

  volver: { alignSelf: 'flex-start', marginLeft: -8 },
  detalleHero: { borderRadius: 26, padding: 22, alignItems: 'center', boxShadow: sombras.suave },
  detalleEmoji: { fontSize: 76 },
  detalleTitulo: { fontFamily: fuentes.titulo, fontSize: 28, color: colores.selva, textAlign: 'center', marginTop: 6 },
  detalleMetas: { flexDirection: 'row', gap: 10, marginTop: 10 },
  detalleMeta: {
    fontFamily: fuentes.textoExtra,
    fontSize: 13,
    color: colores.selva,
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
    overflow: 'hidden',
  },

  caja: { backgroundColor: colores.blanco, borderRadius: 20, padding: 14, boxShadow: sombras.suave },
  ingrediente: { flexDirection: 'row', alignItems: 'center', paddingVertical: 7, flexWrap: 'wrap' },
  ingredienteIcono: { fontSize: 18, marginRight: 10 },
  ingredienteNombre: { fontFamily: fuentes.textoNegrita, fontSize: 15, color: colores.tinta },
  ingredienteFalta: { color: colores.suave },
  ingredienteNota: { fontFamily: fuentes.mano, fontSize: 18, color: colores.papaya, marginLeft: 8 },

  paso: { flexDirection: 'row', alignItems: 'flex-start', paddingVertical: 8 },
  pasoNumero: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colores.hoja,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 1,
  },
  pasoNumeroTexto: { fontFamily: fuentes.textoExtra, fontSize: 14, color: colores.blanco },
  pasoTexto: { flex: 1, fontFamily: fuentes.textoMedio, fontSize: 15, color: colores.tinta, lineHeight: 22 },

  botonPrincipal: { marginTop: 22, borderRadius: 16 },
  botonSecundario: { marginTop: 10, borderRadius: 16 },
  botonEtiqueta: { fontFamily: fuentes.textoExtra, fontSize: 13 },
  botonEtiquetaGrande: { fontFamily: fuentes.textoExtra, fontSize: 16 },

  vacio: { alignItems: 'center', padding: 24 },
  vacioEmoji: { fontSize: 50, marginBottom: 6 },
  vacioTitulo: { fontFamily: fuentes.subtitulo, fontSize: 20, color: colores.selva, textAlign: 'center' },
  vacioTexto: { fontFamily: fuentes.texto, fontSize: 14, color: colores.suave, textAlign: 'center', marginTop: 6 },
  vacioBoton: { marginTop: 14, borderRadius: 14 },
});
