"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}
${"from modules.Debug import contextualize" if upgrades or downgrades else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    % if upgrades:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')
    ${upgrades}
    log.debug(f'Upgraded SQL Schema to Version[{revision}]')
    % else:
    pass
    % endif


def downgrade() -> None:
    % if downgrades:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')
    ${downgrades}
    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
    % else:
    pass
    % endif
