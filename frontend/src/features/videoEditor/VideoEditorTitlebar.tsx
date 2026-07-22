import { Titlebar as DefaultTitlebar } from '@videoflow/react-video-editor';
import type { ReactNode } from 'react';
import { UpluadButton } from './UploadButton';

type Props = {
  onExport?: () => void;
  onSave?: () => void;
  branding?: ReactNode;
  onDelete?: () => void;
};

export const VideoEditorTitlebar = ({
  onExport,
  onSave,
  branding,
  onDelete,
}: Props) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%', alignItems: 'center', }}>
      <DefaultTitlebar
        onExport={onExport}
        onSave={onSave}
        branding={branding}
      />
      <UpluadButton />
      <button onClick={onDelete}>
        Delete
      </button>
    </div>
  );
};
