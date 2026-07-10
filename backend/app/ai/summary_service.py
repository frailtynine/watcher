import logging

from newspaper import Article

from app.ai.gemini_client import GeminiClient

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
