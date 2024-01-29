---
title: The Scheduler
description: >
    The schedulable Tasks which automatically perform all major operations.
---

# The Scheduler

TitleCardMaker runs all core tasks on schedulable intervals. These can be
adjusted by accessing the Scheduler page under `Settings` > `Scheduler` (or at
the `/scheduler` URL).

The Scheduler can be in one of two modes: basic (the default) mode, and advanced
mode. These two modes can be switched between at any point by clicking the green
button at the bottom of the page. All intervals are reset when switching from
basic to advanced mode.

!!! tip "Minimum Task Frequency"

    In both modes, the fastest a single Task can be scheduled is once every 10
    minutes.
    
    TCM will also not start a Task while it is already running, so if a given
    Task takes longer than its assigned frequency, the second run will be
    skipped.

## Basic Mode

While in basic mode, all scheduled Tasks happen on fixed intervals. These
intervals are relative to whenever you first launch TCM (i.e. they are not
guaranteed to start at the top of the hour). In addition to this, only a subset
of the total available Tasks (the most commonly adjusted ones) are displayed.

![](../assets/scheduler_basic_light.webp#only-light){.no-lightbox}
![](../assets/scheduler_basic_dark.webp#only-dark){.no-lightbox}

How often these Tasks occur can be changed by editing the text in the
_Frequency_ column of the table. This information can be entered as text, and
any combination of "seconds", "minutes", "hours", "days", and "weeks" are
supported. 

!!! example "Example Frequency"

    A frequency string can be as simple as `4 hours`, or as complex as
    `1 day 4 hours 12 minutes 23 seconds`. 

## Advanced Mode

In advanced mode, scheduled Tasks happen according to a "cron" expression. These
are expressions which allow for succinctly describing when something can occur,
and can be as simple as `*/30 * * * *` - meaning "every 30 minutes" - to as
complex as `0 2 * * 1-5` - meaning "at 02:00 AM, Monday through Friday".

Advanced mode also make _all_ Tasks available to be rescheduled.

![](../assets/scheduler_advanced_light.webp#only-light){.no-lightbox}
![](../assets/scheduler_advanced_dark.webp#only-dark){.no-lightbox}

When Tasks run can be adjusted by editing the cron expression in the _Schedule_
column of the table. A live human-readable description of the expression is
given in the next column. There are many online resources to creating cron
expressions, but a [helpful resource](https://crontab.guru/) is linked at the
bottom of the page.
