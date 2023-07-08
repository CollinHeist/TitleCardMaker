# Blueprints

!!! warning "Under Construction"

    This documentation is actively being developed.

_Blueprints_ can be viewed as Templates on steroids. These are ready-made
collections of cards configurations that apply to a single Series. These allow
for importing a pre-made customization for a Series, including any applicable
Named Fonts, Templates, Series options, _and_ Episode-specific overrides.

??? example "Example"

    Don't want to spend an hour of your life combing through the Pokémon
    Wikipedia in order to determine which specific Episodes apply to which
    specific seasons? Blueprints allow you to just take the hour of my work and
    apply everything with the click of a button.

    ![](./assets/example_blueprints.png)

All Blueprints are hosted on the
[companion repository](https://github.com/CollinHeist/TitleCardMaker-Blueprints/)
and anyone can (and is encouraged to!) submit a Blueprint for availability
across all of TCM. This process is described [below]().

## Importing a Blueprint

To import a Blueprint for a Series, simply open the Series' page and then open
the _Blueprints_ tab. Click `Search for Blueprints`, and TCM will look for any
available Blueprints for this Series. If any are available, a card will show you
the details.

On this card will be a preview of the Blueprint, as well as what customizations
will be imported. This can be any number of Fonts, Templates, or Episode
overrides.

After picking the Blueprint you like, simply click :material-cloud-download:
`Import` and TCM will grab and apply the Blueprint for you.

!!! note "Note about Font Files"

    If the Blueprint has any Named Fonts that include custom font files, you
    might be prompted to download the Font file from a 3rd party website. This
    is sometimes required as a Font's license might not allow it to be
    redistributed by TitleCardMaker.

    TCM will import the rest of the Font customizations for you, so just be sure
    to upload the Font files before you start Title Card creation.

Once a Blueprint has been imported, you are free to make any edits to the
Series, Templates, or Fonts as you see fit. TitleCardMaker will not override
your changes with the Blueprint settings unless you prompt it to do so by
re-importing the Blueprint.

## Sharing your own Blueprint

In order to help other TitleCardMaker users, it is encouraged to share any
Blueprints you think would be valuable to others. This process is designed to be
as easy as possible.

### Getting the Data

Once you've customized a Series' Cards to :pinched_fingers: _perfection_, open
it's page in TitleCardMaker, and then go to the _Blueprints_ tab. Click the
:fontawesome-solid-file-export: `Export Blueprint` button, and TCM will do a few
things:

1. If the Series (or any linked Templates) have a Named Font -  __this includes
those linked directly to Episodes__ - it will copy any Font files;
2. Search for and copy the first available[^1] Title Card for the Series;
    
    !!! tip "Changing this Preview Card"

        TCM only chooses a Card for you in order to be helpful. You can pick
        any Card you'd like for the preview.

3. Convert the Series, Templates, Fonts, and Episode customizations into a
Blueprint "object" written as JSON.

All of this data is then bundled into a `.zip` file and downloaded through your
browser. This is (practically) all you need in order to submit the Blueprint.

### Submitting the Blueprint

With this zipped Blueprint, the next (and final) step is to submit it to the
Blueprints repository.

1. Open [the repository](https://github.com/CollinHeist/TitleCardMaker-Blueprints/).

2. Log into (or create) your GitHub account.

3. _Fork_ the main repository by clicking the :octicons-repo-forked-16: `Fork`
button in the top right (next to the :star: `Star` - *wink wink*). Hit
`Create Fork`.

4. Once forked, clone this repository:

    ```bash
    git clone ... # (1)!
    ```

    1.  Using _your_ Repository name here.

5. ...

!!! warning "Font Licences"

    Verify the Licences for any exported Fonts _before_ including them in your
    Pull Request.

[^1]: TCM will only grab Title Cards that are not blurred or grayscale, and not
any Cards from Specials (season 0).