import { Navigate } from 'react-router-dom';
import { useGetCurrentUserQuery } from '../services/api';
import { Center, Spinner } from '@chakra-ui/react';

interface PrivateRouteProps {
  children: React.ReactNode;
}

export const PrivateRoute = ({ children }: PrivateRouteProps) => {
  const { isLoading, isError } = useGetCurrentUserQuery();

  if (isLoading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  if (isError) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
