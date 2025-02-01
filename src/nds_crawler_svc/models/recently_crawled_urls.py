from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from .base import Base

class RecentlyCrawledUrl(Base):
    __tablename__ = 'recently_crawled_urls'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True, index=True)
    crawl_timestamp = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
