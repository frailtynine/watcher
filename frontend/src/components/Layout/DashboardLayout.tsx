import { Box, Flex, Container } from '@chakra-ui/react';
import { Outlet, useLocation } from 'react-router-dom';
import { Navbar } from './Navbar';

export const DashboardLayout = () => {
  const location = useLocation();
  const isVideoEditorRoute = location.pathname.startsWith('/video-editor');

  return (
    <Flex direction="column" minH="100vh">
      <Navbar />
      <Box
        flex="1"
        minH={0}
        bg="gray.50"
        py={isVideoEditorRoute ? 0 : 8}
        overflow={isVideoEditorRoute ? 'hidden' : 'visible'}
      >
        {isVideoEditorRoute ? (
          <Box h="100%">
            <Outlet />
          </Box>
        ) : (
          <Container maxW="container.xl">
            <Outlet />
          </Container>
        )}
      </Box>
    </Flex>
  );
};
