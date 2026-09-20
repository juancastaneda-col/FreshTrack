import { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import LoginScreen from '../screens/LoginScreen';
import RegistroScreen from '../screens/RegistroScreen';
import MainTabs from './MainTabs';
import { api } from '../services/api';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  const [rutaInicial, setRutaInicial] = useState(null);

  useEffect(() => {
    api.get('/api/v1/auth/me')
      .then(() => setRutaInicial('Main'))
      .catch(() => setRutaInicial('Login'));
  }, []);

  if (rutaInicial === null) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={rutaInicial} screenOptions={{ headerShown: false, contentStyle: { flex: 1 } }}>
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Registro" component={RegistroScreen} />
        <Stack.Screen name="Main" component={MainTabs} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
