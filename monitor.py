import os
import argparse
import sqlite3
import subprocess
import time
import datetime
import tldextract
import configparser

DATABASE = 'subdomains.db'

config = configparser.ConfigParser()
config.read('config/sub.monitor-config.ini')

def print_banner():
    print('''
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
        cursor.execute('CREATE TABLE IF NOT EXISTS subdomains (subdomain TEXT)')

def get_known_subdomains():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT subdomain FROM subdomains')
        return [row[0] for row in cursor.fetchall()]

def insert_subdomains(subdomains):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.executemany('INSERT INTO subdomains VALUES (?)', [(subdomain,) for subdomain in subdomains])
    return len(subdomains)

def notify(subdomain):

    notify_binary = config.get('Binary paths', 'notify')
    notify_api = config.get('Api', 'notify_api')
    command = f'echo "Subdomain {subdomain} has been discovered!" | {notify_binary} -silent -config {notify_api}'
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def run_tool(tool: str, domain: str, output_file: str):
    with open(output_file, "a") as f:
        if tool == "assetfinder":
            assetfinder_binary = config.get('Binary paths', 'assetfinder')
            subprocess.run([assetfinder_binary, domain, "-subs-only"], stdout=f)
        elif tool == "subfinder":
            subfinder_binary = config.get('Binary paths', 'subfinder')
            subfinder_api = config.get('Api', 'subfinder_api')
            subprocess.run([subfinder_binary, '-silent', '-all', '-d', domain, "-pc", subfinder_api], stdout=f)
        elif tool == "amass":
            amass_binary = config.get('Binary paths', 'amass')
            amass_api = config.get('Api', 'amass_api')
            subprocess.run([amass_binary, 'enum', '-passive', '-norecursive', '-config', amass_api, '-noalts', '-d', domain], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def dump_subdomains(domain):
    known = get_known_subdomains()
    print(f"Subdomains for {domain}:")
    for subdomain in known:
        if domain in subdomain:
            print(subdomain)

def list_domains():
    subdomains = get_known_subdomains()
    domains = set()
    for sub in subdomains:
        extracted = tldextract.extract(sub)
        domain = f"{extracted.domain}.{extracted.suffix}"
        domains.add(domain)
    print("\n".join(sorted(domains)))

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
    parser.add_argument('-help', '-?', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    args = parser.parse_args()

    if args.add and args.file:
        with open(args.file) as f:
            num_inserted = insert_subdomains(f.read().splitlines())
            print(f'[{datetime.datetime.now()}] - {num_inserted} subdomains were added to the local database.')
    elif args.d and args.h:
        output_file = 'results_log.txt'
        while True:
            if os.path.exists(output_file):
                os.remove(output_file)

            known = get_known_subdomains()
            for tool in ['assetfinder', 'subfinder', 'amass']:
                run_tool(tool, args.d, output_file)

            with open(output_file) as f:
                for line in f:
                    new_subdomain = line.strip()
                    if new_subdomain not in known:
                        notify(new_subdomain)
                        print(f'[{datetime.datetime.now()}] - New subdomain {new_subdomain} discovered')
                        insert_subdomains([new_subdomain])
            time.sleep(args.h * 60 * 60)
    elif args.dump and args.d:
        dump_subdomains(args.d)
    elif args.list:
        list_domains()

if __name__ == "__main__":
    main()
