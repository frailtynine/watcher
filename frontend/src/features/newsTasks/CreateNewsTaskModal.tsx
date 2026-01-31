import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
  useToast,
  FormErrorMessage,
} from '@chakra-ui/react';
import { useState } from 'react';
import { useCreateNewsTaskMutation } from '../../services/api';

interface CreateNewsTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateNewsTaskModal = ({
  isOpen,
  onClose,
}: CreateNewsTaskModalProps) => {
  const [createTask, { isLoading }] = useCreateNewsTaskMutation();
  const toast = useToast();

  const [name, setName] = useState('');
  const [prompt, setPrompt] = useState('');
  const [errors, setErrors] = useState<{
    name?: string;
    prompt?: string;
  }>({});

  const validate = () => {
    const newErrors: typeof errors = {};

    if (!name.trim()) {
      newErrors.name = 'Task name is required';
    } else if (name.length < 3) {
      newErrors.name = 'Task name must be at least 3 characters';
    } else if (name.length > 100) {
      newErrors.name = 'Task name must be less than 100 characters';
    }

    if (!prompt.trim()) {
      newErrors.prompt = 'AI prompt is required';
    } else if (prompt.length < 10) {
      newErrors.prompt = 'Prompt must be at least 10 characters';
    } else if (prompt.length > 1000) {
      newErrors.prompt = 'Prompt must be less than 1000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      return;
    }

    try {
      await createTask({
        name: name.trim(),
        prompt: prompt.trim(),
        active: true,
      }).unwrap();

      toast({
        title: 'News task created',
        status: 'success',
        duration: 2000,
      });

      setName('');
      setPrompt('');
      setErrors({});
      onClose();
    } catch (error) {
      toast({
        title: 'Failed to create task',
        description: 'Please try again',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleClose = () => {
    setName('');
    setPrompt('');
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Create News Task</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl isInvalid={!!errors.name} isRequired>
              <FormLabel>Task Name</FormLabel>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Tech Startup News"
              />
              <FormErrorMessage>{errors.name}</FormErrorMessage>
            </FormControl>

            <FormControl isInvalid={!!errors.prompt} isRequired>
              <FormLabel>AI Prompt</FormLabel>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe what news you're looking for..."
                rows={4}
              />
              <FormErrorMessage>{errors.prompt}</FormErrorMessage>
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={handleClose}>
            Cancel
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleSubmit}
            isLoading={isLoading}
          >
            Create Task
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
