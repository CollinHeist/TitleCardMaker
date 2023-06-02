# Rescheduling Tasks

## Background

TitleCardMaker runs all core tasks on schedulable intervals. The default
intervals for each task is typically sufficient for most use-cases, but TCM
allows these to be adjusted to any arbitrary interval.

??? note "Default Intervals"

    Below are the default intervals for all core TCM tasks:

    | Task | Adjustable | Default Interval |
    | ---: | :---: | :---: |
    |  Download missing Source Images | :material-check:{.green} | 4 hours |
    | Load Title Cards into your Media server | :material-check:{.green} | 4 hours |
    | Search for title translations | :material-check:{.green} | 4 hours |
    | Refresh Episode data | :material-check:{.green} | 6 hours |
    | Run all Syncs | :material-check:{.green} | 6 hours |
    | Create Title Cards | :material-check:{.green} | 6 hours |
    | Download Series logos | :material-check:{.green} | 1 day |
    | Check for a new version of TCM | :octicons-x-16:{.red} | 12 hours |
    | Refresh user Card Types | :octicons-x-16:{.red} | 1 day |

For this part of the tutorial, we'll be adjusting the interval for how often
all Syncs are run. 

## Instructions

1. Navigate to the Scheduler page by clicking `Scheduler` from the side
navigation bar.

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

    For more detail on all the supported interval units, see [here](...).