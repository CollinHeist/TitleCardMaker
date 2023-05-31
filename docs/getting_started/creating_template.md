# Creating a Template
## Background

Templates are a critical component of quickly customizing your TitleCardMaker
setup. A Template contains a set of customized settings, and any number of
Templates can be assigned to a Sync, Series, or Episode.

For this tutorial we'll be creating two Templates with opposing settings, use
Filters to control when these Templates are applied, and in a later step we'll
apply these Templates automatically with a [Sync](./first_sync/index.md).

!!! tip "Templates versus Global Settings"
        
    Template settings always take priority over any global settings, __unless__
    the Template value is _unset_ - e.g. left blank.

## Instructions

1. Navigate to the Template page by clicking `Templates` from the side
navigation bar.

2. Create a new Template by clicking the `Create a New Template` button.

3. Expand the created Template by clicking the accordion called "Blank
Template".

4. Rename the Template "Tier 0 - Tinted Frame"

    ??? question "Why this name?"

        The name is arbitrary, but since we'll be layering these Templates in
        tiers, I find it helpful to indicate the tier within the Template name
        so that it's easier to remember when adding within the UI.

        As for "Tinted Frame", that's because we'll be using the Tinted Frame
        card type.

5. Under "Card Settings" change the card type to "Tinted Frame". 

6. Scroll down to "Miscellaneous" and then click the `Add Extra` button.

7. Enter the key as `bottom_element` and the value as `logo`.

    ??? question "What are Extras?"

        Extras are a way of overriding or customizing specific components of a
        Title Card. Extras are typically card type-specific - and in this case
        the Tinted Frame card allows changing the bottom element to a Logo
        (from index text) with the `bottom_element` extra.

        A complete list of Extras are found [here]().

8. Hit `Save Changes`.

9. Create another new Template by clicking the `Create a New Template` button.

10. Expand the Template, rename it to "Tier 1 - Standard"

11. Under "Filters", click the `Add Condition` button.

12. Select the Filter condition as `Season Number` `is less than` `3`.

13. Under "Card Settings", change the card type to "Standard".

14. Hit `Save Changes`.

!!! success "Two Templates Created"

    You have now successfully created two Templates. One of which sets the card
    type to the Tinted Frame card, and sets the bottom element to a logo. The
    other has a filter for a season number less than 3, and sets the card type
    to Standard.

    We'll use these later in the tutorial.