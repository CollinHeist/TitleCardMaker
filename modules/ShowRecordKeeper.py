from pathlib import Path
from hashlib import sha256
from typing import Any

from tinydb import where

from modules.BaseCardType import BaseCardType
from modules.Debug import log
import modules.global_objects as global_objects
from modules.PersistentDatabase import PersistentDatabase

class ShowRecordKeeper:
    """
    This class describes a show record keeper. A ShowRecordKeeper
    maintains a database of hashes of Show objects for comparison.
    Specific attributes of the Show objects are hashed such that changes
    to a Show object's underlying YAML between runs will be identified
    and result in a different hash. This can/should be used to detect
    when to delete and remake cards upon changes to the YAML.

    Hashes are stored by the series' full name and associated media
    directory, so changes to the media directory will result in a NEW
    hash, not a changed one.
    """

    """Attributes of a Show object that should affect a shows record"""
    HASH_RELEVANT_ATTRIBUTES = (
        'card_class', 'episode_text_format', 'style_set.watched',
        '_Show__episode_map', 'title_languages', 'extras', 'font', 'profile',
    )

    """Record database of hashes corresponding to specified shows"""
    RECORD_DATABASE = 'show_records.json'

    """Version of the existing record database"""
    DATABASE_VERSION = 'show_records_version.txt'


    def __init__(self, database_directory: Path) -> None:
        """
        Construct a new instance. This reads the record database file if
        it exists, and creates if it does not.

        Args:
            database_directory: Base Path to read/write any databases
                from.
        """

        # Read record database
        self.records = PersistentDatabase(self.RECORD_DATABASE)

        # Read version of record database
        version = database_directory / self.DATABASE_VERSION
        if version.exists():
            self.version = version.read_text()
        else:
            self.version = global_objects.pp.version

        # Delete database if version does not match
        if self.version != global_objects.pp.version:
            self.records.reset()
            log.debug(f'Deleted show record database, was version {self.version}')

        # Write current version to file
        version.write_text(global_objects.pp.version)

        # Read and log length
        log.info(f'Read {len(self.records)} show records')


    def __get_record_hash(self, hash_obj: Any, record: Any) -> None:
        """
        Get the hash of the given record.

        Args:
            hash_obj: Initialized hash object to update with the record.
            record: Value to get the hash of. If this object is a
                subclass of the CardType abstract class, then the class
                name is hashed. If this object defines a custom_hash
                attribute, that value is hashed. Otherwise the UTF-8
                encoded string of this object is hashed.

        Returns:
            Nothing, the hash is applied to the given hash algorithm
            object.
        """

        # For CardType classes use their class name as the hash value
        if isinstance(record, type) and issubclass(record, BaseCardType):
            record = record.__name__
        # If the object defines a custom hash property/attribute, use that
        elif hasattr(record, 'custom_hash'):
            record = record.custom_hash

        # Hash this recrd (as a UTF-8 encoded string)
        hash_obj.update(str(record).encode('utf-8'))


    def __get_show_hash(self, show: 'Show') -> int: # type: ignore
        """
        Get the hash of the given config. This hash is deterministic,
        and is based only on attributes of the config that visually
        affect a card.

        Args:
            show: Show object to hash.

        Returns:
            Integer of the (SHA256) hash of the given object.
        """

        # Initialize the hash object to update with each attribute
        hash_obj = sha256()

        # Hash each relevant attribute of the Show object
        for attr in self.HASH_RELEVANT_ATTRIBUTES:
            # If a nested attribute, iterate through objects
            if '.' in attr:
                subs = attr.split('.')
                obj = getattr(show, subs[0])
                for sub_attr in subs[1:]:
                    obj = getattr(obj, sub_attr)
                self.__get_record_hash(hash_obj, obj)
            # Singular attribute, get directly from show object
            else:
                self.__get_record_hash(hash_obj, getattr(show, attr))

        # Return the hash as an integer
        return int.from_bytes(hash_obj.digest(), 'big')


    def is_updated(self, show: 'Show') -> bool: # type: ignore
        """
        Determine whether the given show is an update on the recorded
        config.

        Args:
            show: Show object being evaluated.

        Returns:
            True if the given show is different from the recorded show.
            False if the show is identical OR if there is no existing
            record.
        """

        # Condition to get the hash of this show
        condition = (
            (where('series') == show.series_info.full_name) &
            (where('directory') == str(show.media_directory.resolve()))
        )

        # If this show has an existing hash, check for equality
        if self.records.contains(condition):
            existing_hash = self.records.get(condition)['hash']
            new_hash = self.__get_show_hash(show)

            return existing_hash != new_hash

        # No existing hash
        return False


    def add_config(self, show: 'Show') -> None: # type: ignore
        """
        Add the given show's hash to this object's record database.

        Args:
            show: Show object being evaluated.
        """

        # Condition to get the hash of this show
        condition = (
            (where('series') == show.series_info.full_name) &
            (where('directory') == str(show.media_directory.resolve()))
        )

        # Either insert or update hash of this show
        self.records.upsert({
            'series': show.series_info.full_name,
            'directory': str(show.media_directory.resolve()),
            'hash': self.__get_show_hash(show),
        }, condition)
