'''create recently crawled urls table

Revision ID: 20231010_123456
Revises: 
Create Date: 2023-10-10 12:34:56

'''

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20231010_123456'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    try:
        op.create_table(
            'recently_crawled_urls',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('url', sa.String, nullable=False, unique=True, index=True),
            sa.Column('crawl_timestamp', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
        )
    except Exception as e:
        import logging
        logging.error(e, exc_info=True)
        raise


def downgrade() -> None:
    try:
        op.drop_table('recently_crawled_urls')
    except Exception as e:
        import logging
        logging.error(e, exc_info=True)
        raise
