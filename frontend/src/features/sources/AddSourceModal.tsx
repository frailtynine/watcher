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
  VStack,
  useToast,
  FormErrorMessage,
  Text,
  Box,
  List,
  ListItem,
  Spinner,
  HStack,
  IconButton,
  Divider,
  RadioGroup,
  Radio,
  Stack,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { CloseIcon } from '@chakra-ui/icons';
import {
  useCreateSourceMutation,
  useAssociateSourceWithTaskMutation,
  useLazySearchSourcesQuery,
} from '../../services/api';
import type { Source } from '../../types';

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string;
}

type SourceType = 'RSS' | 'Telegram';

const isValidRSSUrl = (url: string): boolean => {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
};

const isValidTelegramChannel = (channel: string): boolean => {
  // Telegram channels can be:
  // - Username format: @channelname or channelname
  // - Numeric ID: -1001234567890
  if (!channel.trim()) return false;
  
  const trimmed = channel.trim();
  
  // Numeric ID format
  if (/^-?\d+$/.test(trimmed)) return true;
  
  // Username format (with or without @)
  const username = trimmed.startsWith('@') ? trimmed.slice(1) : trimmed;
  return /^[a-zA-Z0-9_]{5,32}$/.test(username);
};

export const AddSourceModal = ({
  isOpen,
  onClose,
  taskId,
}: AddSourceModalProps) => {
  const [createSource, { isLoading: isCreating }] =
    useCreateSourceMutation();
  const [associate, { isLoading: isAssociating }] =
    useAssociateSourceWithTaskMutation();
  const [searchSources, { data: searchResults, isFetching }] =
    useLazySearchSourcesQuery();
  const toast = useToast();

  const [sourceType, setSourceType] = useState<SourceType>('RSS');
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(true);
  const [selectedSource, setSelectedSource] = useState<Source | null>(
    null
  );
  const [errors, setErrors] = useState<{
    name?: string;
    url?: string;
  }>({});

  useEffect(() => {
    if (searchQuery.trim().length >= 2) {
      const timer = setTimeout(() => {
        searchSources(searchQuery);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [searchQuery, searchSources]);

  const validate = () => {
    const newErrors: typeof errors = {};

    if (!name.trim()) {
      newErrors.name = `${sourceType} name is required`;
    } else if (name.length < 3) {
      newErrors.name = 'Name must be at least 3 characters';
    } else if (name.length > 100) {
      newErrors.name = 'Name must be less than 100 characters';
    }

    if (sourceType === 'RSS') {
      if (!url.trim()) {
        newErrors.url = 'RSS feed URL is required';
      } else if (!isValidRSSUrl(url.trim())) {
        newErrors.url = 'Please enter a valid HTTP or HTTPS URL';
      }
    } else {
      // Telegram validation
      if (!url.trim()) {
        newErrors.url = 'Telegram channel is required';
      } else if (!isValidTelegramChannel(url.trim())) {
        newErrors.url = 'Please enter a valid Telegram channel username or ID';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (selectedSource) {
      // Associate existing source
      try {
        await associate({
          source_id: Number(selectedSource.id),
          news_task_id: Number(taskId),
        }).unwrap();

        toast({
          title: `${selectedSource.type} source added`,
          status: 'success',
          duration: 2000,
        });

        handleClose();
      } catch (error) {
        toast({
          title: 'Failed to add source',
          description: 'Please try again',
          status: 'error',
          duration: 3000,
        });
      }
    } else {
      // Create new source
      if (!validate()) {
        return;
      }

      try {
        // For Telegram, normalize the channel identifier
        let sourceValue = url.trim();
        if (sourceType === 'Telegram' && sourceValue.startsWith('@')) {
          sourceValue = sourceValue.slice(1);
        }

        const result = await createSource({
          name: name.trim(),
          source: sourceValue,
          type: sourceType,
          active: true,
        }).unwrap();

        await associate({
          source_id: Number(result.id),
          news_task_id: Number(taskId),
        }).unwrap();

        toast({
          title: `${sourceType} source added`,
          status: 'success',
          duration: 2000,
        });

        handleClose();
      } catch (error) {
        toast({
          title: 'Failed to add source',
          description: 'Please try again',
          status: 'error',
          duration: 3000,
        });
      }
    }
  };

  const handleClose = () => {
    setSourceType('RSS');
    setName('');
    setUrl('');
    setSearchQuery('');
    setShowSearch(true);
    setSelectedSource(null);
    setErrors({});
    onClose();
  };

  const handleSelectSource = (source: Source) => {
    setSelectedSource(source);
    setShowSearch(false);
    setSearchQuery('');
  };

  const handleCreateNew = () => {
    setShowSearch(false);
    setSelectedSource(null);
  };

  const isLoading = isCreating || isAssociating;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Add Source</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4} align="stretch">
            {/* Source Type Selection */}
            {!showSearch && !selectedSource && (
              <FormControl>
                <FormLabel>Source Type</FormLabel>
                <RadioGroup
                  value={sourceType}
                  onChange={(value) => {
                    setSourceType(value as SourceType);
                    setUrl('');
                    setErrors({});
                  }}
                >
                  <Stack direction="row" spacing={4}>
                    <Radio value="RSS">RSS Feed</Radio>
                    <Radio value="Telegram">Telegram Channel</Radio>
                  </Stack>
                </RadioGroup>
              </FormControl>
            )}

            {showSearch && !selectedSource && (
              <>
                <FormControl>
                  <FormLabel>Search Existing Sources</FormLabel>
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by name or URL..."
                  />
                </FormControl>

                {isFetching && (
                  <Box textAlign="center" py={4}>
                    <Spinner size="sm" />
                  </Box>
                )}

                {searchResults && searchResults.length > 0 && (
                  <Box
                    maxH="200px"
                    overflowY="auto"
                    borderWidth="1px"
                    borderRadius="md"
                    p={2}
                  >
                    <List spacing={2}>
                      {searchResults.map((source) => (
                        <ListItem
                          key={source.id}
                          p={2}
                          borderRadius="md"
                          cursor="pointer"
                          _hover={{ bg: 'gray.50' }}
                          onClick={() => handleSelectSource(source)}
                        >
                          <HStack justify="space-between">
                            <Box flex="1">
                              <Text fontWeight="medium">{source.name}</Text>
                              <Text fontSize="sm" color="gray.600" noOfLines={1}>
                                {source.source}
                              </Text>
                            </Box>
                            <Text fontSize="xs" color="gray.500" fontWeight="medium">
                              {source.type}
                            </Text>
                          </HStack>
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {searchQuery.trim().length >= 2 &&
                  !isFetching &&
                  searchResults?.length === 0 && (
                    <Text fontSize="sm" color="gray.500" textAlign="center">
                      No existing sources found
                    </Text>
                  )}

                <Divider />

                <Button
                  variant="outline"
                  onClick={handleCreateNew}
                  size="sm"
                >
                  Create New Source
                </Button>
              </>
            )}

            {selectedSource && (
              <Box
                p={4}
                borderWidth="1px"
                borderRadius="md"
                bg="blue.50"
              >
                <HStack justify="space-between">
                  <Box>
                    <Text fontWeight="medium">{selectedSource.name}</Text>
                    <Text fontSize="sm" color="gray.600">
                      {selectedSource.source}
                    </Text>
                  </Box>
                  <IconButton
                    aria-label="Clear selection"
                    icon={<CloseIcon />}
                    size="sm"
                    onClick={() => {
                      setSelectedSource(null);
                      setShowSearch(true);
                    }}
                  />
                </HStack>
              </Box>
            )}

            {!showSearch && !selectedSource && (
              <>
                <FormControl isInvalid={!!errors.name} isRequired>
                  <FormLabel>
                    {sourceType === 'RSS' ? 'Feed Name' : 'Channel Name'}
                  </FormLabel>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={
                      sourceType === 'RSS'
                        ? 'e.g., TechCrunch Startups'
                        : 'e.g., Tech News Channel'
                    }
                  />
                  <FormErrorMessage>{errors.name}</FormErrorMessage>
                </FormControl>

                <FormControl isInvalid={!!errors.url} isRequired>
                  <FormLabel>
                    {sourceType === 'RSS'
                      ? 'RSS Feed URL'
                      : 'Telegram Channel'}
                  </FormLabel>
                  <Input
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder={
                      sourceType === 'RSS'
                        ? 'https://example.com/feed.xml'
                        : '@channelname or -1001234567890'
                    }
                    type={sourceType === 'RSS' ? 'url' : 'text'}
                  />
                  {sourceType === 'Telegram' && !errors.url && (
                    <Text fontSize="xs" color="gray.500" mt={1}>
                      Enter channel username (with or without @) or numeric ID
                    </Text>
                  )}
                  <FormErrorMessage>{errors.url}</FormErrorMessage>
                </FormControl>

                <Button
                  variant="link"
                  onClick={() => setShowSearch(true)}
                  size="sm"
                >
                  ← Back to Search
                </Button>
              </>
            )}
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
            isDisabled={!selectedSource && (!name || !url)}
          >
            {selectedSource ? 'Add Source' : 'Create & Add Source'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
