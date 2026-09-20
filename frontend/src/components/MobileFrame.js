import { View, Platform, StyleSheet } from 'react-native';

export default function MobileFrame({ children }) {
  if (Platform.OS !== 'web') {
    // En celular real, ocupa toda la pantalla normalmente
    return <View style={{ flex: 1 }}>{children}</View>;
  }
  // En navegador, simula el ancho de un celular
  return (
    <View style={styles.outer}>
      <View style={styles.phone}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    flex: 1,
    alignItems: 'center',
    backgroundColor: '#DDD',
    Height: '100vh',
  },
  phone: {
    width: 420,
    maxWidth: '100%',
    height: '100%',
    backgroundColor: '#FFF',
    boxShadow: '0 0 20px rgba(0,0,0,0.2)',
  },
});