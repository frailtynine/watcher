import { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Image,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
  Text,
  VStack,
  useDisclosure,
  useToast,
} from '@chakra-ui/react';
import { commands, useEditorStore } from '@videoflow/react-video-editor';
import { usePreviewMediaMutation } from '../../services/api';
import type { DownloadPreviewItem } from '../../types';
import { useDownloadSingleMediaMutation } from '../../services/api';

const resolvePreviewUrl = (thumbnailUrl: string): string => {
  if (thumbnailUrl.startsWith('/api/')) {
    return `${window.location.protocol}//${window.location.hostname}${thumbnailUrl}`;
  }

  if (thumbnailUrl.startsWith('http://') || thumbnailUrl.startsWith('https://')) {
    try {
      const parsed = new URL(thumbnailUrl);
      if (parsed.pathname.startsWith('/api/')) {
        return `${window.location.protocol}//${window.location.hostname}${parsed.pathname}`;
      }
    } catch {
      return thumbnailUrl;
    }
  }

  return thumbnailUrl;
};

const IMAGE_EXTENSIONS = new Set([
  'jpg',
  'jpeg',
  'png',
  'webp',
  'gif',
  'bmp',
  'heic',
  'heif',
  'avif',
]);

const getLayerTypeFromUrl = (url: string): 'image' | 'video' => {
  const path = new URL(resolvePreviewUrl(url)).pathname;
  const fileName = path.split('/').pop() || '';
  const extension = fileName.includes('.')
    ? fileName.split('.').pop()!.toLowerCase()
    : '';

  if (IMAGE_EXTENSIONS.has(extension)) {
    return 'image';
  }
  return 'video';
};

const getLayerTypeForPreview = (item: DownloadPreviewItem): 'image' | 'video' => {
  if (item.media_type === 'image') {
    return 'image';
  }
  if (item.media_type === 'video') {
    return 'video';
  }
  if (item.thumbnail_url) {
    return getLayerTypeFromUrl(item.thumbnail_url);
  }
  return 'video';
};

const detectVideoDuration = async (source: string): Promise<number> => {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';

    const cleanup = () => {
      video.removeAttribute('src');
      video.load();
    };

    video.onloadedmetadata = () => {
      const duration = Number.isFinite(video.duration) ? video.duration : 0;
      cleanup();
      if (duration > 0) {
        resolve(duration);
      } else {
        reject(new Error('Unable to detect video duration'));
      }
    };

    video.onerror = () => {
      cleanup();
      reject(new Error('Failed to load video metadata'));
    };

    video.src = source;
  });
};

export const UpluadButton = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  const commit = useEditorStore((state) => state.commit);
  const activeGroupPath = useEditorStore((state) => state.activeGroupPath);
  const currentFrame = useEditorStore((state) => state.currentFrame);
  const editorVideo = useEditorStore((state) => state.video);
  const [link, setLink] = useState('');
  const [items, setItems] = useState<DownloadPreviewItem[]>([]);
  const [previewMedia, { isLoading }] = usePreviewMediaMutation();
  const [downloadSingleMedia, { isLoading: isDownloadingSingle }] = useDownloadSingleMediaMutation();
  const [activeMediaId, setActiveMediaId] = useState<number | null>(null);

  const extractErrorMessage = (error: unknown): string => {
    if (!error || typeof error !== 'object') {
      return 'Operation failed';
    }
    if ('data' in error && error.data && typeof error.data === 'object') {
      const data = error.data as { detail?: unknown };
      if (typeof data.detail === 'string') {
        return data.detail;
      }
    }
    if ('message' in error && typeof error.message === 'string') {
      return error.message;
    }
    return 'Operation failed';
  };

  const handlePreview = async () => {
    const data = await previewMedia({ link: link.trim() }).unwrap();
    setItems(data.items);
  };

  const handleChooseMedia = async (mediaId: number) => {
    setActiveMediaId(mediaId);
    try {
      const result = await downloadSingleMedia({
        link: link.trim(),
        media_id: mediaId,
      }).unwrap();

      const resolvedMediaUrl = resolvePreviewUrl(result.url);
      const selectedItem = items.find((item) => item.media_id === mediaId);
      const layerType = selectedItem ? getLayerTypeForPreview(selectedItem) : getLayerTypeFromUrl(result.url);
      const fps = Math.max(1, editorVideo.fps || 30);
      const startTime = currentFrame / fps;
      const source = resolvedMediaUrl;

      let sourceDuration: number | undefined;
      if (layerType === 'image') {
        sourceDuration = 2;
      } else {
        sourceDuration = await detectVideoDuration(source);
      }

      await commands.addLayerCommand(
        commit,
        {
          type: layerType,
          source,
          startTime,
          sourceDuration,
        },
        undefined,
        0,
        activeGroupPath,
      );
      onClose();
    } catch (error) {
      toast({
        title: 'Failed to add media',
        description: extractErrorMessage(error),
        status: 'error',
        isClosable: true,
      });
    } finally {
      setActiveMediaId(null);
    }
  };

  return (
    <>
      <button onClick={onOpen}>Upload from TG</button>

      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Telegram Media Preview</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Telegram post link</FormLabel>
                <Input
                  value={link}
                  onChange={(e) => setLink(e.target.value)}
                  placeholder="https://t.me/channel/123"
                />
              </FormControl>

              {items.length === 0 ? (
                <Text color="gray.500" fontSize="sm">
                  No media attached or preview not loaded yet.
                </Text>
              ) : (
                <SimpleGrid columns={3} spacing={2}>
                  {items.map((item) => (
                    <Box key={item.media_id} borderWidth="1px" borderRadius="md" p={2}>
                      {item.thumbnail_url ? (
                        <Image
                          src={resolvePreviewUrl(item.thumbnail_url)}
                          alt={`Media ${item.media_id}`}
                          borderRadius="sm"
                          objectFit="contain"
                          w="100%"
                          h="72px"
                        />
                      ) : (
                        <Box h="72px" bg="gray.100" borderRadius="sm" />
                      )}
                      <Text mt={2} fontSize="xs" color="gray.600">
                        Media ID: {item.media_id}
                      </Text>
                      <Text mt={1} fontSize="xs" color="gray.500">
                        Type: {getLayerTypeForPreview(item) === 'image' ? 'Image' : 'Video'}
                      </Text>
                      <Button
                        mt={2}
                        size="xs"
                        width="100%"
                        onClick={() => { void handleChooseMedia(item.media_id); }}
                        isLoading={isDownloadingSingle && activeMediaId === item.media_id}
                        isDisabled={isDownloadingSingle && activeMediaId !== item.media_id}
                      >
                        Use this media
                      </Button>
                    </Box>
                  ))}
                </SimpleGrid>
              )}
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button mr={3} onClick={onClose} variant="ghost">Close</Button>
            <Button onClick={() => { void handlePreview(); }} isLoading={isLoading} isDisabled={!link.trim()}>
              Load Preview
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};
