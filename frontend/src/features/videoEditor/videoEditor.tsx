import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Spinner,
  useToast,
} from '@chakra-ui/react';
import { useNavigate, useParams } from 'react-router-dom';
import { VideoEditor, commands, useEditorStore } from '@videoflow/react-video-editor';
import type { VideoJSON } from '@videoflow/react-video-editor';
import type { AIAudioCaptionEntry } from '../../types';
import '@videoflow/react-video-editor/style.css';
import {
  useCreateVideoMutation,
  useDebugAudioTranscriptionMutation,
  useGetVideoQuery,
  useGetVideosQuery,
  useUpdateVideoMutation
} from '../../services/api';
import { VideoEditorTitlebar } from './VideoEditorTitlebar';
import { VideoProjectsPage } from './VideoProjectsPage';
import { renderAudioAsWavFile } from './exportAudio';
import { useSplitAtPlayheadShortcut } from './useSplitAtPlayheadShortcut';

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
  const [isGeneratingCaptions, setIsGeneratingCaptions] = useState(false);
  const editorVideo = useEditorStore((state) => state.video);
  const commit = useEditorStore((state) => state.commit);

  const { data: projects = [], isLoading: isLoadingProjects } = useGetVideosQuery();
  const numericProjectId = projectId ? Number(projectId) : NaN;
  const isProjectRoute = Number.isFinite(numericProjectId);

  const {
    data: project,
    isLoading: isLoadingProject,
  } = useGetVideoQuery(numericProjectId, { skip: !isProjectRoute });

  const [createVideo, { isLoading: isCreating }] = useCreateVideoMutation();
  const [updateVideo] = useUpdateVideoMutation();
  const [debugAudioTranscription] = useDebugAudioTranscriptionMutation();
  const activeVideoJson = loadedVideo || DEFAULT_VIDEO_JSON;
  useSplitAtPlayheadShortcut();

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

  const handleGenerateCaptions = async () => {
    const currentVideo = editorVideo as unknown as VideoJSON;
    setIsGeneratingCaptions(true);
    try {
      const wavFile = await renderAudioAsWavFile(currentVideo, project?.name);
      const formData = new FormData();
      formData.append('audio_file', wavFile);

      const transcription = await debugAudioTranscription(formData).unwrap();
      const captions = transcription.captions as AIAudioCaptionEntry[];

      if (!captions.length) {
        throw new Error('Transcription completed but returned no captions');
      }

      const fontSize = Math.max(1, 39 / (Math.max(1, currentVideo.width) * 0.01));
      const sortedCaptions = [...captions].sort((a, b) => a.startTime - b.startTime);
      let addedCount = 0;

      for (const caption of sortedCaptions) {
        const startTime = Number(caption.startTime ?? 0);
        const endTime = Number(caption.endTime ?? startTime);
        const sourceDuration = Math.max(0.05, endTime - startTime);
        const text = String(caption.caption ?? '').trim();
        if (!text) {
          continue;
        }

        await commands.addLayerCommand(
          commit,
          {
            type: 'text',
            startTime,
            sourceDuration,
            properties: {
              text,
              position: [0.5, 0.5],
              anchor: [0.5, 0.5],
              textAlign: 'center',
              verticalAlign: 'middle',
              fontSize,
              fontWeight: 600,
              color: '#ffffff',
              textStroke: true,
              textStrokeColor: '#000000',
              textStrokeWidth: 0.08,
            },
          },
        );
        addedCount += 1;
      }

      toast({
        title: 'Captions generated',
        description: `Added ${addedCount} text layers.`,
        status: 'success',
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Failed to generate captions',
        description: extractErrorMessage(error),
        status: 'error',
        isClosable: true,
      });
    } finally {
      setIsGeneratingCaptions(false);
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
                onGenerateCaptions={() => { void handleGenerateCaptions(); }}
                isGeneratingCaptions={isGeneratingCaptions}
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
