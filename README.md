# slack-automated-archiving

## Requirements:
* Python 3+
* Install requirements.txt (pip install -r requirements.txt)
* An OAuth token for a Slack App installed on the desired workspace with permission scopes:
  * channels:history
  * channels:read
  * channels:write
  * chat:write:bot
  * chat:write:user

## Configuration:
* The __TOKEN__ must be exposed as an environment variable before running. 
* Users can also specify as environment variables, if they choose:
    * __TIME_INACTIVE__: number of days a channel must be inactive for in order to archive it (default = 180)
    * __ADMIN_CHANNEL__: the channel ID for a channel to receive a Slack message containing the results of the process (default = ‘’)
    * __MIN_MEMBERS__: the minimum number of members a channel can have to exempt it from archival (default = 0)
    * __WHITELIST__: specific words the program will look for in a channels name that if found will exclude the channel from archival (default = ‘’)
    * __IGNORE_PURPOSE__: A keyword that can be included in a channels purpose or topic that will exempt the channel from archival (default = ‘%noarchive’)
* Users can supply a custom message to be sent to a channel prior to being archived. This can be modified in the templates.json file in the root directory of the project. 
* In addition to or in lieu of the __WHITELIST__ environment variable, there is also a whitelist.txt that can be used the same way. Add keywords separated by a comma within this file, and the program will search for them in a channels name. If any of these keywords are found, the channel will be exempt from the archival process. 
