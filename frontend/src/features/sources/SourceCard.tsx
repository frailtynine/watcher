import {
  Box,
  HStack,
  Text,
  IconButton,
  useToast,
  Badge,
} from '@chakra-ui/react';
import { DeleteIcon, LinkIcon } from '@chakra-ui/icons';
import {
  useDisassociateSourceFromTaskMutation,
} from '../../services/api';
import type { Source } from '../../types';

interface SourceCardProps {
  source: Source;
  taskId: string;
}

export const SourceCard = ({ source, taskId }: SourceCardProps) => {
  const [disassociate] = useDisassociateSourceFromTaskMutation();
  const toast = useToast();

  const handleRemove = async () => {
    if (!confirm('Remove this source from the task?')) {
      return;
    }

    try {
      await disassociate({
        sourceId: source.id,
        taskId,
      }).unwrap();

      toast({
        title: 'Source removed',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Failed to remove source',
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
          <LinkIcon boxSize={4} color="gray.500" />

          <Box flex="1">
            <HStack spacing={2}>
              <Text fontWeight="medium" fontSize="sm">
                {source.name}
              </Text>
              <Badge
                colorScheme={source.type === 'RSS' ? 'blue' : 'purple'}
                fontSize="xs"
              >
                {source.type}
              </Badge>
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
