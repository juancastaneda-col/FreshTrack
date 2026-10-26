import { useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Platform } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { colores, fuentes, sombras } from '../theme/theme';

const OPCIONES = [
  {
    ruta: 'Escanear Factura',
    emoji: '🧾',
    titulo: 'Escanear factura',
    texto: 'Sube la foto de tu compra y detectamos tus frutas y verduras.',
    fondo: '#FFE8CC',
  },
  {
    ruta: 'Escanear Alimento',
    emoji: '📸',
    titulo: 'Identificar con la cámara',
    texto: 'Fotografía un alimento y te decimos qué es y cómo está.',
    fondo: '#E3F6D2',
  },
  {
    ruta: 'Agregar',
    emoji: '✍️',
    titulo: 'Agregar a mano',
    texto: 'Búscalo en el catálogo, indica cantidad y dónde lo guardas.',
    fondo: '#FFF3BF',
  },
];

export default function AnadirScreen({ navigation }) {
  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Añadir · FreshTrack';
    }, [])
  );

  return (
    <ScrollView contentContainerStyle={styles.contenido} style={styles.raiz}>
      <Text style={styles.titulo}>¿Cómo quieres añadir?</Text>
      <Text style={styles.mano}>elige la forma más fácil para ti</Text>

      {OPCIONES.map((op) => (
        <Pressable
          key={op.ruta}
          onPress={() => navigation.navigate(op.ruta)}
          style={({ pressed }) => [styles.tarjeta, { backgroundColor: op.fondo }, pressed && { opacity: 0.85 }]}
          accessibilityRole="button"
          accessibilityLabel={op.titulo}
        >
          <Text style={styles.emoji}>{op.emoji}</Text>
          <View style={styles.textos}>
            <Text style={styles.tarjetaTitulo}>{op.titulo}</Text>
            <Text style={styles.tarjetaTexto}>{op.texto}</Text>
          </View>
          <MaterialCommunityIcons name="chevron-right" size={28} color={colores.selva} />
        </Pressable>
      ))}

      <View style={styles.consejo}>
        <Text style={styles.consejoTexto}>
          💡 En Colombia se pierde o se desperdicia cerca de un tercio de los alimentos (DNP), y las
          frutas y verduras son las más afectadas. Cuidar lo que llega a tu cocina también cuenta.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  raiz: { flex: 1, backgroundColor: colores.fondo },
  contenido: { padding: 18, paddingBottom: 32 },
  titulo: { fontFamily: fuentes.titulo, fontSize: 30, color: colores.selva, lineHeight: 36 },
  mano: { fontFamily: fuentes.mano, fontSize: 23, color: colores.papaya, marginBottom: 14 },
  tarjeta: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 24,
    padding: 18,
    marginBottom: 14,
    boxShadow: sombras.suave,
  },
  emoji: { fontSize: 44, marginRight: 14 },
  textos: { flex: 1 },
  tarjetaTitulo: { fontFamily: fuentes.subtitulo, fontSize: 19, color: colores.selva },
  tarjetaTexto: { fontFamily: fuentes.textoMedio, fontSize: 13, color: colores.tinta, marginTop: 3, lineHeight: 18 },
  consejo: { backgroundColor: colores.selva, borderRadius: 20, padding: 16, marginTop: 6 },
  consejoTexto: { fontFamily: fuentes.textoMedio, fontSize: 13, color: colores.blanco, lineHeight: 19 },
});