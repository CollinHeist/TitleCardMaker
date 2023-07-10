# Blueprints

!!! warning "Under Construction"

    This documentation is actively being developed.

_Blueprints_ can be viewed as Templates on :material-needle: steroids. These are
ready-made collections of cards configurations that apply to a single Series.
Blueprints allow for importing a pre-made customization for a Series, including
any applicable Named Fonts, Templates, Series options, _and_ Episode-specific
overrides.

??? example "Example"

    Don't want to spend an hour of your life combing through the Pokémon
    Wikipedia in order to determine which specific Episodes apply to which
    specific seasons? Blueprints allow you to just take the hour of my work and
    apply everything with the click of a button.

    ![](./assets/example_blueprints.png)

All Blueprints are hosted on the
[companion repository](https://github.com/CollinHeist/TitleCardMaker-Blueprints/)
and anyone can (and is encouraged to!) submit a Blueprint for availability
across all of TCM. This process is described
[below](#sharing-your-own-blueprint).

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

!!! tip "Submission Checklist"

    If you are already familiar with GitHub, and just want a quick checklist of
    what to do for your Blueprint submission, see below:

    - [x] Export your Blueprint within the TCM UI.
    - [x] Choose an effective preview image.
    - [x] Enter your name/username in the `creator` field of the `blueprint.json` file.
    - [x] Enter a description of the Blueprint in the `description` field.
    - [x] Verify any Font licenses permit the files to be shared.
        -  [x] If not, remove the Font file, update the `blueprint.json` file,
        add a link to the Font under the `file_download_url` field.
    - [x] Create a subfolder for the Series and its Blueprint, put the data inside.
    - [x] Submit a Pull Request with this Blueprint to the `staging` branch of the Repository.

### Exporting the Data

Once you've customized a Series' Cards to :pinched_fingers: _perfection_, open
it's page in TitleCardMaker, and then go to the _Blueprints_ tab. Click the
:fontawesome-solid-file-export: `Export Blueprint` button, and TCM will do a few
things:

1. If the Series (or any linked Templates) have a Named Font -  __this includes
those linked directly to Episodes__ - it will copy any Font files;
2. Search for and copy the first available[^1] Title Card for the Series;
3. Convert the Series, Templates, Fonts, and Episode customizations into a
Blueprint "object" written as JSON.

All of this data is then bundled into a `.zip` file and downloaded through your
browser. This is (practically) all you need in order to submit the Blueprint.

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

2. Verify the filename of the preview image is reflected in the `blueprint.json`
file. The default is `preview.jpg`, but you can change this if you wish.

    ```json title="blueprint.json" hl_lines="10"
    {
        "series": {}, // (1)
        "episodes": {},
        "templates": [],
        "fonts": [],
        "description": [
            "..."
        ],
        "creator": "CollinHeist",
        "preview": "preview.jpg"
    }
    ```

    1.  Customization not shown.

3. Put your name/username in the `creator` field of the `blueprint.json` file.
If you do not want your name listed in the UI, feel free to put mine instead.

    ```json title="blueprint.json" hl_lines="9"
    {
        "series": {}, // (1)
        "episodes": {},
        "templates": [],
        "fonts": [],
        "description": [
            "..."
        ],
        "creator": "CollinHeist",
        "preview": "preview.jpg"
    }
    ```

    1.  Customization not shown.

4. Enter a general description of the Blueprint in the `description` field. This
is a _list_, with each separate line being a separate paragraph in the UI.

    ```json title="blueprint.json" hl_lines="6-9"
    {
        "series": {}, // (1)
        "episodes": {},
        "templates": [],
        "fonts": [],
        "description": [
            "Bla bla card type that changes (x) thing and uses the (y) font.",
            "This is another paragraph of text" // (2)
        ],
        "creator": "CollinHeist",
        "preview": "preview.jpg"
    }
    ```

    1.  Customization not shown.
    2.  Note that there is **not** a trailing comma (`,`) after the last line.

5. Verify the actual contents of the Blueprint. Any customizations can be
edited, removed, or adjusted. But to prevent any errors, it's best to edit these
values within TCM itself and then just re-export the Blueprint.

6. Verify the Licenses for any exported Font files. Please only upload the file
if the author's license is listed as open and/or free for public
(non-commercial) use and distribution.

    === ":octicons-check-16: Font is Public"

        If the Font is public, then you are free to include the Font file itself
        inside the Blueprint. Please take note (either the URL or a screenshot)
        of the License to be included in the Pull Request.

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
            ],
            "description": [
                "..."
            ],
            "creator": "CollinHeist",
            "preview": "preview.jpg"
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

#### Forking the Repository

1. Open [the repository](https://github.com/CollinHeist/TitleCardMaker-Blueprints/).

2. Log into (or create) your GitHub account.

3. _Fork_ the main repository by clicking the :octicons-repo-forked-16: `Fork`
button in the top right (next to the :star: `Star` - *wink wink*). Hit
`Create Fork`.

4. Once forked, clone the forked repository:

    ```bash
    git clone ... # (1)!
    ```

    1.  Using _your_ Repository name here.

#### Adding your Blueprint

5. Use the `helper.py` file to create the required Series subfolder for the
Series whose Blueprint you are contributing. Enter the full name of the Series 
as the `Title (year)`.

    !!! example "Example"

        If I were contributing a Blueprint for _Breaking Bad (2008)_, I'd run
        the following:

        ```bash
        python3 helper.py "Breaking Bad (2008)"
        ```

        And this would make sure the folders under
        `blueprints/B/Breaking Bad (2008)/` existed.

6. Open this folder, and then create another subfolder for your Blueprint. This
will need to be numbered starting from 0, so if it's the first Blueprint for
that Series, create `0`, then `1`, `2`, etc.

    !!! example "Example"

        For the prior example, this would be the folder at
        `blueprints/B/Breaking Bad (2008)/0/` (if it were the first Blueprint).

7. Copy the contents of the zipped Blueprint folder from TCM into this
subfolder.

8. Commit your files to your Repository, then submit a Pull Request to merge
your repository into the `staging` branch of the Blueprints repository.

9. TitleCardMaker will then run various tests on your submission to verify that
it is a valid Blueprint, that you didn't add any unnecessary files, etc. If it
passes, your Blueprint has been submitted and your part is finished!

[^1]: TCM will only grab Title Cards that are not blurred or grayscale, and not
any Cards from Specials (season 0).