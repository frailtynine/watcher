import { Titlebar as DefaultTitlebar } from '@videoflow/react-video-editor';
import type { ReactNode } from 'react';
import { UpluadButton } from './UploadButton';

type Props = {
  onExport?: () => void;
  onSave?: () => void;
  branding?: ReactNode;
  onDelete?: () => void;
  onGenerateCaptions?: () => void;
  isGeneratingCaptions?: boolean;
};

export const VideoEditorTitlebar = ({
  onExport,
  onSave,
  branding,
  onDelete,
  onGenerateCaptions,
  isGeneratingCaptions,
}: Props) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%', alignItems: 'center', }}>
      <DefaultTitlebar
        onExport={onExport}
        onSave={onSave}
        branding={branding}
      />
      <button onClick={onGenerateCaptions} disabled={isGeneratingCaptions}>
        {isGeneratingCaptions ? 'Generating captions...' : 'Generate captions'}
      </button>
      <UpluadButton />
      <button onClick={onDelete}>
        Delete
      </button>
    </div>
  );
};
