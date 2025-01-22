"""market insights enhancement

Revision ID: 20240122
Revises: previous_revision
Create Date: 2024-01-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add new columns
    op.add_column('market_insights', sa.Column('analysis_type', sa.String(20), nullable=False))
    op.add_column('market_insights', sa.Column('confidence_score', sa.Float(), nullable=False))
    op.add_column('market_insights', sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'))
    op.add_column('market_insights', sa.Column('parameters', postgresql.JSONB(), nullable=False, server_default='{}'))

    # Add new indexes
    op.create_index('ix_market_insights_analysis_type', 'market_insights', ['analysis_type'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_market_insights_analysis_type')
    
    # Remove columns
    op.drop_column('market_insights', 'analysis_type')
    op.drop_column('market_insights', 'confidence_score')
    op.drop_column('market_insights', 'tags')
    op.drop_column('market_insights', 'parameters')