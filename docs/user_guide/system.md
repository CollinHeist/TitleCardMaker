---
title: System Summary
description: >
    Viewing the system details.
---

# System Summary

The System page shows high-level details of TitleCardMaker, provides helpful
links to various TCM-resources, and displays all system backups.

![System Page](./assets/system-light.webp#only-light){.no-lightbox}
![System Page](./assets/system-dark.webp#only-dark){.no-lightbox}

## System Details

### Current Version

What version of TitleCardMaker you are _currently_ running.

If you updated and do __not__ see this version number change, verify you have
properly shutdown and restarted TitleCardMaker for those changes to take effect.

### Execution Mode

Whether TCM is being executed in Docker or non-Docker mode.

### Database Schema

The current version of the SQL database being used.

### Uptime

How long TCM has been running.

## Links

Relevant links for the TCM project.

## System Backups

TitleCardMaker will periodically take system backups of your SQL database and
global settings (see [the scheduler](./scheduler.md)), as well as perform a
system backup before attempting any SQL database migrations (which might occur
when updating TCM). These backups will be kept for 21 days by default, but this
can be adjusted with an
[environment variable](./index.md#environment-variables).

These backups are stored in `config/backups`, but each backup can be restored-
from or deleted via the table.

!!! warning "Restoring from a Backup"

    It is generally inadvisable to attempt to restore to a backup whose
    _Database Schema_ does not match your current version, as these data
    migrations are often not reversible, and this can result in TCM data loss.
