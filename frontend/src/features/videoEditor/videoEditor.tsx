import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Spinner,
  useToast,
} from '@chakra-ui/react';
import { useNavigate, useParams } from 'react-router-dom';
import { VideoEditor } from '@videoflow/react-video-editor';
import '@videoflow/react-video-editor/style.css';
import {
  useCreateVideoMutation,
  useGetVideoQuery,
  useGetVideosQuery,
  useUpdateVideoMutation
} from '../../services/api';
import { VideoEditorTitlebar } from './VideoEditorTitlebar';
import { VideoProjectsPage } from './VideoProjectsPage';

const DEFAULT_VIDEO_JSON = {
  name: 'video-canvas',
  width: 1080,
  height: 1920,
  fps: 30,
  duration: 60,
  layers: [],
  backgroundColor: '#000000',
};

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
  return 'Operation failed';
};

export default function VideoEditorPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId?: string }>();
  const toast = useToast();

  const [newProjectName, setNewProjectName] = useState('');
  const [loadedVideo, setLoadedVideo] = useState<Record<string, unknown> | null>(null);

  const { data: projects = [], isLoading: isLoadingProjects } = useGetVideosQuery();
  const numericProjectId = projectId ? Number(projectId) : NaN;
  const isProjectRoute = Number.isFinite(numericProjectId);

  const {
    data: project,
    isLoading: isLoadingProject,
  } = useGetVideoQuery(numericProjectId, { skip: !isProjectRoute });

  const [createVideo, { isLoading: isCreating }] = useCreateVideoMutation();
  const [updateVideo] = useUpdateVideoMutation();
  const activeVideoJson = loadedVideo || DEFAULT_VIDEO_JSON;

  useEffect(() => {
    if (!project) {
      return;
    }
    const snapshot = (project.video_json as Record<string, unknown>) || DEFAULT_VIDEO_JSON;
    setLoadedVideo(structuredClone(snapshot));
  }, [project?.id]);

  const handleUpload = useCallback(async (file: File) => URL.createObjectURL(file), []);

  const handleCreateProject = async () => {
    try {
      const created = await createVideo({
        name: newProjectName.trim() || `Project ${projects.length + 1}`,
        video_json: DEFAULT_VIDEO_JSON,
        clip_urls: [],
      }).unwrap();
      setNewProjectName('');
      navigate(`/video-editor/${created.id}`);
    } catch (error) {
      toast({
        title: 'Failed to create project',
        description: extractErrorMessage(error),
        status: 'error',
        isClosable: true,
      });
    }
  };

  const handleSaveProject = async (videoJson: Record<string, unknown>) => {
    if (!project) {
      return;
    }
    try {
      await updateVideo({
        id: project.id,
        data: { video_json: videoJson },
      }).unwrap();
    } catch (error) {
      toast({
        title: 'Failed to save project',
        description: extractErrorMessage(error),
        status: 'error',
        isClosable: true,
      });
    }
  };

  if (!isProjectRoute) {
    return (
      <VideoProjectsPage
        projects={projects}
        isLoadingProjects={isLoadingProjects}
        newProjectName={newProjectName}
        setNewProjectName={setNewProjectName}
        onCreateProject={handleCreateProject}
        onOpenProject={(id) => navigate(`/video-editor/${id}`)}
        isCreating={isCreating}
      />
    );
  }

  if (isLoadingProject || !project) {
    return (
      <Box p={6}>
        <Spinner />
      </Box>
    );
  }

  return (
    <Box h="calc(100dvh - 64px)" minH={0} overflow="hidden">
      <Box h="100%" minH={0} overflow="hidden" sx={{ '& > div': { height: '100%' }, '& vf-editor': { height: '100%', minHeight: 0 } }}>
        <VideoEditor
          components={{
            Titlebar: (props) => (
              <VideoEditorTitlebar
                onExport={props.onExport}
                onSave={props.onSave}
                branding={props.branding}
                onDelete={() => {
                  console.log('Delete project button clicked');
                }}
              />
            ),
          }}
          key={`project-${project.id}`}
          video={activeVideoJson as any}
          theme="grey"
          onUpload={handleUpload}
          onSave={(video) => handleSaveProject(video as Record<string, unknown>)}
        />
      </Box>
    </Box>
  );
}
