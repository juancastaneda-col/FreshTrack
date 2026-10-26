import { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, Platform, RefreshControl } from 'react-native';
import { Button, Snackbar } from 'react-native-paper';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../services/api';
import { colores, fuentes, sombras } from '../theme/theme';
import { diasParaVencer, esPorVencer, estadoVencimiento, emojiAlimento } from '../utils/alimentos';
import { mensajeDeError } from '../utils/errores';

export default function InventarioScreen({ navigation }) {
  const [items, setItems] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [refrescando, setRefrescando] = useState(false);
  const [error, setError] = useState(null);
  const [actualizandoId, setActualizandoId] = useState(null);
  const [aviso, setAviso] = useState('');

  // Se ejecuta cada vez que esta pestaña vuelve a estar en foco
  // (por ejemplo, justo después de confirmar una factura).
  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Inventario · FreshTrack';
      cargarInventario();
    }, [])
  );

  const cargarInventario = async (desdeRefresco = false) => {
    if (!desdeRefresco) setCargando(true);
    setError(null);
    try {
      const { data } = await api.get('/api/v1/inventario');
      setItems(data.items || []);
    } catch (err) {
      setError(mensajeDeError(err));
    } finally {
      setCargando(false);
      setRefrescando(false);
    }
  };

  const cambiarSituacion = async (idItem, situacion) => {
    setActualizandoId(idItem);
    try {
      await api.patch(`/api/v1/inventario/${idItem}`, { situacion });
      setItems((prev) => prev.filter((i) => i.id_item !== idItem));
      setAviso(situacion === 'consumido' ? '¡Aprovechado! 💚 Uno menos que se pierde.' : 'Listo, lo sacamos de tu inventario.');
    } catch (err) {
      setAviso(mensajeDeError(err));
    } finally {
      setActualizandoId(null);
    }
  };

  const verRecetas = (item) => navigation.navigate('Recetas', { idItem: item.id_item, nombre: item.nombre });

  if (cargando) {
    return (
      <View style={styles.centro}>
        <ActivityIndicator size="large" color={colores.hoja} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centro}>
        <Text style={styles.vacioEmoji}>🔌</Text>
        <Text style={styles.vacioTitulo}>No pudimos cargar tu inventario</Text>
        <Text style={styles.vacioTexto}>{error}</Text>
        <Button mode="contained" onPress={() => cargarInventario()} style={styles.vacioBoton}>
          Reintentar
        </Button>
      </View>
    );
  }

  const conDias = items.map((item) => ({ ...item, dias: diasParaVencer(item.fecha_vencimiento_est) }));
  const vencidos = conDias.filter((i) => i.dias !== null && i.dias < 0);
  const porVencer = conDias.filter((i) => esPorVencer(i.dias));
  const primero = conDias.filter((i) => i.dias !== null && i.dias <= 5);
  const resto = conDias.filter((i) => i.dias === null || i.dias > 5);

  const tarjeta = (item) => {
    const estado = estadoVencimiento(item.dias);
    const ocupado = actualizandoId === item.id_item;
    const puedeCocinar = esPorVencer(item.dias);
    return (
      <View key={item.id_item} style={[styles.tarjeta, { borderLeftColor: estado.color }]}>
        <View style={styles.fila}>
          <View style={[styles.emojiCaja, { backgroundColor: `${estado.color}22` }]}>
            <Text style={styles.emoji}>{emojiAlimento(item.nombre)}</Text>
          </View>
          <View style={styles.info}>
            <Text style={styles.nombre} numberOfLines={2}>{item.nombre}</Text>
            <Text style={styles.detalle}>
              {Number(item.cantidad)} {item.unidad} · {item.condicion === 'nevera' ? '❄️ Nevera' : '🏠 Fuera de nevera'}
            </Text>
            <View style={[styles.pastilla, { backgroundColor: estado.color }]}>
              <Text style={[styles.pastillaTexto, { color: estado.texto }]}>{estado.etiqueta}</Text>
            </View>
          </View>
        </View>

        {puedeCocinar && (
          <Button
            mode="contained"
            icon="chef-hat"
            buttonColor={colores.papaya}
            textColor={colores.blanco}
            onPress={() => verRecetas(item)}
            style={styles.botonReceta}
            labelStyle={styles.botonEtiqueta}
          >
            Ver recetas con {item.nombre}
          </Button>
        )}

        <View style={styles.acciones}>
          <Button
            mode="outlined"
            compact
            icon="check"
            onPress={() => cambiarSituacion(item.id_item, 'consumido')}
            disabled={ocupado}
            style={styles.accionBoton}
            labelStyle={styles.botonEtiqueta}
          >
            Consumido
          </Button>
          <Button
            mode="outlined"
            compact
            icon="trash-can-outline"
            textColor={colores.tomate}
            onPress={() => cambiarSituacion(item.id_item, 'desechado')}
            disabled={ocupado}
            style={styles.accionBoton}
            labelStyle={styles.botonEtiqueta}
          >
            Desechado
          </Button>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.raiz}>
      <ScrollView
        contentContainerStyle={styles.contenido}
        refreshControl={
          <RefreshControl
            refreshing={refrescando}
            onRefresh={() => {
              setRefrescando(true);
              cargarInventario(true);
            }}
          />
        }
      >
        <View style={styles.hero}>
          <View style={[styles.heroCirculo, styles.heroCirculoA]} />
          <View style={[styles.heroCirculo, styles.heroCirculoB]} />
          <Text style={styles.heroEtiqueta}>MI DESPENSA</Text>

          {items.length === 0 ? (
            <>
              <Text style={styles.heroTitulo}>Empecemos a llenar tu cocina</Text>
              <Text style={styles.heroMano}>cada alimento que registras es uno que no se pierde</Text>
            </>
          ) : porVencer.length > 0 ? (
            <>
              <Text style={styles.heroNumero}>{porVencer.length}</Text>
              <Text style={styles.heroTitulo}>
                {porVencer.length === 1 ? 'producto pide' : 'productos piden'} tu atención
              </Text>
              <Text style={styles.heroMano}>¡Cocínalos hoy y no los pierdas!</Text>
              <Button
                mode="contained"
                icon="chef-hat"
                buttonColor={colores.mango}
                textColor={colores.selva}
                onPress={() => navigation.navigate('Recetas')}
                style={styles.heroBoton}
                labelStyle={styles.botonEtiqueta}
              >
                Ver recetas
              </Button>
            </>
          ) : vencidos.length > 0 ? (
            <>
              <Text style={styles.heroTitulo}>Tienes {vencidos.length} vencido{vencidos.length === 1 ? '' : 's'}</Text>
              <Text style={styles.heroMano}>revísalos y sácalos de tu lista</Text>
            </>
          ) : (
            <>
              <Text style={styles.heroTitulo}>Todo fresco por aquí 🎉</Text>
              <Text style={styles.heroMano}>nada por vencer en los próximos días</Text>
            </>
          )}

          {items.length > 0 && (
            <View style={styles.stats}>
              <View style={styles.stat}>
                <Text style={styles.statNumero}>{items.length}</Text>
                <Text style={styles.statTexto}>en total</Text>
              </View>
              <View style={styles.stat}>
                <Text style={[styles.statNumero, { color: colores.mango }]}>{porVencer.length}</Text>
                <Text style={styles.statTexto}>por vencer</Text>
              </View>
              <View style={styles.stat}>
                <Text style={[styles.statNumero, { color: '#FF8A8A' }]}>{vencidos.length}</Text>
                <Text style={styles.statTexto}>vencidos</Text>
              </View>
            </View>
          )}
        </View>

        {items.length === 0 && (
          <View style={styles.vacio}>
            <Text style={styles.vacioEmoji}>🧺</Text>
            <Text style={styles.vacioTitulo}>Tu despensa está vacía</Text>
            <Text style={styles.vacioTexto}>
              Escanea una factura, identifica un alimento con la cámara o agrégalo a mano.
            </Text>
            <Button
              mode="contained"
              icon="plus"
              onPress={() => navigation.navigate('Anadir')}
              style={styles.vacioBoton}
              labelStyle={styles.botonEtiqueta}
            >
              Añadir productos
            </Button>
          </View>
        )}

        {primero.length > 0 && (
          <>
            <Text style={styles.seccion}>⚠️ Primero estos</Text>
            {primero.map(tarjeta)}
          </>
        )}

        {resto.length > 0 && (
          <>
            <Text style={styles.seccion}>🌱 En buen estado</Text>
            {resto.map(tarjeta)}
          </>
        )}
      </ScrollView>

      <Snackbar visible={!!aviso} onDismiss={() => setAviso('')} duration={3000}>
        {aviso}
      </Snackbar>
    </View>
  );
}

