import os
import argparse
import sqlite3
import subprocess
import time
import datetime
import tldextract
import configparser
import fnmatch

DATABASE = 'subdomains.db'
DB_NAME = 'subdomains.db'

config = configparser.ConfigParser()
config.read('sub.monitor-config.ini')

def print_banner():
    print(r'''
          _    ___  ___            _ _
          | |   |  \/  |           (_) |
 ___ _   _| |__ | .  . | ___  _ __  _| |_ ___  _ __
/ __| | | | '_ \| |\/| |/ _ \| '_ \| | __/ _ \| '__|
\__ \ |_| | |_) | |  | | (_) | | | | | || (_) | |
|___/\__,_|_.__/\_|  |_/\___/|_| |_|_|\__\___/|_|

                    github.com/e1abrador/sub.Monitor
    ''')

def initialize_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS subdomains 
                          (subdomain TEXT, added_manually INTEGER, 
                           discovered INTEGER, discovered_on TEXT, out_of_scope INTEGER)''')

def load_out_of_scope_patterns(filename):
    with open(filename, 'r') as f:
        return f.read().splitlines()

def is_out_of_scope(subdomain, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(subdomain, pattern):
            return True
    return False

def get_known_subdomains():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT subdomain FROM subdomains')
        return [row[0] for row in cursor.fetchall()]

def insert_subdomains(subdomains, out_of_scope_domains=[], manually=False):
    unique_subdomains = list(set(subdomains))
    known_subdomains = get_known_subdomains()

    new_subdomains = [sub for sub in unique_subdomains if sub not in known_subdomains]
    current_date = datetime.datetime.now().strftime('%d/%m/%Y')  # Get the current date

    def is_out_of_scope(subdomain):
        return any(fnmatch.fnmatch(subdomain, pattern) for pattern in out_of_scope_domains)

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Include the discovery date when inserting a new subdomain
        cursor.executemany('INSERT INTO subdomains VALUES (?, ?, ?, ?, ?)', 
                           [(sub, int(manually), int(not manually), current_date, int(is_out_of_scope(sub))) for sub in new_subdomains])

    return len(new_subdomains)

def list_domains():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT subdomain, added_manually, discovered FROM subdomains')
        subdomains = cursor.fetchall()

    domains = dict()
    for sub, manually, discovered in subdomains:
        extracted = tldextract.extract(sub)
        domain = f"{extracted.domain}.{extracted.suffix}"

        if domain not in domains:
            domains[domain] = [0, 0]
        domains[domain][0] += manually
        domains[domain][1] += discovered

    total_unique = count_total_unique_subdomains()
    for domain, (manually, discovered) in domains.items():
        print(f"{domain} [{manually + discovered} total unique in database] [{manually} subdomains added manually] [{discovered} subdomains discovered]")

def count_total_unique_subdomains():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT subdomain) FROM subdomains')
        return cursor.fetchone()[0]

def notify(subdomain, domain):
    notify_binary = config.get('Binary paths', 'notify')
    notify_api = config.get('Api', 'notify_api')
    command = f'echo "Subdomain {subdomain} has been discovered!" | {notify_binary} -silent -config {notify_api} -id {domain}'
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def run_tool(tool, domain, output_file):
    print(f'[{datetime.datetime.now()}] - Running {tool} on {domain}')
    if tool == 'assetfinder':
        assetfinder_binary = config.get('Binary paths', 'assetfinder')
        cmd = f'echo {domain} | {assetfinder_binary} -subs-only | grep -E ".{domain}$" |grep -v "*" | grep -v "@" | sort -u'
    elif tool == 'subfinder':
        subfinder_binary = config.get('Binary paths', 'subfinder')
        subfinder_api = config.get('Api', 'subfinder_api')
        cmd = f'{subfinder_binary} -d {domain} -silent -pc {subfinder_api} -all'
    elif tool == 'amass':
        amass_binary = config.get('Binary paths', 'amass')
        amass_api = config.get('Api', 'amass_api')
        cmd = f'{amass_binary} enum -passive -norecursive -noalts -d {domain} -config {amass_api}'
    else:
        return
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.decode().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error while running {cmd}: {str(e)}")
        return
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open(output_file, "a") as f:
        for subdomain in result:
            print(subdomain, file=f)

def dump_subdomains(domain, show_info=False, inscope=False):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        sql_query = '''SELECT * FROM subdomains WHERE subdomain LIKE ?'''
        cursor.execute(sql_query, (f'%{domain}%',))
        results = cursor.fetchall()

        for result in results:
            subdomain, added_manually, discovered, discovered_on, out_of_scope_db = result

            if inscope and out_of_scope_db:  # if the --inscope flag is provided, and the subdomain is out of scope, then skip it
                continue

            out_of_scope_string = "[Out of scope]" if out_of_scope_db else ""

            if show_info:
                print(f"{subdomain} [discovered on {discovered_on}] {out_of_scope_string}")
            else:
                print(f"{subdomain} {out_of_scope_string}")

def print_subdomain(subdomain, date, show_info, out_of_scope_val):
    out_of_scope_str = '[Out of scope]' if out_of_scope_val == 1 else ''
    if show_info:
        print(f"{subdomain} [discovered on {date}] {out_of_scope_str}")
    else:
        print(subdomain)

def set_scope_based_on_file(subdomain):
    with open('outscope.txt', 'r') as file:
        outscope_domains = file.readlines()

    return 0 if subdomain + '\n' in outscope_domains else 1

def parse_out_of_scope(file_path):
    with open(file_path, 'r') as file:
        return file.read().splitlines()

def is_out_of_scope(subdomain, out_of_scope_list):
    for pattern in out_of_scope_list:
        # Check if the pattern is a wildcard like *.preprod.example.com
        if pattern.startswith('*.') and subdomain.endswith(pattern[1:]):
            return True
        # Check if the pattern is a wildcard like v1-*.preprod.example.com
        elif '*.' in pattern and pattern.replace('*.', '') in subdomain:
            return True
        # Direct match
        elif pattern == subdomain:
            return True
    return False

def load_out_of_scope_patterns(filename):
    with open(filename, 'r') as f:
        return f.read().splitlines()

def main():
    print_banner()
    initialize_db()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--add', help='Domain to scan')
    parser.add_argument('--out-scope', help='File with out-of-scope domains')
    parser.add_argument('--file', help='File with known subdomains')
    parser.add_argument('-D', '--domain', help='Domain to scan')
    parser.add_argument('-H', '--hours', type=int, help='Hours between scans')
    parser.add_argument('--dump', action='store_true', help='Dump all subdomains for a specific domain')
    parser.add_argument('--list', action='store_true', help='List all root domains in the database')
    parser.add_argument('-df', help='File with domains to scan')
    parser.add_argument('--inscope', action='store_true', help='Dump only in-scope domains')
    parser.add_argument('--notinscope', action='store_true', help='Dump only out-of-scope domains')
    parser.add_argument('--dumpall', action='store_true', help='Dump all subdomains with their details')
    parser.add_argument('--info', action='store_true', help='Show discovery date for subdomains')
    parser.add_argument('-help', '-?', action='help', default=argparse.SUPPRESS, help='Show this help message and exit')
    args = parser.parse_args()

    if args.add and args.file:
        out_scope_rules = []
        if args.out_scope:
            out_scope_rules = load_out_of_scope_patterns(args.out_scope)
        with open(args.file) as f:
            num_inserted = insert_subdomains(f.read().splitlines(), out_of_scope_domains=out_scope_rules, manually=True)
            print(f'[{datetime.datetime.now()}] - {num_inserted} subdomains were added to the local database.')

    elif args.df and args.hours:
        while True:
            with open(args.df) as f:
                domains = f.read().splitlines()
            for domain in domains:
                output_file = f'logs/{domain}_results_log.txt'
                if os.path.exists(output_file):
                    os.remove(output_file)

                known = get_known_subdomains()
                for tool in ['subfinder', 'amass', 'assetfinder']:
                    run_tool(tool, domain, output_file)

                with open(output_file) as f:
                    for line in f:
                        new_subdomain = line.strip()
                        if new_subdomain not in known:
                            notify(new_subdomain, domain)
                            print(f'[{datetime.datetime.now()}] - New subdomain {new_subdomain} discovered')
                            insert_subdomains([new_subdomain], manually=False)
            time.sleep(args.hours * 60 * 60)

    elif args.domain and args.hours:
        domain = args.domain
        while True:
            output_file = f'logs/{domain}_results_log.txt'
            if os.path.exists(output_file):
                os.remove(output_file)

            known = get_known_subdomains()
            for tool in ['subfinder', 'amass', 'assetfinder']:
                run_tool(tool, domain, output_file)

            with open(output_file) as f:
                for line in f:
                    new_subdomain = line.strip()
                    if new_subdomain not in known:
                        notify(new_subdomain, domain)
                        print(f'[{datetime.datetime.now()}] - New subdomain {new_subdomain} discovered')
                        insert_subdomains([new_subdomain], manually=False)
            time.sleep(args.hours * 60 * 60)

    elif args.dump and args.domain:
        dump_subdomains(args.domain, show_info=args.info, inscope=args.inscope)

    elif args.list:
        list_domains()

if __name__ == "__main__":
    main()
