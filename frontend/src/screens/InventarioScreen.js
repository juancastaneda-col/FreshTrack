import { useState, useCallback } from 'react';
import { View, StyleSheet, ScrollView, ActivityIndicator, Platform } from 'react-native';
import { Text, Card, Chip, Button } from 'react-native-paper';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../services/api';

function calcularEstado(fechaVencimiento) {
  if (!fechaVencimiento) return { color: '#9E9E9E', label: 'Sin fecha' };
  const hoy = new Date();
  const vence = new Date(fechaVencimiento);
  const dias = Math.ceil((vence - hoy) / (1000 * 60 * 60 * 24));
  if (dias < 0) return { color: '#C62828', label: `Vencido hace ${Math.abs(dias)}d` };
  if (dias <= 3) return { color: '#F9A825', label: `Vence en ${dias}d` };
  return { color: '#2E7D32', label: `Vence en ${dias}d` };
}

export default function InventarioScreen() {
  const [items, setItems] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [actualizandoId, setActualizandoId] = useState(null);

  // Se ejecuta cada vez que esta pestaña vuelve a estar en foco
  // (por ejemplo, justo después de confirmar una factura en Escanear).
  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Inventario · FreshTrack';
      cargarInventario();
    }, [])
  );

  const cargarInventario = async () => {
    setCargando(true);
    setError(null);
    try {
      const { data } = await api.get('/api/v1/inventario');
      setItems(data.items || []);
    } catch (err) {
      setError('No se pudo conectar con el servidor. ¿Iniciaste sesión?');
    } finally {
      setCargando(false);
    }
  };

  const cambiarSituacion = async (idItem, situacion) => {
    setActualizandoId(idItem);
    try {
      await api.patch(`/api/v1/inventario/${idItem}`, { situacion });
      // Quitamos el item de la lista visible al instante, sin esperar recarga completa
      setItems((prev) => prev.filter((i) => i.id_item !== idItem));
    } catch (err) {
      // si falla, no hacemos nada visual raro; el usuario puede reintentar
    } finally {
      setActualizandoId(null);
    }
  };

  if (cargando) return <ActivityIndicator style={{ flex: 1 }} size="large" />;
  if (error) return <View style={styles.container}><Text style={{ padding: 16 }}>{error}</Text></View>;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text variant="headlineMedium" style={styles.title}>Mi despensa</Text>
      {items.length === 0 && <Text>Aún no tienes productos en tu inventario.</Text>}
      {items.map((item) => {
        const estado = calcularEstado(item.fecha_vencimiento_est);
        const actualizando = actualizandoId === item.id_item;
        return (
          <Card key={item.id_item} style={styles.card}>
            <Card.Content>
              <View style={styles.cardHeader}>
                <View style={styles.info}>
                  <Text variant="titleMedium">{item.nombre}</Text>
                  <Text variant="bodySmall" style={styles.detalle}>
                    {item.cantidad} {item.unidad} · {item.condicion === 'nevera' ? 'Nevera' : 'Fuera de nevera'}
                  </Text>
                </View>
                <Chip style={{ backgroundColor: estado.color }} textStyle={{ color: '#FFF' }}>
                  {estado.label}
                </Chip>
              </View>
              <View style={styles.acciones}>
                <Button
                  mode="outlined"
                  compact
                  onPress={() => cambiarSituacion(item.id_item, 'consumido')}
                  disabled={actualizando}
                  style={styles.accionBoton}
                >
                  Consumido
                </Button>
                <Button
                  mode="outlined"
                  compact
                  textColor="#C62828"
                  onPress={() => cambiarSituacion(item.id_item, 'desechado')}
                  disabled={actualizando}
                  style={styles.accionBoton}
                >
                  Desechado
                </Button>
              </View>
            </Card.Content>
          </Card>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7F5' },
  content: { padding: 16 },
  title: { marginBottom: 16 },
  card: { marginBottom: 12, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  info: { flex: 1 },
  detalle: { color: '#666', marginTop: 4 },
  acciones: { flexDirection: 'row', marginTop: 12, gap: 8 },
  accionBoton: { flex: 1 },
});