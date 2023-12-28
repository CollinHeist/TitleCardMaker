from datetime import datetime, timedelta
from enum import Enum
from json import dumps
from logging import Logger
from typing import Literal, TypedDict, TypeVar, Union

from requests import post


class State(Enum):
    FAILURE = 1
    SUCCESS = 0


_CountField = TypeVar('_CountField', bound=str)
_ListField = TypeVar('_ListField', bound=str)
_ListValue = TypeVar('_ListValue')


class FieldDict(TypedDict):
    title: str
    text: str
    inline: bool


class CountField:
    __slots__ = ('name', 'value', 'display_blank')
    def __init__(self, name: str, value: int = 0, /, *, display_blank: bool = False) -> None:
        self.name = name
        self.value = value
        self.display_blank = display_blank

    def __bool__(self) -> bool:
        return bool(self.value or self.display_blank)

    @property
    def as_field(self) -> FieldDict:
        return {
            'title': self.name,
            'text': self.value or ('None' if self.display_blank else '0'),
            'inline': True
        }

class ListField:
    __slots__ = ('name', 'values', 'display_blank')
    def __init__(self, name: str, /, *, display_blank: bool = True) -> None:
        self.name = name
        self.values = []
        self.display_blank = display_blank

    def __bool__(self) -> bool:
        return bool(self.values or self.display_blank)

    @property
    def as_field(self) -> FieldDict:
        if self.values:
            value = '- ' + '\n- '.join(self.values)
        elif self.display_blank:
            value = 'None'
        else:
            value = '0'

        return {
            'title': self.name, 'text': value, 'inline': False,
        }


class NotificationGroup:

    AVATAR = (
        'https://raw.githubusercontent.com/CollinHeist/TitleCardMaker/web-ui/'
        '.github/logos/profile.png'
    )
    EVENT_NAME = 'TitleCardMaker'

    __slots__ = (
        'title', 'log', '__count_fields', '__list_fields', 'state', '_start',
    )


    def __init__(self,
            title: str, 
            logger: Logger,
            *,
            counts: list[CountField] = [],
            lists: list[ListField] = [],
        ) -> None:
        """
        
        """

        self.title = title
        self.log = logger
        self.__count_fields = {field.name: field for field in counts}
        self.__list_fields = {field.name: field for field in lists}
        self.state = State.SUCCESS
        self._start = datetime.now()


    def increment_count(self, field_name: _CountField, /) -> None:
        """
        
        """

        self.__count_fields[field_name].value += 1


    def add_to_list(self,
            field_name: str,
            value: _ListValue,
            /,
        ) -> None:
        """
        
        """

        self.__list_fields[field_name].values.append(value)


    def debug(self, msg: str) -> None:
        self.log.debug(msg)

    def info(self, msg: str) -> None:
        self.log.info(msg)

    def warning(self, msg: str) -> None:
        self.log.warning(msg)

    def error(self, msg: str) -> None:
        self.log.error(msg)

    def critical(self, msg: str) -> None:
        self.log.critical(msg)


    def mark_failure(self):
        self.state = State.FAILURE


    @staticmethod
    def format_timedelta(td: timedelta, /) -> str:
        """
        
        """

        days, seconds = td.days, td.seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Create a formatted string
        if days > 0:
            return f"{days} days, {hours} hours, {minutes} minutes"
        if hours > 0:
            return f"{hours} hours, {minutes} minutes"
        if minutes > 0:
            return f"{minutes} minutes"

        return f"{seconds} seconds"


    @property
    def runtime(self) -> str:
        """"""

        return 'Task Finished in ' + self.format_timedelta(
            datetime.now() - self._start + timedelta(minutes=23, seconds=14)
        )

    @property
    def fields(self) -> list[FieldDict]:
        return (
            [field.as_field for field in self.__count_fields.values() if field]
            + [field.as_field for field in self.__list_fields.values() if field]
        )


    @property
    def color(self) -> str:
        return '6391d2' if self.state.value == State.SUCCESS.value else 'a84232'


    def notify(self):
        """
        
        """

        NOTIFIARR_APIKEY = '99ff70ef-1af0-4ec2-b15a-08b2010401e5'
        CHANNEL_ID = 1157119994900004994

        post(
            f'https://notifiarr.com/api/v1/notification/passthrough/{NOTIFIARR_APIKEY}',
            headers={'Content-type': 'application/json', 'Accept': 'text/plain'},
            timeout=30,
            data=dumps({
                'notification': {
                    'update': False,
                    'name': self.EVENT_NAME,
                    'event': 0
                },
                'discord': {
                    'color': self.color,
                    'text': {
                        'title': self.title,
                        'icon': self.AVATAR,
                        'content': '',
                        # 'description': args.body,
                        'fields': self.fields,
                        'footer': self.runtime,
                    },
                    'ids': {
                        'channel': CHANNEL_ID,
                    }
                }
            }),
        )



# pylint: disable=arguments-differ
class CreateTitleCardsNotification(NotificationGroup):

    def __init__(self, logger: Logger) -> None:
        super().__init__(
            title='Card Creation Task Completed',
            logger=logger,
            counts=[
                'Episode Titles Updated', 'Translations Added',
                'Source Images Downloaded', 'Invalid Card Settings', 
            ],
            lists=[],
        )


class SyncNotification(NotificationGroup):
    def __init__(self, logger: Logger) -> None:
        super().__init__(
            title='Sync Task Completed',
            logger=logger,
            counts=[
                CountField('Libraries Updated'),
                CountField('Failed Library Assignments'),
            ],
            lists=[ListField('Series Added')],
        )

    def increment_count(self,
            field_name: Union[Literal['Libraries Updated'],
                              Literal['Failed Library Assignments']],
            /,
        ) -> None:

        return super().increment_count(field_name)


    def add_to_list(self,
            field_name: Literal['Series Added'],
            value: _ListValue,
        ) -> None:
        return super().add_to_list(field_name, value)
