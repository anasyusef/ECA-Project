"""empty message

Revision ID: b9df2f75896b
Revises: 79b72d6d57ad
Create Date: 2018-03-24 18:22:16.872080

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9df2f75896b'
down_revision = '79b72d6d57ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('waiting_list',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('eca_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['eca_id'], ['eca.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('waiting_list')
    # ### end Alembic commands ###
