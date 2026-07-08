import { useMemo, useState } from 'react';
import {
  Alert,
  AlertDescription,
  AlertIcon,
  Badge,
  Box,
  Button,
  Checkbox,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Select,
  Text,
  Textarea,
  VStack,
  useToast,
} from '@chakra-ui/react';
import {
  useDebugDeduplicationMutation,
  useGetNewsTasksQuery,
} from '../../services/api';


const splitHeadlines = (value: string): string[] =>
  value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);


const extractErrorMessage = (error: unknown): string => {
  if (!error || typeof error !== 'object') {
    return 'Failed to run deduplication test';
  }
  if ('data' in error && error.data && typeof error.data === 'object') {
    const data = error.data as { detail?: unknown };
    if (typeof data.detail === 'string') {
      return data.detail;
    }
  }
  return 'Failed to run deduplication test';
};


export const AIDeduplicationDebugPage = () => {
  const toast = useToast();
  const [candidateTitle, setCandidateTitle] = useState('');
  const [candidateContent, setCandidateContent] = useState('');
  const [headlinesText, setHeadlinesText] = useState('');
  const [useTaskContext, setUseTaskContext] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const [cutoffHours, setCutoffHours] = useState<24 | 48 | 72 | 168>(24);
  const { data: tasks = [], isLoading: isLoadingTasks } = useGetNewsTasksQuery();
  const [debugDeduplication, { data, isLoading }] =
    useDebugDeduplicationMutation();

  const headlinesCount = useMemo(
    () => splitHeadlines(headlinesText).length,
    [headlinesText],
  );

  const canRun =
    candidateTitle.trim().length > 0
    && candidateContent.trim().length > 0
    && (
      useTaskContext
      ? selectedTaskId.trim().length > 0
      : splitHeadlines(headlinesText).length > 0
    );

  const handleRun = async () => {
    const taskId = Number(selectedTaskId);
    try {
      await debugDeduplication({
        candidate_title: candidateTitle.trim(),
        candidate_content: candidateContent.trim(),
        recent_headlines: useTaskContext
          ? []
          : splitHeadlines(headlinesText),
        use_task_context: useTaskContext,
        cutoff_hours: cutoffHours,
        task_id: useTaskContext && Number.isFinite(taskId)
          ? taskId
          : undefined,
      }).unwrap();
    } catch (error: unknown) {
      toast({
        title: 'Deduplication test failed',
        description: extractErrorMessage(error),
        status: 'error',
        duration: 4000,
        isClosable: true,
      });
    }
  };

  return (
    <Box maxW="5xl">
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg" mb={2}>
            AI Deduplication Debug
          </Heading>
          <Text color="gray.600">
            Test whether Gemini treats a relevant item as new or duplicate.
          </Text>
        </Box>

        <Alert status="warning" borderRadius="md">
          <AlertIcon />
          <AlertDescription>
            Debug tool for authenticated users. Each run uses your Gemini key.
          </AlertDescription>
        </Alert>

        <Box bg="white" borderRadius="lg" boxShadow="sm" p={6}>
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel>Candidate Title</FormLabel>
              <Input
                value={candidateTitle}
                onChange={(e) => setCandidateTitle(e.target.value)}
                placeholder="Title of relevant item to test"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Candidate Content</FormLabel>
              <Textarea
                value={candidateContent}
                onChange={(e) => setCandidateContent(e.target.value)}
                rows={8}
                placeholder="Content/body used to decide if this is same event"
              />
            </FormControl>

            <Checkbox
              isChecked={useTaskContext}
              onChange={(e) => setUseTaskContext(e.target.checked)}
            >
              Load recent relevant headlines from task context
            </Checkbox>

            {useTaskContext ? (
              <FormControl>
                <FormLabel>Task</FormLabel>
                <Select
                  placeholder={
                    isLoadingTasks ? 'Loading tasks...' : 'Select task'
                  }
                  value={selectedTaskId}
                  onChange={(e) => setSelectedTaskId(e.target.value)}
                  isDisabled={isLoadingTasks || tasks.length === 0}
                >
                  {tasks.map((task) => (
                    <option key={task.id} value={task.id}>
                      {task.name}
                    </option>
                  ))}
                </Select>
                {tasks.length === 0 && !isLoadingTasks ? (
                  <Text mt={1} fontSize="sm" color="gray.500">
                    No tasks found. Create a task first to use DB context.
                  </Text>
                ) : null}
              </FormControl>
            ) : (
              <FormControl>
                <FormLabel>Recent Relevant Headlines (one per line)</FormLabel>
                <Textarea
                  value={headlinesText}
                  onChange={(e) => setHeadlinesText(e.target.value)}
                  rows={10}
                  placeholder={
                    'Headline A\nHeadline B\nHeadline C'
                  }
                />
                <Text mt={1} fontSize="sm" color="gray.500">
                  {headlinesCount} headlines prepared
                </Text>
              </FormControl>
            )}

            <FormControl>
              <FormLabel>Recent Headlines Cutoff</FormLabel>
              <Select
                value={String(cutoffHours)}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (value === 24 || value === 48 || value === 72 || value === 168) {
                    setCutoffHours(value);
                  }
                }}
                isDisabled={!useTaskContext}
              >
                <option value="24">Last 24 hours</option>
                <option value="48">Last 48 hours</option>
                <option value="72">Last 72 hours</option>
                <option value="168">Last 7 days</option>
              </Select>
              <Text mt={1} fontSize="sm" color="gray.500">
                Applies when using task context.
              </Text>
            </FormControl>

            <Button
              alignSelf="flex-start"
              colorScheme="blue"
              onClick={handleRun}
              isLoading={isLoading}
              isDisabled={!canRun}
            >
              Run Deduplication Test
            </Button>
          </VStack>
        </Box>

        {data ? (
          <Box bg="white" borderRadius="lg" boxShadow="sm" p={6}>
            <VStack spacing={3} align="stretch">
              <Text>
                Result:{' '}
                <Badge colorScheme={data.is_new ? 'green' : 'orange'}>
                  {data.is_new ? 'NEW' : 'DUPLICATE'}
                </Badge>
              </Text>
              <Text fontSize="sm" color="gray.600">
                Headlines used: {data.headlines_used_count}
              </Text>
              <Box>
                <Text fontWeight="semibold" mb={1}>Reasoning</Text>
                <Text whiteSpace="pre-wrap">{data.thinking}</Text>
              </Box>
            </VStack>
          </Box>
        ) : null}
      </VStack>
    </Box>
  );
};
