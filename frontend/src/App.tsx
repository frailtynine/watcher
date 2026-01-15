import { ChakraProvider, Box } from '@chakra-ui/react';
import { Provider } from 'react-redux';
import { store } from './store';
import { LoginPage } from './features/auth/LoginPage';

function App() {
  return (
    <Provider store={store}>
      <ChakraProvider>
        <Box minH="100vh" bg="gray.50">
          <LoginPage />
        </Box>
      </ChakraProvider>
    </Provider>
  );
}

export default App;
