import {
  Box,
  Flex,
  Heading,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Avatar,
  HStack,
  Text,
  Badge,
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  useGetCurrentUserQuery,
  useLogoutMutation,
} from '../../services/api';

export const Navbar = () => {
  const navigate = useNavigate();
  const { data: user } = useGetCurrentUserQuery();
  const [logout] = useLogoutMutation();

  const handleLogout = async () => {
    try {
      await logout().unwrap();
      localStorage.removeItem('access_token');
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      localStorage.removeItem('access_token');
      navigate('/login');
    }
  };

  return (
    <Box bg="white" px={4} shadow="sm" borderBottomWidth="1px">
      <Flex
        h={16}
        alignItems="center"
        justifyContent="space-between"
        maxW="container.xl"
        mx="auto"
      >
        <HStack spacing={8}>
          <Heading size="md" color="blue.600">
            NewsWatcher
          </Heading>

          <HStack spacing={4}>
            <Button
              as={RouterLink}
              to="/tasks"
              variant="ghost"
              size="sm"
            >
              News Tasks
            </Button>
            <Button
              as={RouterLink}
              to="/news-items"
              variant="ghost"
              size="sm"
            >
              <Badge colorScheme="orange" mr={2}>
                DEBUG
              </Badge>
              News Items
            </Button>
          </HStack>
        </HStack>

        <HStack spacing={4}>
          <Menu>
            <MenuButton
              as={Button}
              rightIcon={<ChevronDownIcon />}
              variant="ghost"
            >
              <HStack>
                <Avatar size="sm" name={user?.email} />
                <Text fontSize="sm">{user?.email}</Text>
              </HStack>
            </MenuButton>
            <MenuList>
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
    </Box>
  );
};
