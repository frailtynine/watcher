from fastcrud import FastCRUD
from app.models import (
    NewsTask,
    Source,
    SourceNewsTask,
    NewsItem,
    NewsItemNewsTask
)

# Create FastCRUD instances for each model
news_task_crud = FastCRUD(NewsTask)
source_crud = FastCRUD(Source)
source_news_task_crud = FastCRUD(SourceNewsTask)
# Disable automatic updated_at handling to avoid timezone issues
news_item_crud = FastCRUD(NewsItem, updated_at_column="")
news_item_news_task_crud = FastCRUD(NewsItemNewsTask)
