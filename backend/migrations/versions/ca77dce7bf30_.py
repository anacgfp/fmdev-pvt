"""empty message

Revision ID: ca77dce7bf30
Revises: b7bfdaa4bc85
Create Date: 2020-01-16 17:45:20.128748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca77dce7bf30'
down_revision = 'b7bfdaa4bc85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'created_at')
    # ### end Alembic commands ###