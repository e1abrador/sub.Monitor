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
- Notify api configuration file.
- You will need to specify the binary and config paths on **sub.monitor-config.ini** file.
- Finally, execute ``pip3 install -r requirements.txt``

You can easily implement your own tools on the script, just modify the lines of code:

````python
def run_tool(tool, domain, output_file):
    print(f'[{datetime.datetime.now()}] - Running {tool} on {domain}')
    if tool == 'assetfinder':
        assetfinder_binary = config.get('Binary paths', 'assetfinder')
        cmd = f'echo {domain} | {assetfinder_binary} -subs-only | grep -E "{domain}$" |grep -v "*" | grep -v "@"'
    elif tool == 'subfinder':
        subfinder_binary = config.get('Binary paths', 'subfinder')
        subfinder_api = config.get('Api', 'subfinder_api')
        cmd = f'{subfinder_binary} -d {domain} -silent -pc {subfinder_api} -all'
    elif tool == 'amass':
        amass_binary = config.get('Binary paths', 'amass')
        amass_api = config.get('Api', 'amass_api')
        cmd = f'{amass_binary} enum -passive -norecursive -noalts -d {domain} -config {amass_api}'
    elif tool == 'my-custom-tool':
        my-custom-tool-binary = config.get('Binary paths', 'my-custom-tool-binary-or-script')
        cmd = f'{my-custom-tool-binary} -d {domain}'
````

Also add your tool name here:

````python
                for tool in ['subfinder', 'amass', 'assetfinder', 'my-custom-tool-name']:
                    run_tool(tool, domain, output_file)
````

The only needed thing is that once the command is finished, it must show on the output all the domains discovered so the tool can save them on the logs file and inside the database

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

````console
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

ibm.com [9 subdomains added manually] [2 subdomains discovered] [11 total unique in database]

````

Once it has been correctly loaded, the monitoring process can start. It is recommended to use TMUX in a VPS and leave it running for a long time. With the following command, the script will be running the subdomain enumeration tools and will compare the new results with the old results. If there's any new subdomain found, sub.Monitor will first add it to the local database (so it will not notify anymore about that discovery) and then will notify the user via slack/telegram/discord.

````console
python3 monitor.py -d ibm.com -h 8
````

If any subdomain is found, sub.Monitor will show the following message on the output:

````console
➜ python3 monitor.py -d ibm.com -h 12

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

It is also possible to monitor more than 1 domain, with the following command:

````console
python3 monitor.py -df root-domains.txt -h 8
````

After those messages are reported, on the same time the user will recieve the notifications on telegram

![image](https://github.com/e1abrador/sub.Monitor/assets/74373745/c67ceb5f-da77-4aed-ab28-73f32421273f)

How do I manage the notifications? I found a pretty easy (and easy to manage) way to see all new discovered domains with discord. I got this (blurred since all of them are private programs):

![image](https://github.com/e1abrador/sub.Monitor/assets/74373745/e82a94ea-3310-48ad-a2aa-0f40a6b29637)

The idea is first create a category regarding the program name:

\> Yahoo

--- yahoo.com
  
--- yahoo.net
  
--- etc ...
  
\> IBM

--- ibm.com
  
--- whateverdomain.com
  
--- etc ...

This is how my notify config file looks like:

![image](https://github.com/e1abrador/sub.Monitor/assets/74373745/1f060b91-01a2-4790-8663-d2535b58bc4e)

I recommend to do this for each domain (it may be pretty tedious to set up this but it is a great way to manage the results). monitor.py script will send the results to the given webhook based on the ID (which must be the same as the domain name to scan).

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

You can also use the following command to see the day on which the domain was discovered:

````console
python3 monitor.py -d ibm.com --dump --info

          _    ___  ___            _ _
          | |   |  \/  |           (_) |
 ___ _   _| |__ | .  . | ___  _ __  _| |_ ___  _ __
/ __| | | | '_ \| |\/| |/ _ \| '_ \| | __/ _ \| '__|
\__ \ |_| | |_) | |  | | (_) | | | | | || (_) | |
|___/\__,_|_.__/\_|  |_/\___/|_| |_|_|\__\___/|_|

                    github.com/e1abrador/sub.Monitor

Subdomains for ibm.com:
test.ibm.com [discovered on 06/08/2023]
test2.ibm.com [discovered on 08/08/2023]
````

  ## Thanks
  
  Thanks to:
  
  - Projectdiscovery for creating [subfinder](https://github.com/projectdiscovery/subfinder) and [notify](https://github.com/projectdiscovery/notify)!.
  - Thanks to OWASP for their amazing project [amass](https://github.com/owasp-amass/amass/)!.
  - Tomnomnom for creating [assetfinder](https://github.com/tomnomnom/assetfinder)!.

## TODO

- Implement the monitoring of more than 1 subdomain. [DONE] 
- Continously read the domain files so new domains can be scanned without stopping the program. [DONE]

If you have any idea of some new functionality open a PR at https://github.com/e1abrador/sub.Monitor/pulls.

Good luck and good hunting!
If you really love the tool (or any others), or they helped you find an awesome bounty, consider [BUYING ME A COFFEE!](https://www.buymeacoffee.com/e1abrador) ☕ (I could use the caffeine!)

⚪ e1abrador

<a href='https://www.buymeacoffee.com/e1abrador' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi2.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
