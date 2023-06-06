<h1 align="center">
 sub.Monitor
<br>
</h1>

<pre align="center">
<b>
   Fast & user-friendly subdomain monitoring tool for continous attack surface management.
</b>
</pre>

![image](https://github.com/e1abrador/sub.Monitor/assets/74373745/b7bfe315-fa26-4f55-b0af-5a3db4995dc0)

## Features
- **Fast**
- **Easy to use**
- **Easy to install**
- **Continously save subdomains in local database (with the possibility of dumping them all)**
- **Telegram/slack/discord notifications**

## Help Menu
**sub.Monitor** flags:

```console
options:
  --add ADD    Domain to scan
  --file FILE  File with known subdomains
  -d D         Domain to scan
  -h A         Hours between scans
  --dump       Dump all subdomains for a specific domain
  --list       List all root domains in the database
  -help, -?    Show this help message and exit
  ````
  
  ## Previous needed configurations
  
  You need to write the configuration (api) path files into **config.ini** file.
  
- [Subfinder](https://github.com/projectdiscovery/subfinder/tree/main#post-installation-instructions) api configuration file.
- [Amass](https://github.com/owasp-amass/amass/blob/master/examples/config.ini) api configuration file.
- [Notify]() api configuration file.
- Finally, you will need to specify the binary and config paths on **config/sub.monitor-config.ini** file.
 ## Work plan

First of all **sub.Monitor** needs a list of already scanned domains:

````console
➜  cat ibm_sorted_subdomains.txt
test1.ibm.com
test2.ibm.com
test3.ibm.com
subtest.testX.ibm.com
...
````

Now, the file containing the subdomanis can be passed to **sub.Monitor** with the following command:

````bash
python3 monitor.py --add ibm.com --file ibm_sorted_subdomains.txt
          _    ___  ___            _ _
          | |   |  \/  |           (_) |
 ___ _   _| |__ | .  . | ___  _ __  _| |_ ___  _ __
/ __| | | | '_ \| |\/| |/ _ \| '_ \| | __/ _ \| '__|
\__ \ |_| | |_) | |  | | (_) | | | | | || (_) | |
|___/\__,_|_.__/\_|  |_/\___/|_| |_|_|\__\___/|_|

                    github.com/e1abrador/sub.Monitor

[2023-06-06 18:16:26.002521] - 538 subdomains were added to the local database.
````

To confirm that the domain has been added to the database, execute:

```console
python3 monitor.py --list
          _    ___  ___            _ _
          | |   |  \/  |           (_) |
 ___ _   _| |__ | .  . | ___  _ __  _| |_ ___  _ __
/ __| | | | '_ \| |\/| |/ _ \| '_ \| | __/ _ \| '__|
\__ \ |_| | |_) | |  | | (_) | | | | | || (_) | |
|___/\__,_|_.__/\_|  |_/\___/|_| |_|_|\__\___/|_|

                    github.com/e1abrador/sub.Monitor

ibm.com
````

Once it has been correctly loaded, the monitoring process can start. It is recommended to use TMUX in a VPS and leave it running for a long time. With the following command, the script will be running the subdomain enumeration tools and will compare the new results with the old results. If there's any new subdomain found, sub.Monitor will first add it to the local database (so it will not notify anymore about that discovery) and then will notify the user via slack/telegram/discord.

````console
python3 monitor.py -d ibm.com -h 8
````

If any subdomain is found, sub.Monitor will show the following message on the output:

````console
➜  monitor python3 monitor.py -d ibm.com -h 12

          _    ___  ___            _ _
          | |   |  \/  |           (_) |
 ___ _   _| |__ | .  . | ___  _ __  _| |_ ___  _ __
/ __| | | | '_ \| |\/| |/ _ \| '_ \| | __/ _ \| '__|
\__ \ |_| | |_) | |  | | (_) | | | | | || (_) | |
|___/\__,_|_.__/\_|  |_/\___/|_| |_|_|\__\___/|_|

                    github.com/e1abrador/sub.Monitor

[2023-06-06 18:07:25.191169] - New subdomain xxxx.ibm.com discovered
[2023-06-06 18:07:25.353156] - New subdomain xyxyxyxyxyx.ibm.com discovered
[2023-06-06 18:07:25.641082] - New subdomain x1.xxxx.ibm.com discovered
````

After those messages are reported, on the same time the user will recieve the notifications on telegram

![image](https://github.com/e1abrador/sub.Monitor/assets/74373745/c67ceb5f-da77-4aed-ab28-73f32421273f)

Let's say that the script has been running for 2 months and you want to get all the results (old subdomains and new discovered ones). With sub.Monitor it is possible using --dump flag:

````console
python3 monitor.py -d ibm.com --dump

          _    ___  ___            _ _
          | |   |  \/  |           (_) |
 ___ _   _| |__ | .  . | ___  _ __  _| |_ ___  _ __
/ __| | | | '_ \| |\/| |/ _ \| '_ \| | __/ _ \| '__|
\__ \ |_| | |_) | |  | | (_) | | | | | || (_) | |
|___/\__,_|_.__/\_|  |_/\___/|_| |_|_|\__\___/|_|

                    github.com/e1abrador/sub.Monitor

Subdomains for ibm.com:
subdomain1.ibm.com
subdomain2.ibm.com
...
````

  ## Thanks
  
  Thanks to:
  
  - Projectdiscovery for creating [subfinder](https://github.com/projectdiscovery/subfinder) and [notify](https://github.com/projectdiscovery/notify)!.
  - Thanks to OWASP for their amazing project [amass](https://github.com/owasp-amass/amass/)!.
  - Thanks to Tomnomnom for coding [assetfinder](https://github.com/tomnomnom/assetfinder)!.
