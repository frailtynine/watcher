import {
  Box,
  Button,
  Heading,
  HStack,
  Input,
  Spinner,
  Text,
} from '@chakra-ui/react';
import type { VideoProject } from '../../types';

type Props = {
  projects: VideoProject[];
  isLoadingProjects: boolean;
  newProjectName: string;
  setNewProjectName: (value: string) => void;
  onCreateProject: () => Promise<void>;
  onOpenProject: (id: number) => void;
  isCreating: boolean;
};

export const VideoProjectsPage = ({
  projects,
  isLoadingProjects,
  newProjectName,
  setNewProjectName,
  onCreateProject,
  onOpenProject,
  isCreating,
}: Props) => {
  return (
    <Box p={6}>
      <Heading size="lg" mb={5}>Video Projects</Heading>

      <Box bg="white" borderWidth="1px" borderRadius="md" p={4} mb={4}>
        <HStack>
          <Input
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="Project name"
          />
          <Button onClick={() => { void onCreateProject(); }} isLoading={isCreating} colorScheme="blue">
            Create Project
          </Button>
        </HStack>
      </Box>

      <Box bg="white" borderWidth="1px" borderRadius="md" p={4}>
        {isLoadingProjects ? <Spinner /> : (
          <Box>
            {projects.length === 0 ? (
              <Text color="gray.500">No projects yet.</Text>
            ) : (
              projects.map((item) => (
                <Button
                  key={item.id}
                  variant="outline"
                  justifyContent="space-between"
                  width="100%"
                  mb={2}
                  onClick={() => onOpenProject(item.id)}
                >
                  <Text>{item.name}</Text>
                  <Text fontSize="xs" color="gray.500">{item.clip_urls.length} clips</Text>
                </Button>
              ))
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
};
