import { Alert, Platform } from 'react-native';

// Alert.alert no hace nada en la versión web de React Native,
// así que en el navegador usamos window.alert.
export function avisar(titulo, mensaje) {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined') {
      window.alert(mensaje ? `${titulo}\n\n${mensaje}` : titulo);
    }
    return;
  }
  Alert.alert(titulo, mensaje);
}