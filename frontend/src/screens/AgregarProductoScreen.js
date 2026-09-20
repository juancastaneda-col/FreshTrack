import { useState, useCallback } from 'react';
import { View, StyleSheet, ScrollView, Platform } from 'react-native';
import { Text, TextInput, Button, List, SegmentedButtons, ActivityIndicator } from 'react-native-paper';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../services/api';

function mensajeDeError(error, fallback) {
  if (!error.response) {
    return 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.';
  }
  const detalle = error.response.data?.detail;
  if (Array.isArray(detalle)) return detalle.map((d) => d.msg).join(' · ');
  if (typeof detalle === 'string') return detalle;
  return fallback || `Error ${error.response.status}.`;
}

const UNIDADES = [
  { value: 'UND', label: 'Unidad' },
  { value: 'KG', label: 'Kilo' },
  { value: 'LB', label: 'Libra' },
  { value: 'G', label: 'Gramo' },
  { value: 'MANOJO', label: 'Manojo' },
];

export default function AgregarProductoScreen() {
  const [busqueda, setBusqueda] = useState('');
  const [resultados, setResultados] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [sinResultados, setSinResultados] = useState(false);

  const [seleccionado, setSeleccionado] = useState(null); // { id_alimento, nombre }
  const [cantidad, setCantidad] = useState('1');
  const [unidad, setUnidad] = useState('UND');
  const [condicion, setCondicion] = useState('fuera');
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [exito, setExito] = useState(null);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Agregar producto · FreshTrack';
    }, [])
  );

  const buscarEnCatalogo = async (texto) => {
    setBusqueda(texto);
    setSeleccionado(null);
    if (texto.trim().length < 2) {
      setResultados([]);
      setSinResultados(false);
      return;
    }
    setBuscando(true);
    try {
      const { data } = await api.get('/api/v1/catalogo', { params: { q: texto.trim() } });
      setResultados(data.resultados || []);
      setSinResultados((data.resultados || []).length === 0);
    } catch (error) {
      setResultados([]);
      setSinResultados(true);
    } finally {
      setBuscando(false);
    }
  };

  const elegirProducto = (producto) => {
    setSeleccionado(producto);
    setResultados([]);
    setBusqueda(producto.nombre);
  };

  const elegirSinCatalogo = () => {
    setSeleccionado({ id_alimento: null, nombre: busqueda.trim() });
    setResultados([]);
  };

  const guardarProducto = async () => {
    setError(null);
    setExito(null);
    if (!seleccionado) return;
    const cantidadNum = parseFloat(cantidad);
    if (!cantidadNum || cantidadNum <= 0) {
      setError('Ingresa una cantidad mayor a 0.');
      return;
    }
    setGuardando(true);
    try {
      const { data } = await api.post('/api/v1/inventario', {
        id_alimento: seleccionado.id_alimento,
        nombre: seleccionado.nombre,
        cantidad: cantidadNum,
        unidad,
        condicion,
      });

      let mensaje = 'Producto agregado a tu inventario.';
      if (data.fecha_vencimiento_est) mensaje += ` Vence el ${data.fecha_vencimiento_est}.`;
      if (data.aviso) mensaje += ` Aviso: ${data.aviso}`;

      setExito(mensaje);
      setSeleccionado(null);
      setBusqueda('');
      setCantidad('1');
      setUnidad('UND');
      setCondicion('fuera');
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo agregar el producto.'));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text variant="headlineMedium" style={styles.title}>Agregar producto</Text>
      <Text style={styles.subtitle}>Regístralo a mano si no tienes la factura.</Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {exito ? <Text style={styles.exito}>{exito}</Text> : null}

      <TextInput
        mode="outlined"
        label="Buscar en el catálogo"
        placeholder="Ej: tomate"
        value={busqueda}
        onChangeText={buscarEnCatalogo}
        style={styles.input}
      />

      {buscando && <ActivityIndicator style={{ marginVertical: 8 }} />}

      {resultados.length > 0 && (
        <List.Section style={styles.resultados}>
          {resultados.map((r) => (
            <List.Item
              key={r.id_alimento}
              title={r.nombre}
              onPress={() => elegirProducto(r)}
              left={(props) => <List.Icon {...props} icon="food-apple-outline" />}
            />
          ))}
        </List.Section>
      )}

      {sinResultados && !seleccionado && busqueda.trim().length >= 2 && (
        <View style={styles.aviso}>
          <Text style={styles.avisoTexto}>
            No se encontró en el catálogo. Puedes agregarlo igual, pero no se calculará fecha de vencimiento.
          </Text>
          <Button mode="outlined" onPress={elegirSinCatalogo} style={{ marginTop: 8 }}>
            Agregar "{busqueda.trim()}" sin catálogo
          </Button>
        </View>
      )}

      {seleccionado && (
        <View style={styles.formulario}>
          <Text variant="titleMedium" style={styles.seleccionadoTexto}>
            Producto: {seleccionado.nombre}
            {!seleccionado.id_alimento && ' (fuera del catálogo)'}
          </Text>

          <View style={styles.fila}>
            <TextInput
              mode="outlined"
              label="Cantidad"
              value={cantidad}
              onChangeText={setCantidad}
              keyboardType="numeric"
              style={{ flex: 1, marginRight: 8 }}
            />
          </View>

          <Text style={styles.etiqueta}>Unidad</Text>
          <SegmentedButtons
            value={unidad}
            onValueChange={setUnidad}
            style={styles.segmented}
            buttons={UNIDADES.slice(0, 3)}
          />
          <SegmentedButtons
            value={unidad}
            onValueChange={setUnidad}
            style={styles.segmented}
            buttons={UNIDADES.slice(3)}
          />

          <Text style={styles.etiqueta}>¿Dónde lo vas a guardar?</Text>
          <SegmentedButtons
            value={condicion}
            onValueChange={setCondicion}
            style={styles.segmented}
            buttons={[
              { value: 'fuera', label: 'Fuera de nevera' },
              { value: 'nevera', label: 'Nevera' },
            ]}
          />

          <Button
            mode="contained"
            buttonColor="#2E7D32"
            onPress={guardarProducto}
            loading={guardando}
            disabled={guardando}
            style={styles.guardarBoton}
          >
            {guardando ? 'Guardando...' : 'Guardar en inventario'}
          </Button>
          <Button onPress={() => { setSeleccionado(null); setBusqueda(''); }}>
            Cancelar
          </Button>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7F5' },
  content: { padding: 24 },
  title: { marginBottom: 4 },
  subtitle: { color: '#666', marginBottom: 20 },
  input: { marginBottom: 4 },
  resultados: { backgroundColor: '#FFF', borderRadius: 12, marginBottom: 12 },
  aviso: {
    backgroundColor: '#FFF4E5', borderLeftWidth: 4, borderLeftColor: '#E08B00',
    padding: 12, borderRadius: 8, marginBottom: 12,
  },
  avisoTexto: { color: '#5a3d00' },
  formulario: {
    backgroundColor: '#FFF', borderRadius: 12, padding: 16, marginTop: 8,
  },
  seleccionadoTexto: { marginBottom: 16 },
  fila: { flexDirection: 'row', marginBottom: 8 },
  etiqueta: { fontSize: 13, color: '#666', marginTop: 12, marginBottom: 6 },
  segmented: { marginBottom: 8 },
  guardarBoton: { marginTop: 16, marginBottom: 4 },
  error: { color: '#b3261e', backgroundColor: '#fdecea', padding: 10, borderRadius: 8, marginBottom: 12, textAlign: 'center' },
  exito: { color: '#1B5E20', backgroundColor: '#E8F5E9', padding: 10, borderRadius: 8, marginBottom: 12, textAlign: 'center' },
});