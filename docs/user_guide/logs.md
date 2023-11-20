---
title: Server Logs
description: >
    Viewing and filtering logs within the UI.
---

# Server Logs

TitleCardMaker keeps all log files for the system in the `config/logs`
directory -  however, you can also access, view and filter these files within
the UI by clicking the small green
<span class="example md-button">:fontawesome-solid-server:</span> server button
in the top right of the UI. It is also accessible at the `/logs` URL.

![Log Viewer](../assets/logs_light.webp#only-light){.no-lightbox}
![Log Viewer](../assets/logs_dark.webp#only-dark){.no-lightbox}

!!! note "Purpose of Logs"

    The purpose of this page is to provide you with a quick way to view and
    filter logs, it is __not__ a replacement for the actual log files. If you
    are debugging a problem, it is often better to just view the raw log files.

## Filters

There are a variety of filter options available to narrow down which log
messages are displayed. All filters are optional.

After editing any filters, you will need to refresh the log table by clicking
<span class="example md-button">:material-refresh: Refresh logs</span>.

### Message

You can enter any text in the _Message Contains_ input text box to filter out
logs which do not contain that text. This is case-insensitive.

### Context IDs

TCM applies a "context ID" to all operations performed via the UI and
internally. This ID is a pseudo-random hexstring like `0f5cecd9aff7` and are
intended to make filtering out irrelevant logs easier by looking at the messages
for one specific operation.

You may enter any number of comma-separated context IDs into the _Context IDs_
text box to filter messages associated with those contexts.

!!! tip "Table Interaction"

    To easily add a given ID as a filter, simply click on the ID in the log
    table. This will add the ID to your current filters.

### Date Range

Logs can also be filtered between a start and end time. All log messages outside
this range will be excluded. Clicking either the _Start Date_ or _End Date_
inputs will open a calendar selector in which you can narrow down your time
range.

The calendar selectors are just aids, and times can be manually entered if
desired.

!!! tip "Table Interaction"

    To easily add a date as the start or end of a date range filter, you can
    click the _Timestamp_ cell in the log table. This will add the selected date
    as the current start time, or end time (if start time is populated).

### Log Level

This is often the most critical filter. All log messages are categorized in a
level of either `Debug`, `Info`, `Warning`, `Error`, or `Critical`. Setting the
filter at a specific level will not display messages of lower priority than that
level.

By default the log table is set to `Info` mode, meaning `Debug` messages are
omitted. When debugging a problem, a good first step is to change this to
`Debug`.

!!! tip "Table Interaction"

    Clicking a _Level_ cell in the log table will set that log level as the
    current filter level.

## API Logs

If you are troubleshooting a specific issue, it can be useful to find the start
and end of the operation. TCM will log the start of all API requests with a
message _like_:

```log
Starting POST "/api/cards/key"
```

and will end it with a message _like_:

```log
Finished in 8683.2ms
```

The specific API endpoint and time will obviously vary depending on your
situation, but typically finding the start and then filtering by that
operation's Context ID is a good place to begin.
