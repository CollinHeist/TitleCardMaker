# Release Notes

## Changes between v1 and v2

TitleCardMaker was (practically) rewritten when transitioning to the Web UI in
v2.0. Because of this, there are __many__ changes - a summary of these changes
is listed below:

- YAML, as used for Preference files, Series files, as well as data files is
completely removed. All data is now stored in a SQL database.

- Templates can no longer contain arbitrary font customization. Now that Named
Fonts exist, these can be _assigned_ to a Template and used.

- Multiple Templates can be applied to a single Sync, Series, and Episode.

    - Along with this, Filters were added to Templates to give very precise
    control over when Templates become effective.

- Logos are now automatically passed into all Title cards, meaning they no
longer need to be explicity specified as a series extra.

- Series can no longer have directly assigned custom Font files - custom Font
files are reserved for Named Fonts.

- The concept of serial vs. batch "execution modes" are obsolete as TCM now runs
all primary Tasks on difference schedules.

- Syncs no longer write to YAML files, meaning a few Sync features are modified:

    - Sync mode is no longer a concept, all Syncing uses "append" mode, but
    Series can be easily deleted or batch-deleted along with a Sync.

    - Compact or verbose mode is no longer necessary as Syncing does not write
    to YAML files.

    - Per-Sync card directories are removed, as a global card directory is now
    enforced.

    - Sync exclusions can no longer by a YAML file or a specific
    Series -exclusions can only be tags, libraries, or series type.

- Libraries can no longer have arbitrary data assigned to them - libraries can
__only__ be assigned to a Series.

- The ability to specify a standalone ImageMagick Docker container is removed.
Although still relevant, a poll on the Discord revealed nobody (except myself)
used this.

- Font validation can now no longer be turned off.

- You can specify a specific folder format for Specials

- Archives have been completely removed

- Media Server specific watch styles have been removed - there is now just one
global style set.

- Any individual setting can now be explicitly overwritten per-Episode

- Custom season titles specifications can now be _mixed_ - e.g. season-level
customization like `1` and range-level customization like `s2e3-s2e5`.

- Series can now be explicitly Unmonitored to indicate they should be skipped
when TCM is processing scheduled Tasks.

- A Series can now be individually processed, without the need to process
every Series at the same time.

- The Tautulli integration now works via an explicit Webhook making direct API
requests, no longer requiring the hacky file monitoring system.

- Title Cards are now individually monitored on the Episode level for _all_ 
settings, rather than the old method of Series-level YAML change detection for
a subset of settings.

- 