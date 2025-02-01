import sqlalchemy as sa
import pytest

# Test to check if the recently_crawled_urls table exists

def test_recently_crawled_urls_table_exists(db_session):
    engine = db_session.get_bind() or db_session.bind
    inspector = sa.inspect(engine)
    assert 'recently_crawled_urls' in inspector.get_table_names(), "Table 'recently_crawled_urls' does not exist"


# Test to verify that the 'url' column has a unique constraint

def test_url_unique_constraint(db_session):
    engine = db_session.get_bind() or db_session.bind
    inspector = sa.inspect(engine)
    indexes = inspector.get_indexes('recently_crawled_urls')
    unique_index_exists = any(idx.get('unique', False) and 'url' in idx.get('column_names', []) for idx in indexes)
    assert unique_index_exists, "Unique constraint on 'url' is not set"


# Test to verify that the crawl_timestamp has a default value of CURRENT_TIMESTAMP

def test_crawl_timestamp_default(db_session):
    from sqlalchemy import MetaData, Table
    engine = db_session.get_bind() or db_session.bind
    metadata = MetaData()
    table = Table('recently_crawled_urls', metadata, autoload_with=engine)
    col = table.c.crawl_timestamp
    default_expr = col.server_default.arg.text if col.server_default is not None else None
    assert default_expr == 'CURRENT_TIMESTAMP', "Default CURRENT_TIMESTAMP is not set for crawl_timestamp"
