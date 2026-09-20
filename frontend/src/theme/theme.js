import { MD3LightTheme, configureFonts } from 'react-native-paper';

const fontConfig = {
  displayLarge: { fontFamily: 'Poppins_700Bold' },
  headlineLarge: { fontFamily: 'Poppins_700Bold' },
  headlineMedium: { fontFamily: 'Poppins_700Bold' },
  titleLarge: { fontFamily: 'Poppins_600SemiBold' },
  titleMedium: { fontFamily: 'Poppins_600SemiBold' },
  bodyLarge: { fontFamily: 'Poppins_400Regular' },
  bodyMedium: { fontFamily: 'Poppins_400Regular' },
  bodySmall: { fontFamily: 'Poppins_400Regular' },
  labelLarge: { fontFamily: 'Poppins_600SemiBold' },
};

export const theme = {
  ...MD3LightTheme,
  fonts: configureFonts({ config: fontConfig }),
  colors: {
    ...MD3LightTheme.colors,
    primary: '#2E7D32',
    secondary: '#F9A825',
    error: '#C62828',
    background: '#F5F7F5',
    surface: '#FFFFFF',
    onPrimary: '#FFFFFF',
  },
};