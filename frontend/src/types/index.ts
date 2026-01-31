export interface NewsTask {
  id: string;
  user_id: string;
  name: string;
  prompt: string;
  active: boolean;
  created_at: string;
  updated_at: string;
  sources_count: number;
}

export interface NewsTaskCreate {
  name: string;
  prompt: string;
  active: boolean;
}

export interface NewsTaskUpdate {
  name?: string;
  prompt?: string;
  active?: boolean;
}

export interface Source {
  id: string;
  user_id: string;
  name: string;
  type: 'RSS' | 'Telegram';
  source: string;
  active: boolean;
  last_fetched_at: string | null;
  created_at: string;
}

export interface SourceCreate {
  name: string;
  type: 'RSS' | 'Telegram';
  source: string;
  active: boolean;
}

export interface SourceUpdate {
  name?: string;
  source?: string;
  active?: boolean;
}

export interface SourceNewsTaskAssociation {
  source_id: number;
  news_task_id: number;
  created_at?: string;
}
