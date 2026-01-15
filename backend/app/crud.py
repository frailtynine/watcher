from fastcrud import FastCRUD
from app.models import NewsTask, Source, SourceNewsTask, NewsItem

# Create FastCRUD instances for each model
news_task_crud = FastCRUD(NewsTask)
source_crud = FastCRUD(Source)
source_news_task_crud = FastCRUD(SourceNewsTask)
news_item_crud = FastCRUD(NewsItem)
