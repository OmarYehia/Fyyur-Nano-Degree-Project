"""empty message

Revision ID: 41b3b5d48176
Revises: d630f66396cc
Create Date: 2020-07-16 15:12:20.477106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41b3b5d48176'
down_revision = 'd630f66396cc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artist', sa.Column('seeking_venue', sa.Boolean(), server_default='False', nullable=True))
    op.add_column('artist', sa.Column('seeking_venue_description', sa.String(length=500), nullable=True))
    op.add_column('artist', sa.Column('website', sa.String(length=120), server_default='No Website', nullable=True))
    op.add_column('shows', sa.Column('show_date', sa.DateTime(), nullable=False))
    op.add_column('venue', sa.Column('image_link', sa.String(length=500), nullable=True))
    op.add_column('venue', sa.Column('seeking_talent', sa.Boolean(), server_default='False', nullable=True))
    op.add_column('venue', sa.Column('seeking_talent_description', sa.String(length=500), nullable=True))
    op.add_column('venue', sa.Column('website', sa.String(length=120), server_default='No Website', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'website')
    op.drop_column('venue', 'seeking_talent_description')
    op.drop_column('venue', 'seeking_talent')
    op.drop_column('venue', 'image_link')
    op.drop_column('shows', 'show_date')
    op.drop_column('artist', 'website')
    op.drop_column('artist', 'seeking_venue_description')
    op.drop_column('artist', 'seeking_venue')
    # ### end Alembic commands ###