import { Box, Flex, Container } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export const DashboardLayout = () => {
  return (
    <Flex direction="column" minH="100vh">
      <Navbar />
      <Box flex="1" bg="gray.50" py={8}>
        <Container maxW="container.xl">
          <Outlet />
        </Container>
      </Box>
    </Flex>
  );
};
