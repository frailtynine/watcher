import logging

from newspaper import Article

from app.ai.gemini_client import GeminiClient
from app.models.news_item import NewsItem
from app.models.source import SourceType

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for summarizing news articles."""

    def get_article(self, url: str) -> Article:
        """Fetch and parse a news article from the given URL.

        Args:
            url: The URL of the news article.
        """
        article = Article(url)
        article.download()
        article.parse()
        return article

    async def summarize_article(
        self, article: Article, prompt: str, api_key: str
    ) -> str:
        """Summarize the given news article using Gemini API.

        Args:
            article: The news article to summarize.
            prompt: The prompt to guide the summarization.
            api_key: The API key for Gemini API.
        """
        return await self.summarize_text(
            title=article.title,
            text=article.text,
            prompt=prompt,
            api_key=api_key,
        )

    async def summarize_text(
        self,
        title: str | None,
        text: str | None,
        prompt: str,
        api_key: str,
    ) -> str:
        """Summarize plain title/text content using Gemini API."""
        gemini_client = GeminiClient(api_key=api_key)
        summary_prompt = (
            f"{prompt}\n\nArticle Title: {title or ''}"
            f"\nArticle Text: {text or ''}"
        )
        return await gemini_client.generate_text_response(summary_prompt)

    def should_fetch_article_for_news_item(self, news_item: NewsItem) -> bool:
        """Use article fetch only for RSS sources with URL."""
        if not news_item.url or not news_item.source:
            return False
        return news_item.source.type == SourceType.RSS

    @staticmethod
    def _add_link_to_summary(summary_text: str, news_item: NewsItem) -> str:
        if news_item.url:
            return f"{summary_text.strip()}\n\n{news_item.url}"
        return summary_text.strip()

    async def summarize_news_item(
        self,
        news_item: NewsItem,
        prompt: str,
        language: str,
        api_key: str,
    ) -> str:
        """Summarize a news item with source-aware strategy and link output."""
        prompt_with_language = f"{prompt}\n\nSummarize in {language} language"

        summary_text: str | None = None
        article_url = news_item.url
        if article_url and self.should_fetch_article_for_news_item(news_item):
            try:
                article = self.get_article(article_url)
                summary_text = await self.summarize_article(
                    article=article,
                    prompt=prompt_with_language,
                    api_key=api_key,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to fetch/parse article URL for news_item_id=%s: %s",
                    news_item.id,
                    exc,
                )

        if not isinstance(summary_text, str) or not summary_text.strip():
            summary_text = await self.summarize_text(
                title=news_item.title,
                text=news_item.content,
                prompt=prompt_with_language,
                api_key=api_key,
            )

        return self._add_link_to_summary(summary_text, news_item)
