# suwako-bot
The greatest goddess Suwako is here with some nice images to share with you! Gelbooru bot made for Discord using discord.py. Can remember your tastes so you don't have to type as much.

# How to install
Suwako comes with a run script that sets her up in a global or virtual environment. See ./run -h for some options.

After you have done the setup command, enter the config.txt file and add your bot token and some positive tags to the list. She will use these words to increese your affection with a GB tag.

Now you should be all done!

# Run as a service
Suwako now has a systemd unit file that can be used. It runs Suwako i virtual envoronment mode form the directory /opt. So make sure to clone the project to /opt if you want to use this. Run it once and set up the configuration files before you attempt to run it as a service. The unit also uses type simple so error messages won't show up in the terminal, only in the log.
