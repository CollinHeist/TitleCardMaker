---
title: The Scheduler
description: >
    The basics of the schedulable Tasks which perform the primary duties of
    TitleCardMaker.
tags:
    - Tutorial
    - Scheduler
---

# Rescheduling Tasks

## Background

TitleCardMaker runs all core tasks on schedulable intervals. The default
intervals for each task is typically sufficient for most use-cases, but TCM
allows these to be adjusted to any arbitrary interval.

??? note "Default Intervals"

    Below are the default intervals for all core TCM tasks:

    | Task | Default Interval |
    | ---: | :---: |
    |  Download missing Source Images | 4 hours |
    | Load Title Cards into your Media server | 4 hours |
    | Search for title translations | 4 hours |
    | Refresh Episode data | 6 hours |
    | Run all Syncs | 6 hours |
    | Create Title Cards | 6 hours |
    | Download Series logos | 1 day |
    | Download Series posters | 1 day |
    | Check for a new version of TCM | 1 day |
    | Refresh user Card Types | 1 day |
    | Set Series ID's | 1 day |

For this part of the tutorial, we'll be adjusting the interval for how often
all Syncs are run. 

## Instructions

1. Navigate to the Scheduler page by clicking :fontawesome-solid-stopwatch:
`Scheduler` from the side navigation bar.

2. Find the task description that reads "Run all defined Syncs, adding any new
Series".

3. In the "Frequency" column, replace the existing `6 hours` text with
`4 hours 30 minutes 20 seconds`.

    ??? question "Why this interval?"

        This is a completely arbitrary interval, and was chosen just to show how
        any different interval units can be utilized.

4. Click the `Save Changes` button.

!!! success "Success"

    You have now successfully change the execution interval for a Task within
    TCM. This exact procedure can be followed to change _any_ Task interval.
