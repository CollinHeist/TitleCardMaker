# Tautulli

!!! info "Optional Step"

    This step is completely optional, and only those with both Plex media
    servers and Tautulli should continue.

!!! question "Why Connect to Tautulli?"

    Typically, TitleCardMaker creates and loads Title Cards on an
    [adjustable schedule](../scheduler.md). However, TCM is able to set up a
    Notification Agent on Tautulli so that it can notify TCM __immediately__
    after new Episodes are available, or an existing Episode has been watched.

1. Click the `Create Notification Agent` button.
2. In the launched window, enter the _root_ URL to your instance of Tautulli.

    ??? example "Example URL"

        Although your local IP address will obviously be different, this IP
        should be _like_ `http://192.168.0.29:8181/`.

3. Open the Tautull WebUI, and navigate to the Settings by clicking the 
:fontawesome-solid-gears: Gear icon in the top right.
4. From the left navigation bar, open the `Web Interface` settings.
5. Scroll to the bottom, and ensure the `Enable API` checkbox is checked, then
show and copy the generated API key.

    ??? danger "Security Warning"

        Keep this API key private, as it can be used to remotely access and
        modify Tautulli.

6. Back within TitleCardMaker, paste the API key from Step 5 into the API key
input box.
7. Enter some descriptive name (or leave the default), and then click the
`Create Agent` button.
8. Open Plex (on a computer) and navigate to your server settings via the
:material-wrench-outline: Wrench icon in the top right corner.
9. From the left navigation bar, scroll down to `Library` under the `Settings`
section and take note of your `Video Played Threshold` setting.
10. Back in Tautulli, open the `General` settings from the sidebar, and find the
`TV Episode Watched Percent` setting. Set this to 1-2% _higher_ than the Plex
setting from Step 9.

    ??? example "Example Setting"

        For a Plex played threshold of 90%, the appropriate Tautulli setting is
        91% or 92%.

    ??? question "Why is this Necessary?"
    
        Because this integration is so fast (typically triggering within 5
        seconds of finishing an Episode) - it is imperative that Tautulli
        triggers TCM to update a Title Card _after_ an Episode's watch-status
        has had time to update within Plex.