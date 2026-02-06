import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  VStack,
  Box,
  Text,
  Link,
  Badge,
  Heading,
  Divider,
  Code,
  HStack,
  Spinner,
  Alert,
  AlertIcon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '@chakra-ui/react';
import { ExternalLinkIcon } from '@chakra-ui/icons';
import { NewsItem } from '../../types';
import { useGetNewsItemResultsQuery, useGetNewsTasksQuery } from '../../services/api';

interface NewsItemDetailProps {
  item: NewsItem;
  sourceName: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function NewsItemDetail({
  item,
  sourceName,
  isOpen,
  onClose,
}: NewsItemDetailProps) {
  const { data: results, isLoading: resultsLoading } = useGetNewsItemResultsQuery(item.id);
  const { data: tasks } = useGetNewsTasksQuery();

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getTaskName = (taskId: number) => {
    const task = tasks?.find((t) => Number(t.id) === taskId);
    return task?.name || `Task #${taskId}`;
  };

  const renderJson = (data: any, label: string) => {
    if (!data) return null;
    return (
      <Box>
        <Heading size="sm" mb={2}>
          {label}
        </Heading>
        <Code
          display="block"
          whiteSpace="pre"
          p={3}
          borderRadius="md"
          fontSize="xs"
          overflowX="auto"
        >
          {JSON.stringify(data, null, 2)}
        </Code>
      </Box>
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="3xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>News Item #{item.id}</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack spacing={4} align="stretch">
            <Box>
              <Heading size="md" mb={2}>
                {item.title || '(No title)'}
              </Heading>
              <HStack spacing={2} mb={2}>
                <Badge colorScheme="blue">{sourceName}</Badge>
              </HStack>
            </Box>

            <Divider />

            {/* Processing Results Section */}
            <Box>
              <Heading size="sm" mb={3}>
                Processing Results
              </Heading>
              {resultsLoading && <Spinner size="sm" />}
              {results && results.length === 0 && (
                <Alert status="info">
                  <AlertIcon />
                  Not processed by any tasks yet
                </Alert>
              )}
              {results && results.length > 0 && (
                <Table size="sm" variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Task</Th>
                      <Th>Processed</Th>
                      <Th>Result</Th>
                      <Th>Processed At</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {results.map((result) => (
                      <Tr key={result.news_task_id}>
                        <Td>{getTaskName(result.news_task_id)}</Td>
                        <Td>
                          {result.processed ? (
                            <Badge colorScheme="green">Yes</Badge>
                          ) : (
                            <Badge colorScheme="gray">No</Badge>
                          )}
                        </Td>
                        <Td>
                          {result.result === null ? (
                            <Badge>-</Badge>
                          ) : result.result ? (
                            <Badge colorScheme="green">✓ Relevant</Badge>
                          ) : (
                            <Badge colorScheme="red">✗ Not Relevant</Badge>
                          )}
                        </Td>
                        <Td fontSize="xs">{formatDate(result.processed_at)}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              )}
            </Box>

            <Divider />

            {item.url && (
              <Box>
                <Text fontWeight="semibold" mb={1}>
                  URL
                </Text>
                <Link href={item.url} isExternal color="blue.500">
                  {item.url} <ExternalLinkIcon mx="2px" />
                </Link>
              </Box>
            )}

            {item.content && (
              <Box>
                <Text fontWeight="semibold" mb={1}>
                  Content
                </Text>
                <Text whiteSpace="pre-wrap">{item.content}</Text>
              </Box>
            )}

            <Box>
              <Text fontWeight="semibold" mb={1}>
                Details
              </Text>
              <VStack align="stretch" spacing={1} fontSize="sm">
                <HStack>
                  <Text fontWeight="medium" width="150px">
                    External ID:
                  </Text>
                  <Text>{item.external_id || 'N/A'}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="medium" width="150px">
                    Published:
                  </Text>
                  <Text>{formatDate(item.published_at)}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="medium" width="150px">
                    Fetched:
                  </Text>
                  <Text>{formatDate(item.fetched_at)}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="medium" width="150px">
                    Created:
                  </Text>
                  <Text>{formatDate(item.created_at)}</Text>
                </HStack>
                <HStack>
                  <Text fontWeight="medium" width="150px">
                    Updated:
                  </Text>
                  <Text>{formatDate(item.updated_at)}</Text>
                </HStack>
              </VStack>
            </Box>

            {/* AI Responses from each task */}
            {results && results.some((r) => r.ai_response) && (
              <>
                <Divider />
                <Box>
                  <Heading size="sm" mb={3}>
                    AI Responses
                  </Heading>
                  {results
                    .filter((r) => r.ai_response)
                    .map((result) => (
                      <Box key={result.news_task_id} mb={4}>
                        <Text fontWeight="semibold" mb={2}>
                          {getTaskName(result.news_task_id)}
                        </Text>
                        <Code
                          display="block"
                          whiteSpace="pre"
                          p={3}
                          borderRadius="md"
                          fontSize="xs"
                          overflowX="auto"
                        >
                          {JSON.stringify(result.ai_response, null, 2)}
                        </Code>
                      </Box>
                    ))}
                </Box>
              </>
            )}

            {item.settings && Object.keys(item.settings).length > 0 && (
              <>
                <Divider />
                {renderJson(item.settings, 'Settings')}
              </>
            )}

            {item.raw_data && Object.keys(item.raw_data).length > 0 && (
              <>
                <Divider />
                {renderJson(item.raw_data, 'Raw Data')}
              </>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
}
