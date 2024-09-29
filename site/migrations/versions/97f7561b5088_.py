"""empty message

Revision ID: 97f7561b5088
Revises: 
Create Date: 2024-07-01 20:23:50.033773

"""
from alembic import op
import sqlalchemy as sa
import json

default = json.dumps({"AMC 8": 1, "AMC 10": 1, "AMC 12": 1})

# revision identifiers, used by Alembic.
revision = '97f7561b5088'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferred_levels', sa.String(length=100), server_default=default, nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.drop_column('preferred_levels')

    # ### end Alembic commands ###