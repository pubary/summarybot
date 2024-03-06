# Summarybot

-----

### Python application for Telegram

Bot sending messages with news summaries to the reader’s telegram in the language of his choice.
Resumes are made using the KAGI service and then translated using the DEEPL service.
News is read from links that are extracted from xml-files of news sites.


#### What do you need:

* a computer (with Windows, macOS or Linux)
* Python installed on your machine (with pip)
* accounts on kagi.com and deepl.com with payment made
* registered telegram bot


### Installation


##### Step 1: Clone Newseater from GIT:

+ create a directory for web applications in the user's home directory if it doesn't already exist:
  `~$ mkdir www`
+ go to this directory
  `~$ cd www`
+ clone the project: 
  `~/www$ git clone http://git........summarybot.git`
+ go to directory *summarybot*, which was created when cloning the application:
  `~/www$ cd summarybot`


#### Step 2: Install Python (>=3.6) and a virtual environment:

If you're on Linux or macOS you should have Python and Git installed, just check that your Python version is >= 3.6:<br>
`~$ python3 -V` <br>
On Windows you have to install it for sure.

+ download the package for creating a virtual environment corresponding to the version of python
  into the directory with the application:<br>
  `~/www/summarybot$ wget https://bootstrap.pypa.io/virtualenv/3.6/virtualenv.pyz`
+ being in the application directory, create a virtual environment named *ne-venv*:<br>
  `~/www/summarybot$ python3 virtualenv.pyz sb-venv`
+ activate the created virtual environment:<br>
  `~/www/summarybot$ source sb-venv/bin/activate`
  > If you activate the venv correctly, you will see a little *(sb-venv)* on the left side of the command line!


#### Step 3: Installing dependencies and configuring the environment:

+ install the requirements:<br>
  `~/www/summarybot$ pip install -r requirements.txt`
+ copy *exemple_.env* file as *.env*:<br>
  `~/www/summarybot$ cp exemple_.env .env`<br>
+ copy *exemple_config.py* file as *config.py*:<br>
  `~/www/summarybot$ cp exemple_config.py config.py`<br>
You need to put your data in the *.env* file after it has been created.
You can also make changes to the *config.py* file to make changes to the app. 
But to get a real summary of the news and its translation, you need the `MY_DEBUG = False` entry in this file.


#### Step 4: Start the NewsSummary app

  > All news from the xml-file are not checked for age and are marked outdated when the application is launched.
Therefore, summaries and translations will not be created for these news items.
News will be checked for age and a summary and translation will be created for them
if links to these news were added to the xml-files after launching the application.
  
Now everything is ready, and you can finally run the Newseater app in the *newseater* directory:<br>
  `~/www/summarybot$ python3 summarybot.py`
  > But if you close the terminal in which you ran the app, it will stop working. 
 
To prevent this, use for example 
  on Linux *nohup* from directory with *summarybot.py*:<br>
  `~/www/summarybot$ nohup python3 summarybot.py > summarybot.out 2>&1 &`
  
  
#### Application update

If changes have been made to the remote repository, you can update your application:<br>
  `~/www/summarybot$ git pull http://git.......summarybot.git`

But after starting the app, if you make any changes to the program files, you must restart it:
+ To do this, you must first stop the app that is already running. If the app was started with "nohup",
just type the command <br>
  `kill <pid>` (*pid* is the process ID of *python3 summarybot.py*).
  > To find the pid, run `ps -ef | grep summarybot.py`.
+ go to the *summarybot* directory with the *summarybot.py* file and activate the virtual environment,
  if it was previously deactivated for some reason:
  `~/www/summarybot$ source sb-venv/bin/activate`
+ being in the directory with the *summarybot.py* file restart the app: <br>
  `~/www/summarybot$ nohup python3 summarybot.py > summarybot.out 2>&1 &` (if using *nohup*)
