import { VideoEditor } from '@videoflow/react-video-editor';
import '@videoflow/react-video-editor/style.css';

const initialVideoCanvas = {
    name: 'video-canvas',
    width: 1080, height: 1920, fps: 30, duration: 60,
    layers: [],
    backgroundColor: '#000000',
}

export default function VideoEditorComponent() {
    return (
        <div className="video-editor" style={{ height: 'calc(100vh - 64px)' }}>
            <VideoEditor
                video={initialVideoCanvas} theme='grey'
                onChange={(next) => console.log('edited', next)}
            />
        </div>
    )
}