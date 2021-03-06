"""empty message

Revision ID: 550d9f4a7a5d
Revises: f9dad48260da
Create Date: 2021-04-29 01:37:52.374017

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '550d9f4a7a5d'
down_revision = 'f9dad48260da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('roles', sa.Column('default', sa.Boolean(), nullable=True))
    op.add_column('roles', sa.Column('permissions', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_roles_default'), 'roles', ['default'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_roles_default'), table_name='roles')
    op.drop_column('roles', 'permissions')
    op.drop_column('roles', 'default')
    # ### end Alembic commands ###
