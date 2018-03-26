"""empty message

Revision ID: 4dd851b14b68
Revises: cb5f05ebe00e
Create Date: 2018-03-24 23:46:53.243792

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4dd851b14b68'
down_revision = 'cb5f05ebe00e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('waiting_list')
    op.add_column('registration', sa.Column('waiting_list', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('registration', 'waiting_list')
    op.create_table('waiting_list',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('registration_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['registration_id'], ['registration.id'], name='waiting_list_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='latin1',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###
