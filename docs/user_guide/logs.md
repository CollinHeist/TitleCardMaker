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

![Logs Page](./assets/logs-light.webp#only-light){.no-lightbox}
![Logs Page](./assets/logs-dark.webp#only-dark){.no-lightbox}

This page will display an interactive table of all recent log messages, all your
current log files, and a summary of any recent "Internal Server Errors."

!!! note "Purpose of Logs"

    The purpose of this page is to provide you with a quick way to view and
    filter logs, it is __not__ a replacement for the actual log files. If you
    are debugging a problem, it is often better to just view the raw log files.

## Log Messages

### Filters

There are a variety of filter options available to narrow down which log
messages are displayed. All filters are optional.

After editing any filters, you will need to refresh the log table by clicking
<span class="example md-button">:material-refresh: Refresh logs</span>.

#### Message

You can enter any text in the _Message Contains_ input text box to filter out
logs which do not contain that text. This is case-insensitive.

You may filter messages with "or" logic by entering pipe-separated (`|`) text.
For example, `Breaking Bad|Better Call Saul` will filter messages which contain
either "Breaking Bad" _or_ "Better Call Saul".

#### Context IDs

TCM applies a "context ID" to most operations performed via the UI and
internally. This ID is a pseudo-random hexstring like `0f5ce2` and is intended
to make filtering out irrelevant logs easier by looking at the messages for one
specific operation.

You may enter any number of comma-separated context IDs into the _Context IDs_
text box to filter messages associated with those contexts.

!!! tip "Table Interaction"

    To easily add a given ID as a filter, simply click on the ID in the log
    table. This will add the ID to your current filters.

Some messages do not have an ID.

#### Date Range

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

#### Log Level

This is often the most critical filter. All log messages are categorized in a
level of either `Trace`, `Debug`, `Info`, `Warning`, `Error`, or `Critical`.
Setting the filter at a specific level will not display messages of lower
priority than that level.

!!! tip "Table Interaction"

    Clicking a _Level_ cell in the log table will set that log level as the
    current filter level.

### Dynamic Links

In addition to the filter interactions described above, TCM will also
dynamically parse the log messages themselves to create links to the relevent
content. For example, a message containing `Series[1]` would dynamically become
a link to the page for the Series with an ID of 1. These links can be clicked to
navigate to the relevant page.

### API Logs

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

## Log Files

Below the table of log messages will be a table of all log files created by TCM.
By default, TCM keeps log files for up to 7 days - however, this can be adjusted
with an [environment variable](./index.md#environment-variables).

You can click the _Download_ cell to download the associated log file.

TCM will cycle log files every 24 hours _or_ 24.9 MB so they can be shared on
Discord without Nitro.

## Internal Server Errors

When an unexpected error occurs within TCM, this _usually_ indicates a bug. To
make creating bug reports easier, TCM will list all past internal server errors
on the Logs page.

Clicking the :simple-github: GitHub icon will open a new tab on the TCM GitHub
page with an issue form pre-filled with some of the applicable information. It
will also download a `.zip` file of the relevant logs, for including in the
issue.
