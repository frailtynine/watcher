import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Heading,
  Text,
  Grid,
  GridItem,
  VStack,
  Spinner,
  Center,
  Divider,
  Button,
  Link,
  useToast,
} from '@chakra-ui/react';
import { ArrowBackIcon, RepeatIcon, ExternalLinkIcon } from '@chakra-ui/icons';
import { useGetNewspaperQuery, useRegenerateNewspaperMutation } from '../../services/api';
import type { NewspaperItem } from '../../types';

const truncate = (text: string | null, max: number): string => {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '…' : text;
};

const formatDate = (iso: string | null): string => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

interface NewsCardProps {
  item: NewspaperItem;
  variant: 'large' | 'medium' | 'small';
}

const NewsCard = ({ item, variant }: NewsCardProps) => {
  const title = item.link ? (
    <Link href={item.link} isExternal color="inherit" _hover={{ textDecoration: 'underline' }}>
      {item.title} <ExternalLinkIcon mx="2px" boxSize={3} />
    </Link>
  ) : item.title;

  return (
    <Box
      borderWidth="1px"
      borderRadius="md"
      p={4}
      bg="white"
      h="100%"
      display="flex"
      flexDirection="column"
    >
      <Text
        fontWeight="bold"
        fontSize={variant === 'large' ? 'xl' : variant === 'medium' ? 'md' : 'sm'}
        lineHeight="1.4"
        mb={2}
        fontFamily="Georgia, serif"
      >
        {title}
      </Text>

      {variant !== 'small' && (
        <Text fontSize="sm" color="gray.700" flex="1" mb={3}>
          {truncate(item.summary, variant === 'large' ? 400 : 200)}
        </Text>
      )}

      {(item.source_name || item.pub_date) && (
        <Text fontSize="xs" color="gray.400" mt="auto">
          {[item.source_name, item.pub_date ? formatDate(item.pub_date) : null]
            .filter(Boolean)
            .join(' · ')}
        </Text>
      )}
    </Box>
  );
};

interface NewspaperRowProps {
  items: NewspaperItem[];
}

const NewspaperRow = ({ items }: NewspaperRowProps) => {
  if (items.length === 1) {
    return <NewsCard item={items[0]} variant="large" />;
  }

  if (items.length === 2) {
    return (
      <Grid templateColumns="1fr 1fr" gap={4}>
        {items.map((item, i) => (
          <GridItem key={i}>
            <NewsCard item={item} variant="medium" />
          </GridItem>
        ))}
      </Grid>
    );
  }

  return (
    <Grid templateColumns={`repeat(${items.length}, 1fr)`} gap={3}>
      {items.map((item, i) => (
        <GridItem key={i}>
          <NewsCard item={item} variant="small" />
        </GridItem>
      ))}
    </Grid>
  );
};

export const NewspaperPage = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const {
    data: newspaper,
    isLoading,
    isError,
  } = useGetNewspaperQuery(Number(taskId));
  const [regenerate, { isLoading: isRegenerating }] = useRegenerateNewspaperMutation();

  const handleRegenerate = async () => {
    try {
      await regenerate(Number(taskId)).unwrap();
      toast({ title: 'Newspaper regenerated', status: 'success', duration: 3000 });
    } catch {
      toast({ title: 'Failed to regenerate', status: 'error', duration: 3000 });
    }
  };

  if (isLoading) {
    return (
      <Center h="60vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  if (isError || !newspaper) {
    return (
      <Center h="60vh">
        <VStack spacing={4}>
          <Text fontSize="lg" color="gray.500">
            No newspaper available for this task yet.
          </Text>
          <Button
            leftIcon={<RepeatIcon />}
            colorScheme="blue"
            isLoading={isRegenerating}
            loadingText="Generating…"
            onClick={handleRegenerate}
          >
            Generate Newspaper
          </Button>
          <Button leftIcon={<ArrowBackIcon />} variant="ghost" onClick={() => navigate(-1)}>
            Go back
          </Button>
        </VStack>
      </Center>
    );
  }

  const rowMap = new Map<number, NewspaperItem[]>();
  for (const item of newspaper.body.rows) {
    const rowNum = item.position[0];
    if (!rowMap.has(rowNum)) rowMap.set(rowNum, []);
    rowMap.get(rowNum)!.push(item);
  }
  const rows = [...rowMap.entries()]
    .sort(([a], [b]) => a - b)
    .map(([, items]) => items.sort((a, b) => a.position[1] - b.position[1]));

  return (
    <Box bg="gray.50" minH="100vh" py={8}>
      <Container maxW="4xl">
        <VStack align="stretch" spacing={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
            <Button
              leftIcon={<ArrowBackIcon />}
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
            >
              Back
            </Button>
            <Button
              leftIcon={<RepeatIcon />}
              size="sm"
              colorScheme="blue"
              variant="outline"
              isLoading={isRegenerating}
              loadingText="Regenerating…"
              onClick={handleRegenerate}
            >
              Regenerate
            </Button>
          </Box>

          <Box textAlign="center" mb={6}>
            <Heading
              size="2xl"
              fontFamily="Georgia, serif"
              letterSpacing="-0.5px"
            >
              {newspaper.title}
            </Heading>
            <Text color="gray.500" fontSize="sm" mt={2}>
              Updated {new Date(newspaper.updated_at).toLocaleString()}
            </Text>
          </Box>

          <Divider borderColor="gray.800" borderWidth="2px" mb={2} />
          <Divider borderColor="gray.800" mb={6} />

          {rows.length === 0 ? (
            <Center py={12}>
              <Text color="gray.500">No news items in this edition yet.</Text>
            </Center>
          ) : (
            <VStack spacing={0} align="stretch">
              {rows.map((items, i) => (
                <Box key={i}>
                  <NewspaperRow items={items} />
                  {i < rows.length - 1 && (
                    <Divider borderColor="gray.300" my={6} />
                  )}
                </Box>
              ))}
            </VStack>
          )}
        </VStack>
      </Container>
    </Box>
  );
};
