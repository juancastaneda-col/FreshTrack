import { View, Platform, StyleSheet, useWindowDimensions } from 'react-native';
import { colores, sombras } from '../theme/theme';


export default function MobileFrame({ children }) {
  const { width, height } = useWindowDimensions();

  if (Platform.OS !== 'web' || width <= 480) {
    return <View style={{ flex: 1, backgroundColor: colores.fondo }}>{children}</View>;
  }

  return (
    <View style={styles.exterior}>
      <View style={[styles.circulo, styles.circuloMango]} />
      <View style={[styles.circulo, styles.circuloLima]} />
      <View style={[styles.circulo, styles.circuloPapaya]} />
      <View style={[styles.telefono, { height: Math.min(height - 32, 880) }]}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  exterior: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colores.selva,
    overflow: 'hidden',
  },
  circulo: { position: 'absolute', borderRadius: 999 },
  circuloMango: { width: 420, height: 420, top: -140, left: -120, backgroundColor: 'rgba(255, 183, 3, 0.18)' },
  circuloLima: { width: 360, height: 360, bottom: -120, right: -80, backgroundColor: 'rgba(183, 227, 79, 0.18)' },
  circuloPapaya: { width: 220, height: 220, top: '55%', left: '8%', backgroundColor: 'rgba(251, 133, 0, 0.14)' },
  telefono: {
    width: 420,
    maxWidth: '100%',
    backgroundColor: colores.fondo,
    borderRadius: 32,
    overflow: 'hidden',
    boxShadow: sombras.media,
  },
});