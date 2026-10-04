import { ChakraProvider } from '@chakra-ui/react';
import { Provider } from 'react-redux';
import {
  BrowserRouter,
  Routes,
  Route,
} from 'react-router-dom';
import { store } from './store';
import { LoginPage } from './features/auth/LoginPage';
import { DashboardLayout } from './components/Layout/DashboardLayout';
import { NewsTasks } from './features/newsTasks/NewsTasks';
import NewsItemsPage from './features/newsItems/NewsItemsPage';
import { SettingsPage } from './features/settings/SettingsPage';
import { AIDeduplicationDebugPage } from './features/debug/AIDeduplicationDebugPage';
import { PrivateRoute } from './components/PrivateRoute';

// SignupPage is kept in the codebase in case public signup is re-enabled.
// import { SignupPage } from './features/auth/SignupPage';

function App() {
  return (
    <Provider store={store}>
      <ChakraProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            {/* Public signup route intentionally disabled for now.
                Re-enable when the backend register endpoint returns. */}
            {/* <Route path="/signup" element={<SignupPage />} /> */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <DashboardLayout />
                </PrivateRoute>
              }
            >
              <Route path="tasks" element={<NewsTasks />} />
              <Route path="news-items" element={<NewsItemsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="debug/ai-dedup" element={<AIDeduplicationDebugPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ChakraProvider>
    </Provider>
  );
}

export default App;
