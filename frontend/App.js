import { PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { View, Text, ActivityIndicator } from 'react-native';
import { useFonts } from 'expo-font';
import { Fraunces_700Bold, Fraunces_900Black } from '@expo-google-fonts/fraunces';
import {
  Nunito_400Regular,
  Nunito_600SemiBold,
  Nunito_700Bold,
  Nunito_800ExtraBold,
} from '@expo-google-fonts/nunito';
import { Caveat_700Bold } from '@expo-google-fonts/caveat';

import { theme, colores } from './src/theme/theme';
import AppNavigator from './src/navigation/AppNavigator';
import MobileFrame from './src/components/MobileFrame';

export default function App() {
  const [fuentesListas] = useFonts({
    Fraunces_700Bold,
    Fraunces_900Black,
    Nunito_400Regular,
    Nunito_600SemiBold,
    Nunito_700Bold,
    Nunito_800ExtraBold,
    Caveat_700Bold,
  });

  if (!fuentesListas) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colores.selva }}>
        <Text style={{ fontSize: 56 }}>🥭</Text>
        <ActivityIndicator size="large" color={colores.lima} style={{ marginTop: 16 }} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <StatusBar style="light" />
        <MobileFrame>
          <AppNavigator />
        </MobileFrame>
      </PaperProvider>
    </SafeAreaProvider>
  );
}