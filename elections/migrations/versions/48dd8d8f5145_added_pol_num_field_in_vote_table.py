"""added pol num field in vote table

Revision ID: 48dd8d8f5145
Revises: ffb5c6b36577
Create Date: 2021-09-14 15:18:47.603366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48dd8d8f5145'
down_revision = 'ffb5c6b36577'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('votes', sa.Column('polNum', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('votes', 'polNum')
    # ### end Alembic commands ###
