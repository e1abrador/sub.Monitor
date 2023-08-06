import os
import argparse
import sqlite3
import subprocess
import time
import datetime
import tldextract
import configparser

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
        cursor.execute('CREATE TABLE IF NOT EXISTS subdomains (subdomain TEXT, added_manually INTEGER, discovered INTEGER)')

def get_known_subdomains():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT subdomain FROM subdomains')
        return [row[0] for row in cursor.fetchall()]

def insert_subdomains(subdomains, manually=False):
    unique_subdomains = list(set(subdomains))
    known_subdomains = get_known_subdomains()
    
    new_subdomains = [sub for sub in unique_subdomains if sub not in known_subdomains]
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.executemany('INSERT INTO subdomains VALUES (?, ?, ?)', [(sub, int(manually), int(not manually)) for sub in new_subdomains])
    
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
        print(f"{domain} [{manually} subdomains added manually] [{discovered} subdomains discovered] [{manually + discovered} total unique in database]")

def count_total_unique_subdomains():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT subdomain) FROM subdomains')
        return cursor.fetchone()[0]

def notify(subdomain, domain):

    notify_binary = config.get('Binary paths', 'notify')
    notify_api = config.get('Api', 'notify_api')
    command = f'echo "Subdomain {subdomain} has been discovered! for {domain}" | {notify_binary} -silent -config {notify_api}'
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def run_tool(tool, domain, output_file):
    print(f'[{datetime.datetime.now()}] - Running {tool} on {domain}')
    if tool == 'assetfinder':
        cmd = f'assetfinder --subs-only {domain}'
    elif tool == 'subfinder':
        cmd = f'subfinder -d {domain} -silent'
    elif tool == 'amass':
        cmd = f'amass enum -passive -d {domain}'
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

def dump_subdomains(domain):
    known = get_known_subdomains()
    print(f"Subdomains for {domain}:")
    for subdomain in known:
        if domain in subdomain:
            print(subdomain)

def main():
    print_banner()
    initialize_db()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--add', help='Domain to scan')
    parser.add_argument('--file', help='File with known subdomains')
    parser.add_argument('-d', help='Domain to scan')
    parser.add_argument('-h', type=int, help='Hours between scans')
    parser.add_argument('--dump', action='store_true', help='Dump all subdomains for a specific domain')
    parser.add_argument('--list', action='store_true', help='List all root domains in the database')
    parser.add_argument('-df', help='File with domains to scan')
    parser.add_argument('-help', '-?', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    args = parser.parse_args()

    if args.add and args.file:
        with open(args.file) as f:
            num_inserted = insert_subdomains(f.read().splitlines(), manually=True)
            print(f'[{datetime.datetime.now()}] - {num_inserted} subdomains were added to the local database.')
    elif args.df and args.h:
        while True:
            with open(args.df) as f:
                domains = f.read().splitlines()
            for domain in domains:
                output_file = f'logs/{domain}_results_log.txt'
                if os.path.exists(output_file):
                    os.remove(output_file)

                known = get_known_subdomains()
                for tool in ['subfinder', 'amass']:
                    run_tool(tool, domain, output_file)

                with open(output_file) as f:
                    for line in f:
                        new_subdomain = line.strip()
                        if new_subdomain not in known:
                            notify(new_subdomain, domain)
                            print(f'[{datetime.datetime.now()}] - New subdomain {new_subdomain} discovered')
                            insert_subdomains([new_subdomain], manually=False)
            time.sleep(args.h * 60 * 60)
    elif args.dump and args.d:
        dump_subdomains(args.d)
    elif args.list:
        list_domains()


if __name__ == "__main__":
    main()
