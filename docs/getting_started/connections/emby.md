---
title: Connecting to Emby
description: >
    How to connect TitleCardMaker to Emby.
tags:
    - Tutorial
    - Emby
---

# :material-emby:{.emby} Emby

!!! info "Optional Step"

    This step is completely optional, and only those with Emby media servers
    should continue.

As a Media Server, Emby can serve as an
[Episode Data Source](../../user_guide/settings.md#episode-data-source),
[Image Source](../../user_guide/settings.md#image-source-priority), and as a
location where Title Cards are uploaded to.

1. Under the Emby section, click the
<span class="example md-button">Add Connection</span> button.

2. Give this Connection some descriptive name - e.g. `Emby` - and enter the
_root_ URL to your Emby server __including the port__.

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:8096/`.

3. Open your Emby interface, and open your server Dashboard by clicking the gear
icon in the top right.

4. Scroll to the bottom of the left navigation bar, open `Api Keys` under
`Advanced`.

5. Click `+ New Api Key`, and enter some name (like `TitleCardMaker`).

6. Copy the created key, it should be a 32-character long string of numbers and
the letters between A and F.

7. Back within TitleCardMaker, paste the API key from Step 6 into the API key
input box and then click <span class="example md-button">Create</span>. TCM will
reload the page.

8. After the page has reloaded, expand the Connection form you just created and
select the username of the account you would like Episode watch-statuses to be
queried from.

9. Click <span class="example md-button">Save Changes</span>.

The above process can be repeated for as many Emby Media Servers as you have. I
do recommend specifying a _unique_ name for each Connection so they can be
easily distinguished within the UI.
