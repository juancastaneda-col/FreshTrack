import { useState } from 'react';
import { View, Text, StyleSheet, ImageBackground, ScrollView, ActivityIndicator } from 'react-native';
import { TextInput, Button } from 'react-native-paper';
import { api } from '../services/api';
import { colores, fuentes, sombras } from '../theme/theme';
import { mensajeDeError } from '../utils/errores';

export default function LoginScreen({ navigation }) {
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [verPassword, setVerPassword] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [errorMensaje, setErrorMensaje] = useState('');

  const handleLogin = async () => {
    setErrorMensaje('');
    if (!correo || !password) {
      setErrorMensaje('Ingresa tu correo y contraseña.');
      return;
    }
    setCargando(true);
    try {
      await api.post('/api/v1/auth/login', { correo, password });
      navigation.replace('Main');
    } catch (error) {
      setErrorMensaje(mensajeDeError(error));
    } finally {
      setCargando(false);
    }
  };

  return (
    <ImageBackground
      source={require('../../assets/images/login-bg.jpg')}
      style={styles.fondo}
      resizeMode="cover"
    >
      <View style={styles.velo} />
      <ScrollView contentContainerStyle={styles.contenido} keyboardShouldPersistTaps="handled">
        <View style={styles.marca}>
          <View style={styles.sello}>
            <Text style={styles.selloEmoji}>🥭</Text>
          </View>
          <Text style={styles.titulo}>FreshTrack</Text>
          <Text style={styles.lema}>¡Que ninguna fruta ni verdura se pierda!</Text>
        </View>

        <View style={styles.tarjeta}>
          <Text style={styles.saludo}>Qué bueno verte</Text>
          <Text style={styles.saludoSub}>Entra y mira qué se vence primero en tu cocina.</Text>

          <TextInput
            label="Correo electrónico"
            value={correo}
            onChangeText={setCorreo}
            style={styles.input}
            autoCapitalize="none"
            keyboardType="email-address"
            mode="outlined"
            outlineStyle={styles.contornoInput}
            activeOutlineColor={colores.hoja}
            left={<TextInput.Icon icon="email-outline" />}
          />
          <TextInput
            label="Contraseña"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!verPassword}
            style={styles.input}
            mode="outlined"
            outlineStyle={styles.contornoInput}
            activeOutlineColor={colores.hoja}
            left={<TextInput.Icon icon="lock-outline" />}
            right={
              <TextInput.Icon
                icon={verPassword ? 'eye-off-outline' : 'eye-outline'}
                onPress={() => setVerPassword(!verPassword)}
              />
            }
          />

          {errorMensaje ? <Text style={styles.error}>{errorMensaje}</Text> : null}

          {cargando ? (
            <ActivityIndicator style={styles.boton} color={colores.hoja} />
          ) : (
            <Button
              mode="contained"
              onPress={handleLogin}
              style={styles.boton}
              contentStyle={styles.botonContenido}
              labelStyle={styles.botonEtiqueta}
              icon="arrow-right"
            >
              Iniciar sesión
            </Button>
          )}

          <Button
            onPress={() => navigation.navigate('Registro')}
            textColor={colores.hoja}
            labelStyle={styles.enlace}
          >
            ¿No tienes cuenta? Regístrate
          </Button>
        </View>

        <View style={styles.beneficios}>
          <Text style={styles.pastilla}>🍅 Menos desperdicio</Text>
          <Text style={styles.pastilla}>💚 Más ahorro</Text>
          <Text style={styles.pastilla}>🍳 Recetas con lo que tienes</Text>
        </View>
      </ScrollView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  fondo: { flex: 1, width: '100%', height: '100%' },
  velo: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(8, 55, 28, 0.62)' },
  contenido: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  marca: { alignItems: 'center', marginBottom: 22 },
  sello: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: colores.mango,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    boxShadow: sombras.media,
  },
  selloEmoji: { fontSize: 40 },
  titulo: { fontFamily: fuentes.titulo, fontSize: 42, color: colores.blanco, lineHeight: 48 },
  lema: { fontFamily: fuentes.mano, fontSize: 23, color: colores.mango, textAlign: 'center' },
  tarjeta: {
    backgroundColor: colores.blanco,
    borderRadius: 28,
    padding: 22,
    boxShadow: sombras.media,
  },
  saludo: { fontFamily: fuentes.titulo, fontSize: 26, color: colores.selva },
  saludoSub: { fontFamily: fuentes.texto, fontSize: 14, color: colores.suave, marginTop: 2, marginBottom: 16 },
  input: { marginBottom: 12, backgroundColor: colores.blanco, fontFamily: fuentes.texto },
  contornoInput: { borderRadius: 14 },
  error: {
    fontFamily: fuentes.textoMedio,
    color: '#B3261E',
    backgroundColor: '#FDECEA',
    padding: 10,
    borderRadius: 12,
    marginBottom: 8,
    textAlign: 'center',
  },
  boton: { marginTop: 6, marginBottom: 6, borderRadius: 16 },
  botonContenido: { height: 50, flexDirection: 'row-reverse' },
  botonEtiqueta: { fontFamily: fuentes.textoExtra, fontSize: 16 },
  enlace: { fontFamily: fuentes.textoNegrita, fontSize: 14 },
  beneficios: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', marginTop: 18, gap: 8 },
  pastilla: {
    fontFamily: fuentes.textoNegrita,
    fontSize: 12,
    color: colores.blanco,
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    overflow: 'hidden',
  },
});