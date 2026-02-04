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
} from '@chakra-ui/react';
import { ExternalLinkIcon } from '@chakra-ui/icons';
import { NewsItem } from '../../types';

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
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
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
                {item.processed && <Badge colorScheme="green">Processed</Badge>}
                {item.result !== null && (
                  <Badge colorScheme={item.result ? 'green' : 'red'}>
                    Result: {item.result ? 'True' : 'False'}
                  </Badge>
                )}
              </HStack>
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
                    Processed At:
                  </Text>
                  <Text>{formatDate(item.processed_at)}</Text>
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

            {item.ai_response && (
              <>
                <Divider />
                {renderJson(item.ai_response, 'AI Response')}
              </>
            )}

            {item.settings && (
              <>
                <Divider />
                {renderJson(item.settings, 'Settings')}
              </>
            )}

            {item.raw_data && (
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
