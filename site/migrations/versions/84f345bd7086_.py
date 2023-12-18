"""empty message

Revision ID: 84f345bd7086
Revises: 77103c11fbdc
Create Date: 2023-12-02 22:43:24.187634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84f345bd7086'
down_revision = '77103c11fbdc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('problem_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_id', sa.Integer(), nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('fk_problem_history_profile_id_profile'), 'profile', ['profile_id'], ['id'])
        batch_op.drop_column('user_id')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_profile', sa.Integer(), nullable=False))
        batch_op.create_unique_constraint(batch_op.f('uq_user_email'), ['email'])
        batch_op.create_unique_constraint(batch_op.f('uq_user_username'), ['username'])
        batch_op.drop_column('performance')
        batch_op.drop_column('preferred_categories')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferred_categories', sa.VARCHAR(length=2000), server_default=sa.text("'[]'"), nullable=False))
        batch_op.add_column(sa.Column('performance', sa.VARCHAR(length=2000), nullable=False))
        batch_op.drop_constraint(batch_op.f('uq_user_username'), type_='unique')
        batch_op.drop_constraint(batch_op.f('uq_user_email'), type_='unique')
        batch_op.drop_column('current_profile')

    with op.batch_alter_table('problem_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint(batch_op.f('fk_problem_history_profile_id_profile'), type_='foreignkey')
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])
        batch_op.drop_column('profile_id')

    # ### end Alembic commands ###