const styles = StyleSheet.create({
  raiz: { flex: 1, backgroundColor: colores.fondo },
  centro: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 28, backgroundColor: colores.fondo },
  contenido: { padding: 16, paddingBottom: 28 },

  hero: {
    backgroundColor: colores.hoja,
    borderRadius: 26,
    padding: 20,
    overflow: 'hidden',
    marginBottom: 6,
    boxShadow: sombras.media,
  },
  heroCirculo: { position: 'absolute', borderRadius: 999 },
  heroCirculoA: { width: 170, height: 170, right: -50, top: -60, backgroundColor: 'rgba(255, 183, 3, 0.35)' },
  heroCirculoB: { width: 110, height: 110, right: 40, bottom: -50, backgroundColor: 'rgba(183, 227, 79, 0.28)' },
  heroEtiqueta: { fontFamily: fuentes.textoExtra, fontSize: 12, letterSpacing: 2, color: colores.lima },
  heroNumero: { fontFamily: fuentes.titulo, fontSize: 64, color: colores.blanco, lineHeight: 70 },
  heroTitulo: { fontFamily: fuentes.subtitulo, fontSize: 22, color: colores.blanco, marginTop: 2 },
  heroMano: { fontFamily: fuentes.mano, fontSize: 22, color: colores.mango, marginTop: 2 },
  heroBoton: { marginTop: 14, alignSelf: 'flex-start', borderRadius: 14 },
  stats: {
    flexDirection: 'row',
    marginTop: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.18)',
    borderRadius: 16,
    paddingVertical: 10,
  },
  stat: { flex: 1, alignItems: 'center' },
  statNumero: { fontFamily: fuentes.titulo, fontSize: 24, color: colores.blanco },
  statTexto: { fontFamily: fuentes.textoMedio, fontSize: 12, color: 'rgba(255,255,255,0.85)' },

  seccion: { fontFamily: fuentes.subtitulo, fontSize: 19, color: colores.selva, marginTop: 20, marginBottom: 10 },

  tarjeta: {
    backgroundColor: colores.blanco,
    borderRadius: 20,
    padding: 14,
    marginBottom: 12,
    borderLeftWidth: 6,
    boxShadow: sombras.suave,
  },
  fila: { flexDirection: 'row', alignItems: 'center' },
  emojiCaja: { width: 58, height: 58, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  emoji: { fontSize: 32 },
  info: { flex: 1, marginLeft: 12 },
  nombre: { fontFamily: fuentes.textoExtra, fontSize: 17, color: colores.tinta },
  detalle: { fontFamily: fuentes.textoMedio, fontSize: 13, color: colores.suave, marginTop: 2, marginBottom: 6 },
  pastilla: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 3, borderRadius: 999 },
  pastillaTexto: { fontFamily: fuentes.textoExtra, fontSize: 12 },
  botonReceta: { marginTop: 12, borderRadius: 14 },
  botonEtiqueta: { fontFamily: fuentes.textoExtra, fontSize: 13 },
  acciones: { flexDirection: 'row', marginTop: 12, gap: 8 },
  accionBoton: { flex: 1, borderRadius: 12 },

  vacio: { alignItems: 'center', padding: 28 },
  vacioEmoji: { fontSize: 54, marginBottom: 6 },
  vacioTitulo: { fontFamily: fuentes.subtitulo, fontSize: 22, color: colores.selva, textAlign: 'center' },
  vacioTexto: { fontFamily: fuentes.texto, fontSize: 14, color: colores.suave, textAlign: 'center', marginTop: 6 },
  vacioBoton: { marginTop: 16, borderRadius: 14 },
});