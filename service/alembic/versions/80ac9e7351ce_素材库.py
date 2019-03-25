"""素材库

Revision ID: 80ac9e7351ce
Revises: bacb2617af3f
Create Date: 2019-03-25 10:24:08.083485

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '80ac9e7351ce'
down_revision = 'bacb2617af3f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Dietitian',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('DTid', sa.String(length=64), nullable=False),
    sa.Column('DTname', sa.String(length=20), nullable=False),
    sa.Column('DTphone', sa.String(length=13), nullable=True),
    sa.Column('DTavatar', sa.String(length=255), nullable=False),
    sa.Column('DTqrcode', sa.String(length=255), nullable=True),
    sa.Column('DTintroduction', sa.Text(), nullable=True),
    sa.Column('DTisrecommend', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('DTid')
    )
    op.create_table('DietitianCategoryRelated',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('DCRid', sa.String(length=64), nullable=False),
    sa.Column('DTid', sa.String(length=64), nullable=False),
    sa.Column('MCid', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('DCRid')
    )
    op.create_table('Material',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('MTid', sa.String(length=64), nullable=False),
    sa.Column('MTauthor', sa.String(length=64), nullable=False),
    sa.Column('MTauthorname', sa.String(length=128), nullable=True),
    sa.Column('MTauthoravatar', sa.String(length=255), nullable=True),
    sa.Column('MTtitle', sa.String(length=128), nullable=False),
    sa.Column('MTcontent', mysql.LONGTEXT(), nullable=True),
    sa.Column('MTtext', sa.Text(), nullable=True),
    sa.Column('MTpicture', mysql.LONGTEXT(), nullable=True),
    sa.Column('MTvideo', mysql.LONGTEXT(), nullable=True),
    sa.Column('MTviews', sa.Integer(), nullable=True),
    sa.Column('MTfakeviews', sa.Integer(), nullable=True),
    sa.Column('MTfakefavorite', sa.Integer(), nullable=True),
    sa.Column('MTforward', sa.Integer(), nullable=True),
    sa.Column('MTfakeforward', sa.Integer(), nullable=True),
    sa.Column('MTstatus', sa.Integer(), nullable=True),
    sa.Column('MTisrecommend', sa.Boolean(), nullable=True),
    sa.Column('MTsort', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('MTid')
    )
    op.create_table('MaterialCategory',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('MCid', sa.String(length=64), nullable=False),
    sa.Column('MCname', sa.String(length=64), nullable=False),
    sa.Column('MCparentid', sa.String(length=64), nullable=True),
    sa.Column('MClevel', sa.Integer(), nullable=True),
    sa.Column('MCsort', sa.Integer(), nullable=True),
    sa.Column('MCtype', sa.Integer(), nullable=True),
    sa.Column('MCpicture', sa.Text(), nullable=True),
    sa.Column('MCdesc', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('MCid')
    )
    op.create_table('MaterialCategoryRelated',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('MCRid', sa.String(length=64), nullable=False),
    sa.Column('MTid', sa.String(length=64), nullable=False),
    sa.Column('MCid', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('MCRid')
    )
    op.create_table('MaterialFavorite',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('MFid', sa.String(length=64), nullable=False),
    sa.Column('MTid', sa.String(length=64), nullable=False),
    sa.Column('USid', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('MFid')
    )
    op.create_table('UserCollection',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('UCSid', sa.String(length=64), nullable=False),
    sa.Column('USid', sa.String(length=64), nullable=False),
    sa.Column('UCScollectionid', sa.String(length=64), nullable=False),
    sa.Column('UCStype', sa.Integer(), nullable=True),
    sa.Column('USCtitle', sa.String(length=125), nullable=True),
    sa.Column('USCpicture', sa.String(length=255), nullable=True),
    sa.Column('USCsummary', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('UCSid')
    )
    op.create_table('material_comment',
    sa.Column('isdelete', sa.Boolean(), nullable=True),
    sa.Column('createtime', sa.DateTime(), nullable=True),
    sa.Column('updatetime', sa.DateTime(), nullable=True),
    sa.Column('MCOid', sa.String(length=64), nullable=False),
    sa.Column('MTid', sa.String(length=64), nullable=False),
    sa.Column('MCOcontent', sa.String(length=255), nullable=True),
    sa.Column('MCOstatus', sa.Integer(), nullable=True),
    sa.Column('MCOauthor', sa.String(length=64), nullable=False),
    sa.Column('MCOauthorname', sa.String(length=128), nullable=True),
    sa.Column('MCOauthoravatar', sa.String(length=255), nullable=True),
    sa.Column('MCOistop', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('MCOid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('material_comment')
    op.drop_table('UserCollection')
    op.drop_table('MaterialFavorite')
    op.drop_table('MaterialCategoryRelated')
    op.drop_table('MaterialCategory')
    op.drop_table('Material')
    op.drop_table('DietitianCategoryRelated')
    op.drop_table('Dietitian')
    # ### end Alembic commands ###
