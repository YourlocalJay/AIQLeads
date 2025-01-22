"""add transaction and subscription tables

Revision ID: 202501221
Revises: previous_revision_id
Create Date: 2025-01-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '202501221'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None

def upgrade():
    # Create TransactionStatus enum type
    op.execute("""
        CREATE TYPE transaction_status AS ENUM 
        ('pending', 'completed', 'failed', 'refunded')
    """)

    # Create TransactionType enum type
    op.execute("""
        CREATE TYPE transaction_type AS ENUM 
        ('subscription', 'one_time', 'refund')
    """)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'failed', 'refunded',
                                            name='transaction_status'), 
                  nullable=False, server_default='pending'),
        sa.Column('type', postgresql.ENUM('subscription', 'one_time', 'refund',
                                          name='transaction_type'), 
                  nullable=False),
        sa.Column('reference_id', sa.String(length=100), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('description', sa.String(length=255), nullable=True),
    )

    # Create SubscriptionTier enum type
    op.execute("""
        CREATE TYPE subscription_tier AS ENUM 
        ('basic', 'premium', 'enterprise')
    """)

    # Create SubscriptionStatus enum type
    op.execute("""
        CREATE TYPE subscription_status AS ENUM 
        ('active', 'cancelled', 'expired', 'pending')
    """)

    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=False),
        sa.Column('tier', postgresql.ENUM('basic', 'premium', 'enterprise', 
                                          name='subscription_tier'), nullable=False),
        sa.Column('status', postgresql.ENUM('active', 'cancelled', 'expired', 'pending',
                                            name='subscription_status'), nullable=False, 
                  server_default='pending'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('idx_transactions_status', 'transactions', ['status'])
    op.create_index('idx_subscriptions_user_id', 'subscriptions', ['user_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_subscriptions_dates', 'subscriptions', ['start_date', 'end_date'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_subscriptions_dates', table_name='subscriptions')
    op.drop_index('idx_subscriptions_status', table_name='subscriptions')
    op.drop_index('idx_subscriptions_user_id', table_name='subscriptions')
    op.drop_index('idx_transactions_status', table_name='transactions')
    op.drop_index('idx_transactions_user_id', table_name='transactions')

    # Drop tables
    op.drop_table('subscriptions')
    op.drop_table('transactions')

    # Drop enum types
    op.execute('DROP TYPE subscription_status')
    op.execute('DROP TYPE subscription_tier')
    op.execute('DROP TYPE transaction_type')
    op.execute('DROP TYPE transaction_status')
