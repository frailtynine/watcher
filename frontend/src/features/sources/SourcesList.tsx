import { VStack } from '@chakra-ui/react';
import { SourceCard } from './SourceCard';
import type { Source } from '../../types';

interface SourcesListProps {
  sources: Source[];
  taskId: string;
}

export const SourcesList = ({ sources, taskId }: SourcesListProps) => {
  return (
    <VStack spacing={3} align="stretch">
      {sources.map((source) => (
        <SourceCard key={source.id} source={source} taskId={taskId} />
      ))}
    </VStack>
  );
};
