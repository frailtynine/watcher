import {
  Box,
  Button,
  Heading,
  HStack,
  VStack,
  useDisclosure,
  useToast,
  Spinner,
  Center,
  Text,
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import { useState } from 'react';
import { NewsTaskCard } from './NewsTaskCard';
import { CreateNewsTaskModal } from './CreateNewsTaskModal';
import { EditNewsTaskModal } from './EditNewsTaskModal';
import {
  useGetNewsTasksQuery,
  useUpdateNewsTaskMutation,
  useDeleteNewsTaskMutation,
} from '../../services/api';
import type { NewsTask } from '../../types';

export const NewsTasks = () => {
  const { data, isLoading } = useGetNewsTasksQuery();
  const [updateTask] = useUpdateNewsTaskMutation();
  const [deleteTask] = useDeleteNewsTaskMutation();
  const toast = useToast();

  const [selectedTask, setSelectedTask] = useState<NewsTask | null>(null);
  const createModal = useDisclosure();
  const editModal = useDisclosure();

  const handleToggleActive = async (id: string, active: boolean) => {
    try {
      await updateTask({ id, data: { active } }).unwrap();
      toast({
        title: active ? 'Task resumed' : 'Task paused',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Failed to update task',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleEdit = (task: NewsTask) => {
    setSelectedTask(task);
    editModal.onOpen();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this task?')) {
      return;
    }

    try {
      await deleteTask(id).unwrap();
      toast({
        title: 'Task deleted',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Failed to delete task',
        status: 'error',
        duration: 3000,
      });
    }
  };

  if (isLoading) {
    return (
      <Center h="400px">
        <Spinner size="xl" />
      </Center>
    );
  }

  const tasks = data || [];

  return (
    <Box>
      <HStack justify="space-between" mb={6}>
        <Heading size="lg">My News Tasks</Heading>
        <Button
          leftIcon={<AddIcon />}
          colorScheme="blue"
          onClick={createModal.onOpen}
        >
          New Task
        </Button>
      </HStack>

      {tasks.length === 0 ? (
        <Center
          p={12}
          bg="white"
          borderRadius="md"
          borderWidth="1px"
          borderStyle="dashed"
        >
          <VStack spacing={4}>
            <Text fontSize="lg" color="gray.500">
              No news tasks yet
            </Text>
            <Text color="gray.400">
              Create your first task to start monitoring news
            </Text>
            <Button
              leftIcon={<AddIcon />}
              colorScheme="blue"
              onClick={createModal.onOpen}
            >
              Create News Task
            </Button>
          </VStack>
        </Center>
      ) : (
        <VStack spacing={4} align="stretch">
          {tasks.map((task) => (
            <NewsTaskCard
              key={task.id}
              task={task}
              sourcesCount={task.sources_count}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onToggleActive={handleToggleActive}
            />
          ))}
        </VStack>
      )}

      <CreateNewsTaskModal
        isOpen={createModal.isOpen}
        onClose={createModal.onClose}
      />

      {selectedTask && (
        <EditNewsTaskModal
          isOpen={editModal.isOpen}
          onClose={() => {
            editModal.onClose();
            setSelectedTask(null);
          }}
          task={selectedTask}
        />
      )}
    </Box>
  );
};
