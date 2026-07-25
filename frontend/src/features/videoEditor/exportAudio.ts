import BrowserRenderer from '@videoflow/renderer-browser';
import { audioBufferToWav } from '@videoflow/core';
import type { VideoJSON } from '@videoflow/react-video-editor';

const sanitizeFileName = (value: string): string => {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '') || 'video-audio';
};

export const renderAudioAsWavFile = async (
  video: VideoJSON,
  fileNameBase?: string,
): Promise<File> => {
  const renderer = new BrowserRenderer(video);
  try {
    const audioBuffer = await renderer.renderAudio();
    if (!audioBuffer) {
      throw new Error('No audio could be rendered from this project');
    }

    const wavBuffer = audioBufferToWav(audioBuffer);
    const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
    const fileName = `${sanitizeFileName(fileNameBase || video.name || 'video-audio')}.wav`;
    return new File([wavBlob], fileName, { type: 'audio/wav' });
  } finally {
    renderer.destroy();
  }
};
