"""volunteer change to int

Revision ID: 2c01339b154f
Revises: 134d5ced25e1
Create Date: 2024-02-28 16:29:14.559389

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c01339b154f'
down_revision = '134d5ced25e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('archive', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('community', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('pending_project', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Integer(),
               existing_nullable=True)

    with op.batch_alter_table('plan', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Integer(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('plan', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

    with op.batch_alter_table('pending_project', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

    with op.batch_alter_table('community', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

    with op.batch_alter_table('archive', schema=None) as batch_op:
        batch_op.alter_column('volunteer',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

    # ### end Alembic commands ###
