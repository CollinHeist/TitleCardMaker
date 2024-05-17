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

TitleCardMaker runs all core tasks on schedulable intervals. The default
intervals for each task is typically sufficient for most use-cases, but TCM
allows these to be adjusted to any arbitrary interval.

For this part of the tutorial, we'll be adjusting the interval for how often all
Syncs are run. 

1. Navigate to the Scheduler page by clicking Setings, then
:fontawesome-solid-stopwatch `Scheduler` from the side navigation bar.

2. Find the task description that reads "Run all defined Syncs, adding any new
Series".

3. In the "Frequency" column, replace the existing `6 hours` text with
`4 hours 30 minutes 20 seconds`.

    ??? question "Why this interval?"

        This is a completely arbitrary interval, and was chosen just to show how
        any different interval units can be utilized.

4. Click the <span class="example md-button">Save Changes</span> button.

!!! success "Success"

    You have now successfully change the execution interval for a Task within
    TCM. This exact procedure can be followed to change _any_ Task interval.
