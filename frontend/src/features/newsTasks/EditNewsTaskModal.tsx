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
  HStack,
  Divider,
  Heading,
  Badge,
  useToast,
  FormErrorMessage,
  useDisclosure,
  Box,
  Text,
  SimpleGrid,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import { useState, useEffect, useMemo } from 'react';
import {
  useUpdateNewsTaskMutation,
  useGetTaskSourcesQuery,
  useGetSourcesQuery,
  usePreviewNewsTaskMutation,
} from '../../services/api';
import {
  DEFAULT_TELEGRAM_SUMMARY_PROMPT,
  createDefaultNewsTaskSettings,
  type NewsTask,
  type NewsTaskPreview,
  type NewsTaskSettings,
} from '../../types';
import { SourcesList } from '../sources/SourcesList';
import { AddSourceModal } from '../sources/AddSourceModal';
import { TaskBotsManager } from './TaskBotsManager';
import { TaskDeliverySettings } from './TaskDeliverySettings';

interface EditNewsTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: NewsTask;
}

export const EditNewsTaskModal = ({
  isOpen,
  onClose,
  task,
}: EditNewsTaskModalProps) => {
  const [updateTask, { isLoading }] = useUpdateNewsTaskMutation();
  const [previewTask, { isLoading: isPreviewLoading }] =
    usePreviewNewsTaskMutation();
  const { data: associations } = useGetTaskSourcesQuery(task.id);
  const { data: allSources } = useGetSourcesQuery();
  const toast = useToast();

  const addSourceModal = useDisclosure();

  const [name, setName] = useState(task.name);
  const [prompt, setPrompt] = useState(task.prompt);
  const [settings, setSettings] = useState<NewsTaskSettings>(
    task.settings || createDefaultNewsTaskSettings()
  );
  const [errors, setErrors] = useState<{
    name?: string;
    prompt?: string;
    settingsLang?: string;
  }>({});
  const [preview, setPreview] = useState<NewsTaskPreview | null>(null);

  useEffect(() => {
    setName(task.name);
    setPrompt(task.prompt);
    setSettings(task.settings || createDefaultNewsTaskSettings());
    setPreview(null);
  }, [task]);

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

    if (!settings.delivery.telegram.lang.trim()) {
      newErrors.settingsLang = 'Telegram language is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      return;
    }

    try {
      await updateTask({
        id: task.id,
        data: {
          name: name.trim(),
          prompt: prompt.trim(),
          settings: {
            treshold: settings.treshold,
            delivery: {
              telegram: {
                summary: settings.delivery.telegram.summary,
                lang: settings.delivery.telegram.lang.trim(),
                prompt:
                  settings.delivery.telegram.prompt.trim() ||
                  DEFAULT_TELEGRAM_SUMMARY_PROMPT,
              },
            },
          },
        },
      }).unwrap();

      toast({
        title: 'Task updated',
        status: 'success',
        duration: 2000,
      });

      onClose();
    } catch (error) {
      toast({
        title: 'Failed to update task',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handlePreview = async () => {
    if (!prompt.trim()) {
      setErrors((current) => ({
        ...current,
        prompt: 'AI prompt is required to test the task',
      }));
      return;
    }

    setPreview(null);
    try {
      setPreview(
        await previewTask({
          taskId: task.id,
          prompt: prompt.trim(),
          treshold: settings.treshold,
        }).unwrap()
      );
    } catch {
      toast({
        title: 'Failed to test task',
        description: 'Could not fetch and classify recent RSS items.',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const sources = useMemo(() => {
    if (!associations || !allSources) return [];
    const sourceIds = associations.map((a) => a.source_id);
    return allSources.filter((s) => sourceIds.includes(Number(s.id)));
  }, [associations, allSources]);

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} size="2xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Edit: {task.name}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={6} align="stretch">
              <VStack spacing={4}>
                <FormControl isInvalid={!!errors.name} isRequired>
                  <FormLabel>Task Name</FormLabel>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <FormErrorMessage>{errors.name}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.prompt} isRequired>
                  <FormLabel>AI Prompt</FormLabel>
                  <Textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                  />
                  <FormErrorMessage>{errors.prompt}</FormErrorMessage>
                </FormControl>

                <FormControl>
                  <FormLabel>
                    Relevance treshold: {settings.treshold.toFixed(2)}
                  </FormLabel>
                  <Slider
                    value={settings.treshold}
                    min={0}
                    max={1}
                    step={0.05}
                    onChange={(treshold) =>
                      setSettings((current) => ({ ...current, treshold }))
                    }
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                </FormControl>

                <FormControl isInvalid={!!errors.settingsLang} isRequired>
                  <FormLabel>Delivery Settings</FormLabel>
                  <TaskDeliverySettings
                    settings={settings}
                    onChange={setSettings}
                  />
                  <FormErrorMessage>{errors.settingsLang}</FormErrorMessage>
                </FormControl>
              </VStack>

              <Divider />

              <Box>
                <HStack justify="space-between" mb={4}>
                  <Heading size="sm">
                    RSS Feeds ({sources.length})
                  </Heading>
                  <Button
                    leftIcon={<AddIcon />}
                    size="sm"
                    colorScheme="blue"
                    onClick={addSourceModal.onOpen}
                  >
                    Add Feed
                  </Button>
                </HStack>

                {sources.length === 0 ? (
                  <Box
                    p={6}
                    bg="gray.50"
                    borderRadius="md"
                    textAlign="center"
                  >
                    <Text color="gray.500" fontSize="sm">
                      No RSS feeds added yet
                    </Text>
                  </Box>
                ) : (
                  <SourcesList sources={sources} taskId={task.id} />
                )}
              </Box>

              <Divider />

              <Box>
                <HStack justify="space-between" mb={4} align="center">
                  <Box>
                    <Heading size="sm">Task Test</Heading>
                    <Text fontSize="sm" color="gray.500">
                      Classify recent RSS items without saving them.
                    </Text>
                  </Box>
                  <Button
                    size="sm"
                    colorScheme="purple"
                    onClick={handlePreview}
                    isLoading={isPreviewLoading}
                  >
                    Test Task
                  </Button>
                </HStack>

                {preview && (
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                    <PreviewResults
                      title="Relevant"
                      colorScheme="green"
                      items={preview.relevant}
                    />
                    <PreviewResults
                      title="Not Relevant"
                      colorScheme="gray"
                      items={preview.non_relevant}
                    />
                  </SimpleGrid>
                )}
              </Box>

              <Divider />

              <Box>
                <Heading size="sm" mb={4}>
                  Telegram Bots
                </Heading>
                <TaskBotsManager taskId={task.id} />
              </Box>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSubmit}
              isLoading={isLoading}
            >
              Save Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      <AddSourceModal
        isOpen={addSourceModal.isOpen}
        onClose={addSourceModal.onClose}
        taskId={task.id}
      />
    </>
  );
};

function PreviewResults({
  title,
  colorScheme,
  items,
}: {
  title: string;
  colorScheme: string;
  items: NewsTaskPreview['relevant'];
}) {
  return (
    <Box flex={1} minW={0}>
      <Heading size="xs" mb={2} color={`${colorScheme}.600`}>
        {title} ({items.length})
      </Heading>
      <VStack align="stretch" spacing={2}>
        {items.length === 0 ? (
          <Text fontSize="sm" color="gray.500">No items found</Text>
        ) : (
          items.map((item) => (
            <Box
              key={`${item.title}-${item.decision}`}
              p={3}
              bg="gray.50"
              borderRadius="md"
            >
              <HStack justify="space-between" align="start" mb={1}>
                <Text fontWeight="medium" fontSize="sm" noOfLines={2}>
                  {item.title}
                </Text>
                <Badge colorScheme={colorScheme} flexShrink={0}>
                  {(item.decision * 100).toFixed(0)}%
                </Badge>
              </HStack>
              <Text fontSize="xs" color="gray.600" noOfLines={3}>
                {item.description}
              </Text>
            </Box>
          ))
        )}
      </VStack>
    </Box>
  );
}
