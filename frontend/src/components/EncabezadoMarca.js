import { View, Text, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colores, fuentes } from '../theme/theme';

const FRASES = {
  Inventario: 'lo que hay en tu cocina',
  Recetas: 'cocina antes de que se dañe',
  Anadir: '¿qué trajiste del mercado?',
  Cuenta: 'tu espacio en FreshTrack',
  'Escanear Factura': 'de la factura a tu despensa',
  'Escanear Alimento': 'una foto y listo',
  Agregar: 'a mano, sin afán',
};

// Cabecera de marca para todas las pestañas. Si la pantalla es una "subpantalla"
// (por ejemplo Escanear factura) muestra una flecha para volver al menú Añadir.
export default function EncabezadoMarca({ navigation, route, volverA }) {
  const insets = useSafeAreaInsets();
  const frase = FRASES[route?.name] || 'que nada se pierda';

  return (
    <View style={[styles.contenedor, { paddingTop: insets.top + 12 }]}>
      <View style={[styles.circulo, styles.circuloMango]} />
      <View style={[styles.circulo, styles.circuloLima]} />

      <View style={styles.fila}>
        {volverA ? (
          <Pressable
            onPress={() => navigation.navigate(volverA)}
            style={styles.volver}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel="Volver"
          >
            <MaterialCommunityIcons name="arrow-left" size={22} color={colores.blanco} />
          </Pressable>
        ) : (
          <View style={styles.sello}>
            <MaterialCommunityIcons name="leaf" size={20} color={colores.selva} />
          </View>
        )}

        <View style={styles.textos}>
          <Text style={styles.marca}>FreshTrack</Text>
          <Text style={styles.frase}>{frase}</Text>
        </View>

        <Text style={styles.emoji}>🥭</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  contenedor: {
    backgroundColor: colores.selva,
    paddingBottom: 14,
    paddingHorizontal: 18,
    overflow: 'hidden',
    borderBottomLeftRadius: 26,
    borderBottomRightRadius: 26,
  },
  circulo: { position: 'absolute', borderRadius: 999 },
  circuloMango: { width: 120, height: 120, right: -30, top: -40, backgroundColor: 'rgba(255, 183, 3, 0.35)' },
  circuloLima: { width: 80, height: 80, right: 70, bottom: -40, backgroundColor: 'rgba(183, 227, 79, 0.30)' },
  fila: { flexDirection: 'row', alignItems: 'center' },
  sello: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colores.lima,
    alignItems: 'center',
    justifyContent: 'center',
  },
  volver: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  textos: { flex: 1, marginLeft: 12 },
  marca: { fontFamily: fuentes.titulo, fontSize: 24, color: colores.blanco, lineHeight: 28 },
  frase: { fontFamily: fuentes.mano, fontSize: 18, color: colores.mango, lineHeight: 20 },
  emoji: { fontSize: 30, marginRight: 4 },
});