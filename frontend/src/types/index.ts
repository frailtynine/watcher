export interface TelegramBot {
  id: number;
  bot_name: string;
  bot_tg_id: string;
  bot_token: boolean;
  is_active: boolean;
}

export interface UserSettings {
  gemini_api_key?: string | boolean | null;
  telegram_api_id?: string | boolean | null;
  telegram_api_hash?: string | boolean | null;
  telegram_session_string?: string | boolean | null;
  telegram_bots?: TelegramBot[];
}

export interface UserSettingsUpdate {
  gemini_api_key?: string | null;
  telegram_api_id?: string | null;
  telegram_api_hash?: string | null;
  telegram_session_string?: string | null;
  [key: string]: unknown;
}

export interface TelegramBotCreate {
  bot_token: string;
}

export interface TelegramBotTaskAssociation {
  telegram_bot_id: number;
  news_task_id: number;
  created_at?: string;
}

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

export interface NewsItem {
  id: number;
  source_id: number;
  title: string | null;
  content: string | null;
  url: string | null;
  external_id: string | null;
  published_at: string | null;
  fetched_at: string;
  settings: any | null;
  raw_data: any | null;
  created_at: string;
  updated_at: string;
  processing_results?: NewsItemNewsTask[];
}

export interface NewspaperItem {
  title: string;
  summary: string;
  news_item_id: number | null;
  position: [number, number];
  body: string | null;
  pub_date: string | null;
  link: string | null;
  source_name: string | null;
}

export interface Newspaper {
  id: number;
  news_task_id: number;
  title: string;
  body: { rows: NewspaperItem[] };
  updated_at: string;
}

export interface NewsItemNewsTask {
  news_item_id: number;
  news_task_id: number;
  processed: boolean;
  result: boolean | null;
  processed_at: string | null;
  ai_response: any | null;
  created_at: string;
  updated_at: string;
}
