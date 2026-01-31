import {
  Box,
  HStack,
  Text,
  IconButton,
  useToast,
  Tooltip,
} from '@chakra-ui/react';
import { DeleteIcon, LinkIcon } from '@chakra-ui/icons';
import { FaPlay, FaPause } from 'react-icons/fa';
import {
  useUpdateSourceMutation,
  useDisassociateSourceFromTaskMutation,
} from '../../services/api';
import type { Source } from '../../types';

interface SourceCardProps {
  source: Source;
  taskId: string;
}

export const SourceCard = ({ source, taskId }: SourceCardProps) => {
  const [updateSource] = useUpdateSourceMutation();
  const [disassociate] = useDisassociateSourceFromTaskMutation();
  const toast = useToast();

  const handleToggleActive = async () => {
    try {
      await updateSource({
        id: source.id,
        data: { active: !source.active },
      }).unwrap();

      toast({
        title: source.active ? 'Feed paused' : 'Feed resumed',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Failed to update feed',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleRemove = async () => {
    if (!confirm('Remove this feed from the task?')) {
      return;
    }

    try {
      await disassociate({
        sourceId: source.id,
        taskId,
      }).unwrap();

      toast({
        title: 'Feed removed',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Failed to remove feed',
        status: 'error',
        duration: 3000,
      });
    }
  };

  return (
    <Box
      p={3}
      bg="gray.50"
      borderRadius="md"
      borderWidth="1px"
      borderColor="gray.200"
    >
      <HStack justify="space-between">
        <HStack flex="1" spacing={3}>
          <Tooltip label={source.active ? 'Pause feed' : 'Resume feed'}>
            <IconButton
              aria-label={source.active ? 'Pause' : 'Play'}
              icon={source.active ? <FaPause /> : <FaPlay />}
              size="xs"
              colorScheme={source.active ? 'orange' : 'green'}
              onClick={handleToggleActive}
            />
          </Tooltip>

          <Box flex="1">
            <HStack>
              <LinkIcon boxSize={3} color="gray.500" />
              <Text fontWeight="medium" fontSize="sm">
                {source.name}
              </Text>
            </HStack>
            <Text fontSize="xs" color="gray.500" noOfLines={1}>
              {source.source}
            </Text>
            {source.last_fetched_at && (
              <Text fontSize="xs" color="gray.400">
                Last fetched:{' '}
                {new Date(source.last_fetched_at).toLocaleString()}
              </Text>
            )}
          </Box>
        </HStack>

        <IconButton
          aria-label="Remove"
          icon={<DeleteIcon />}
          size="xs"
          variant="ghost"
          colorScheme="red"
          onClick={handleRemove}
        />
      </HStack>
    </Box>
  );
};
