import { MD3LightTheme, configureFonts } from 'react-native-paper';


export const colores = {
  selva: '#0F4D2A', // verde profundo (cabeceras y fondos fuertes)
  hoja: '#2E7D32', // verde principal
  menta: '#DDF3C8', // verde suave
  lima: '#B7E34F', // acento fresco
  mango: '#FFB703', // amarillo mango
  papaya: '#FB8500', // naranja papaya
  tomate: '#D62839', // rojo tomate
  crema: '#FFF6E3',
  fondo: '#F5F7F5',
  tinta: '#1B2A1F', // texto principal
  suave: '#5F6F62', // texto secundario
  borde: '#E3EBE0',
  blanco: '#FFFFFF',
};


export const fuentes = {
  titulo: 'Fraunces_900Black',
  subtitulo: 'Fraunces_700Bold',
  texto: 'Nunito_400Regular',
  textoMedio: 'Nunito_600SemiBold',
  textoNegrita: 'Nunito_700Bold',
  textoExtra: 'Nunito_800ExtraBold',
  mano: 'Caveat_700Bold',
};

export const sombras = {
  suave: '0 4px 14px rgba(15, 77, 42, 0.08)',
  media: '0 8px 24px rgba(15, 77, 42, 0.18)',
};

const f = (fontFamily) => ({ fontFamily, fontWeight: '400' });

const fontConfig = {
  displayLarge: f(fuentes.titulo),
  displayMedium: f(fuentes.titulo),
  displaySmall: f(fuentes.titulo),
  headlineLarge: f(fuentes.titulo),
  headlineMedium: f(fuentes.titulo),
  headlineSmall: f(fuentes.subtitulo),
  titleLarge: f(fuentes.subtitulo),
  titleMedium: f(fuentes.textoExtra),
  titleSmall: f(fuentes.textoNegrita),
  labelLarge: f(fuentes.textoNegrita),
  labelMedium: f(fuentes.textoNegrita),
  labelSmall: f(fuentes.textoNegrita),
  bodyLarge: f(fuentes.texto),
  bodyMedium: f(fuentes.texto),
  bodySmall: f(fuentes.texto),
};

export const theme = {
  ...MD3LightTheme,
  roundness: 5,
  fonts: configureFonts({ config: fontConfig }),
  colors: {
    ...MD3LightTheme.colors,
    primary: colores.hoja,
    onPrimary: colores.blanco,
    primaryContainer: colores.menta,
    onPrimaryContainer: colores.selva,
    secondary: colores.papaya,
    onSecondary: colores.blanco,
    secondaryContainer: colores.menta,
    onSecondaryContainer: colores.selva,
    tertiary: colores.mango,
    error: colores.tomate,
    background: colores.fondo,
    surface: colores.blanco,
    surfaceVariant: '#EEF3EC',
    outline: '#9DB5A0',
    outlineVariant: colores.borde,
    onSurface: colores.tinta,
  },
};