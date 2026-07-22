import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Text,
  VStack,
  useToast,
} from '@chakra-ui/react';
import {
  Sidebar as DefaultSidebar,
  useEditorStore,
} from '@videoflow/react-video-editor';

const toAbsoluteUrl = (path: string): string => {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }

  const origin = window.location.origin;
  const apiBase = import.meta.env.VITE_API_URL || '/api';

  if (path.startsWith('/api/')) {
    if (apiBase.startsWith('http://') || apiBase.startsWith('https://')) {
      const apiOrigin = new URL(apiBase).origin;
      return new URL(path, apiOrigin).toString();
    }
    return new URL(path, origin).toString();
  }

  if (path.startsWith('/')) {
    return new URL(path, origin).toString();
  }

  if (apiBase.startsWith('http://') || apiBase.startsWith('https://')) {
    return new URL(path, apiBase.endsWith('/') ? apiBase : `${apiBase}/`).toString();
  }

  return new URL(`${apiBase.replace(/^\/+|\/+$/g, '')}/${path}`, origin).toString();
};

const fetchClipAsFile = async (url: string): Promise<File> => {
  const response = await fetch(url);
  const contentType = response.headers.get('content-type') || '';
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const fileName = new URL(url).pathname.split('/').pop() || `clip-${Date.now()}`;
  const type = blob.type || contentType || 'video/mp4';
  return new File([blob], fileName, { type });
};

const extractErrorMessage = (error: unknown): string => {
  if (!error || typeof error !== 'object') {
    return 'Operation failed';
  }
  if ('message' in error && typeof error.message === 'string') {
    return error.message;
  }
  return 'Operation failed';
};

type Props = {
  clipUrls: string[];
  downloadLink: string;
  onDownloadLinkChange: (value: string) => void;
  onDownload: () => Promise<void>;
  isDownloading: boolean;
};

export const VideoEditorSidebar = ({
  clipUrls,
  downloadLink,
  onDownloadLinkChange,
  onDownload,
  isDownloading,
}: Props) => {
  const toast = useToast();
  const mediaImporter = useEditorStore((state) => state.mediaImporter);
  const currentFrame = useEditorStore((state) => state.currentFrame);
  const video = useEditorStore((state) => state.video);
  const activeGroupPath = useEditorStore((state) => state.activeGroupPath);

  const handleInsert = async (url: string) => {
    if (!mediaImporter) {
      toast({
        title: 'Editor not ready',
        description: 'Media importer is not initialized yet.',
        status: 'warning',
        isClosable: true,
      });
      return;
    }

    try {
      const absoluteUrl = toAbsoluteUrl(url);
      const file = await fetchClipAsFile(absoluteUrl);
      const fps = Math.max(1, video.fps || 30);
      await mediaImporter([file], {
        startTime: currentFrame / fps,
        track: 0,
        groupPath: activeGroupPath,
      });
    } catch (error) {
      toast({
        title: 'Failed to insert clip',
        description: extractErrorMessage(error),
        status: 'error',
        isClosable: true,
      });
    }
  };

  return (
    <VStack align="stretch" spacing={3} h="100%">
      <DefaultSidebar />
      <Box borderTopWidth="1px" pt={3} px={3} pb={4}>
        <Heading size="xs" mb={2}>Telegram Download</Heading>
        <FormControl>
          <FormLabel fontSize="xs">Post Link</FormLabel>
          <Input
            size="sm"
            value={downloadLink}
            onChange={(e) => onDownloadLinkChange(e.target.value)}
            placeholder="https://t.me/channel/123"
          />
        </FormControl>
        <Button
          mt={2}
          size="sm"
          colorScheme="teal"
          onClick={() => { void onDownload(); }}
          isLoading={isDownloading}
          isDisabled={!downloadLink.trim()}
        >
          Download Clips
        </Button>

        <Heading size="xs" mt={4} mb={2}>Saved Clips</Heading>
        <VStack align="stretch" spacing={2} maxH="220px" overflow="auto">
          {clipUrls.length === 0 ? (
            <Text fontSize="xs" color="gray.500">No clips yet.</Text>
          ) : (
            clipUrls.map((url) => (
              <Button
                key={url}
                size="xs"
                variant="outline"
                justifyContent="flex-start"
                onClick={() => { void handleInsert(url); }}
              >
                {url.split('/').pop() || url}
              </Button>
            ))
          )}
        </VStack>
      </Box>
    </VStack>
  );
};
