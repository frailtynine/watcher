import { useEffect } from 'react';
import { useEditorStore } from '@videoflow/react-video-editor';
import type { LayerJSON, VideoJSON } from '@videoflow/react-video-editor';

const EPSILON = 1e-4;

const isTextInputElement = (target: EventTarget | null): boolean => {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  const tagName = target.tagName;
  return tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT' || target.isContentEditable;
};

const getLayersAtPath = (video: VideoJSON, groupPath: string[]): LayerJSON[] => {
  let layers = video.layers;
  for (const groupId of groupPath) {
    const groupLayer = layers.find((layer) => layer.id === groupId && layer.type === 'group');
    if (!groupLayer || !Array.isArray(groupLayer.children)) {
      return [];
    }
    layers = groupLayer.children;
  }
  return layers;
};

const getGroupOffsetSeconds = (video: VideoJSON, groupPath: string[]): number => {
  let layers = video.layers;
  let offset = 0;

  for (const groupId of groupPath) {
    const groupLayer = layers.find((layer) => layer.id === groupId && layer.type === 'group');
    if (!groupLayer) {
      break;
    }
    const startTime = Number(groupLayer.settings.startTime ?? 0);
    const sourceStart = Number(groupLayer.settings.sourceStart ?? 0);
    offset += startTime - sourceStart;
    layers = Array.isArray(groupLayer.children) ? groupLayer.children : [];
  }

  return offset;
};

const makeLayerId = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `layer-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}`;
};

const cloneLayer = (layer: LayerJSON): LayerJSON => {
  return JSON.parse(JSON.stringify(layer)) as LayerJSON;
};

export const useSplitAtPlayheadShortcut = () => {
  useEffect(() => {
    const onKeyDown = async (event: KeyboardEvent) => {
      if (event.key.toLowerCase() !== 's') {
        return;
      }
      if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) {
        return;
      }
      if (isTextInputElement(event.target)) {
        return;
      }

      const state = useEditorStore.getState();
      const selectedLayerIds = state.selection.layerIds;
      if (!selectedLayerIds.length) {
        return;
      }

      const fps = Math.max(1, state.video.fps || 30);
      const playheadGlobalSeconds = state.currentFrame / fps;
      const groupOffset = getGroupOffsetSeconds(state.video, state.activeGroupPath);
      const playheadSeconds = Math.max(0, playheadGlobalSeconds - groupOffset);

      let createdLayerIds: string[] = [];
      await state.commit((draft) => {
        const activeLayers = getLayersAtPath(draft as VideoJSON, state.activeGroupPath);
        if (!activeLayers.length) {
          return;
        }

        const idSet = new Set(selectedLayerIds);
        const nextLayers: LayerJSON[] = [];
        const createdIds: string[] = [];

        for (const layer of activeLayers) {
          if (!idSet.has(layer.id)) {
            nextLayers.push(layer);
            continue;
          }

          const start = Number(layer.settings.startTime ?? 0);
          const sourceDuration = Number(layer.settings.sourceDuration ?? 0);
          const end = start + sourceDuration;

          if (sourceDuration <= 0 || playheadSeconds <= start + EPSILON || playheadSeconds >= end - EPSILON) {
            nextLayers.push(layer);
            continue;
          }

          const leftDuration = playheadSeconds - start;
          const rightDuration = end - playheadSeconds;
          const sourceStart = Number(layer.settings.sourceStart ?? 0);

          layer.settings.sourceDuration = leftDuration;
          nextLayers.push(layer);

          const rightLayer = cloneLayer(layer);
          rightLayer.id = makeLayerId();
          rightLayer.settings.startTime = playheadSeconds;
          rightLayer.settings.sourceDuration = rightDuration;
          rightLayer.settings.sourceStart = sourceStart + leftDuration;

          nextLayers.push(rightLayer);
          createdIds.push(rightLayer.id);
        }

        activeLayers.splice(0, activeLayers.length, ...nextLayers);
        createdLayerIds = createdIds;
      }, { label: 'Split at playhead' });

      if (!createdLayerIds.length) {
        return;
      }

      state.selectLayers(createdLayerIds);
      event.preventDefault();
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);
};
