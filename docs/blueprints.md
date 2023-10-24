---
title: Blueprints
description: >
    Pre-made collections of Card customizations that includes Fonts, Templates,
    and card settings.
---

# Blueprints

_Blueprints_ can be viewed as amped-up Templates. These are ready-made
collections of cards configurations that apply to a single Series. Blueprints
allow for importing a pre-made customization for a Series, and can include any
of the following:

- Named Fonts - _i.e. Fonts with files_
- Templates
- Series customizations
- Episode customizations
- Source files - _i.e. logos, masks, source images, etc._

!!! example "Example"

    Don't want to spend an hour of your life combing through the Pokémon
    Wikipedia in order to determine which specific Episodes apply to which
    specific seasons? Blueprints allow you to just take the hour of my work and
    apply everything with the click of a button.

All Blueprints are hosted on the
[companion repository](https://github.com/CollinHeist/TitleCardMaker-Blueprints/)
and anyone can (and is encouraged to!) submit a Blueprint for availability
across all of TCM. This process is described
[below](#sharing-your-own-blueprint).

## Viewing Blueprints

There are two main ways of browsing Blueprints.

1. Searching for the available Blueprints for a specific Series. This is done by
going to the _Blueprints_ tab on a Series' page.

2. Viewing _all_ available Blueprints for _all_ Series. These are accessed by
going to the new/add Series page.

Some Blueprints will also have multiple preview images. This will be indicated
by a slight animation when the preview is hovered over. Clicking on the image
will then cycle through the available previews.

## Importing Blueprints

??? note "Note about Font Files"

    If the Blueprint has any Named Fonts that include custom font files, you
    might be prompted to download the Font file from a 3rd party website. This
    is sometimes required as a Font's license might not allow it to be
    redistributed by TitleCardMaker.

    TCM will import the rest of the Font customizations for you, so just be sure
    to upload the Font files before you start Title Card creation.

### By Series

To import a Blueprint for a Series, simply open the Series' page and then open
the _Blueprints_ tab. Click `Search for Blueprints`, and TCM will look for any
available Blueprints for this Series. If any are available, a preview card will
show the details.

On this card will be a preview of the Blueprint, as well as what customizations
will be imported. This can be any number of Fonts, Templates, or Episode
overrides.

After picking the Blueprint you like, simply click :material-cloud-download:
`Import` and TCM will grab and apply the Blueprint for you.

Once a Blueprint has been imported, you are free to make any edits to the
Series, Templates, or Fonts as you see fit. TitleCardMaker will not override
your changes with the Blueprint settings unless you prompt it to do so by
re-importing the Blueprint.

![](./assets/blueprint_series_light.jpg#only-light){loading=lazy}
![](./assets/blueprint_series_dark.jpg#only-dark){loading=lazy}

### Browsing

If you'd like to browse all available Blueprints, go to the new Series page
(the `/add` URL) and scroll down to the Blueprints section. After clicking
`Browse Blueprints`, preview cards for each Blueprint will be shown.

This is covered in greater detail [here](./user_guide/new_series.md).

![](./assets/blueprint_all_light.webp#only-light){loading=lazy}
![](./assets/blueprint_all_dark.webp#only-dark){loading=lazy}

## Sharing your own Blueprint

In order to help other TitleCardMaker users, it is encouraged to share any
Blueprints you think would be valuable to others. This process is designed to be
as easy as possible.

!!! tip "Submission Checklist"

    If you just want a quick checklist of what to do for your Blueprint
    submission, see below:

    - [x] Export your Blueprint within the TCM UI.
    - [x] Choose an effective preview image.
    - [x] [Create an issue](https://github.com/CollinHeist/TitleCardMaker-Blueprints/issues/new?assignees=CollinHeist&labels=blueprint&projects=&template=new_blueprint.yml&title=%5BBlueprint%5D+)
    on the Blueprints repository (this should be started for you).
    - [x] Fill out the issue form's required data:
        - [x] Series name, year, your username, and the blueprint description
        - [x] Copy/paste the contents of the exported `blueprint.json` file in
        the _Blueprint File_ field.
        - [x] Upload any associated files.
            - [x] Verify any Font licenses permit the files to be shared - if
            not, [see below](#editing-the-blueprint).

### Exporting the Data

Once you've customized a Series' Cards to :pinched_fingers: _perfection_, open
it's page in TitleCardMaker, and then go to the _Blueprints_ tab. Click the
:fontawesome-solid-file-export: `Export` button, and TCM will do a few things:

1. If the Series (or any linked Templates) have a Named Font -  __this includes
those linked directly to Episodes__ - it will copy any Font files;
2. Search for and copy the first available[^1] Title Card for the Series;
3. Convert the Series, Templates, Fonts, and Episode customizations into a
Blueprint "object" written as JSON.
4. All of the above data is bundled (and sub-bundled) into a `.zip` file and
downloaded through your browser.
5. Finally, TCM will open a new tab to GitHub and begin filling out the
Blueprint submission form (if you are logged in).

### Editing the Blueprint

Before submitting the Blueprint to the repository, it's best to double-check the
data in the Blueprint for validity.

1. Review that the Preview image is appropriate, present, and representative of
the Blueprint.

    ??? question "No Preview Image Present?"

        If TCM did not include a `preview` file in the zip, then there were no
        valid Cards for it to export. You can grab any existing Card in its
        place.

    ??? tip "Changing the Preview"

        TCM only automatically chooses a Card for you in order to be helpful.
        You can pick any Card you'd like for the preview.

5. Verify the actual contents of the Blueprint. Any customizations can be
edited, removed, or adjusted. But to prevent any errors, it's best to edit these
values within TCM itself and then just re-export the Blueprint.

6. Verify the Licenses for any exported Font files. Please only upload the file
if the author's license is listed as open and/or free for public
(non-commercial) use and distribution.

    === ":octicons-check-16: Font is Public"

        If the Font is public, then you are free to include the Font file itself
        inside the Blueprint. Please take note (either the URL or a screenshot)
        of the License to be included in the Issue if needed.

    === ":octicons-x-16: Font is Not Public"

        If the Font is _not_ public, **do not** include the Font file in the
        Blueprint. Remove reference to this file from the `blueprint.json` file,
        and you can include a URL where TCM users can find the Font themselves
        under the `file_download_url` field. For example:

        ```json title="blueprint.json" hl_lines="8-9"
        {
            "series": {},
            "episodes": {},
            "templates": [],
            "fonts": [
                {
                    "name": "Better Call Saul",
                    "file": "script-casual-normal.ttf", // (1)
                    "file_download_url": "https://www.google.com/" // (2)
                }
            ]
        }
        ```

        1.  _Delete_ this line.
        2. _Add_ this line with the URL for your specific Font.

    === ":octicons-question-16: Cannot Find License"

        If you cannot find the applicable license for a Font, assume the Font
        is not public and follow those instructions.

### Submitting the Blueprint

With this Blueprint, the next (and final) step is to submit it to the Blueprints
repository.

1. Open a [new issue](https://github.com/CollinHeist/TitleCardMaker-Blueprints/issues/new?assignees=CollinHeist&labels=blueprint&projects=&template=new_blueprint.yml&title=%5BBlueprint%5D+)
on the Blueprints GitHub repository - this should have been started for you.

2. Fill out the form with the relevant information.

3. Paste the contents of the exported `blueprint.json` file into the _Blueprint
File_ field.

4. Upload a preview Title Card into the _Preview Title Card_ section of the form.

5. The last step is only applicable to Blueprints _with_ custom Font files:

    === "No Font Files"

        If your Blueprint does not have any custom Font files, you can skip this
        step.

    === "Font Files"

        If you have at least one Font file - then you need to drag/drop or
        attach that zipped file into the _Zip of Font Files_ field.

        ??? question "Why is this necessary?"

            This is required because GitHub only allows directly uploading files
            of specific extensions, and Font extensions are not on that list.

5. Click the _Submit new issue_ button.

!!! success "Success"

    After the issue is created, there is an automated action that will validate
    your submission (check for syntax errors, bad file uploads, missing preview,
    etc.). If this passes, then your work is done and the Blueprint will be
    available within TCM shortly.

[^1]: TCM will only grab Title Cards that are not blurred or grayscale, and not
any Cards from Specials (season 0).