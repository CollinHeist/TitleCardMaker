from sqlalchemy.orm import Session

from app.dependencies import get_preferences
from app.models.connection import Connection
from app.schemas.preferences import EpisodeDataSourceToggle


def get_episode_data_sources(db: Session) -> list[EpisodeDataSourceToggle]:
    """
    Get the list of Episode data sources.

    Args:
        db: Database to query for Connections

    Returns:
        List of episode data source details for all enabled Connections.
    """

    return [
        EpisodeDataSourceToggle(
            interface=connection.interface_type,
            interface_id=connection.id,
            name=connection.name,
            selected=get_preferences().episode_data_source == connection.id,
        )
        for connection in db.query(Connection).all()
    ]
