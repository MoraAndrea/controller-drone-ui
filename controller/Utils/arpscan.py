import argparse
import re
import shutil
import subprocess
import sys

class ArpScanner:
    interface = ''
    hosts = ''

    def __init__(self, interface, hosts='--localnet'):
        self.interface = interface
        self.hosts = hosts

    def scan(self):
        sudo = shutil.which('sudo')
        if not sudo:
            raise FileNotFoundError('sudo binary is needed')
        arpscan = shutil.which('arp-scan')
        if not arpscan:
            raise FileNotFoundError('arp-scan binary is needed')
        if not subprocess.getstatusoutput(sudo + ' -n true')[0] == 0:
            raise PermissionError('You must be a sudoers without password')
        pargs = [sudo, '-n', arpscan, '-I', self.interface, self.hosts]
        try:
            out = subprocess.check_output(pargs, universal_newlines=True, timeout=5)
        except subprocess.TimeoutExpired:
            pass
        re_ip = r'(?P<ip>((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9]))'
        re_mac = r'(?P<mac>([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))'
        re_hw = r'(?P<hw>[\w.]+)'
        pattern = re.compile(re_ip + '\s+' + re_mac + '\s' + re_hw)
        return [match.groupdict() for match in re.finditer(pattern, out)]

def main():
    desc = 'Command-line tool for network discovery. \
            It is a Python wrapper for arp-scan tool. \
            Both this command and sudo are needed.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('interface', help='interface to scan')
    parser.add_argument('-H', '--hosts', default='--localnet', help='host or network to scan')
    args = parser.parse_args()
    arpscan = ArpScanner(args.interface, args.hosts)
    for entry in arpscan.scan():
        print('{mac}: {ip} ({hw})'.format(**entry))

if __name__ == '__main__':
    sys.exit(main())