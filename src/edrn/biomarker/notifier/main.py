# encoding: utf-8

'''Main console entrypoint'''

from . import __version__
from ._scanner import scan, notify
import argparse, logging, pathlib

_logger = logging.getLogger(__name__)
_protocolsRDF = 'https://edrn.jpl.nasa.gov/cancerdataexpo/rdf-data/protocols/@@rdf'
_email = 'sean.kelly@jpl.nasa.gov,mryancolbert@gmail.com'
_mailHost = 'smtp.jpl.nasa.gov'


def main():
    parser = argparse.ArgumentParser(description='Get notified of changes to biomarkers')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO,
        help='🔊 Log debugging messages; handy for developers'
    )
    group.add_argument(
        '-q', '--quiet', action='store_const', dest='loglevel', const=logging.WARNING,
        help="🤫 Don't log info messages; just warnings and critical notes"
    )
    journal = pathlib.Path.home() / '.biomarker-journal'
    parser.add_argument('-j', '--journal', default=str(journal), help='📖 Journal file [%(default)s]')
    parser.add_argument('-r', '--reset', default=False, action='store_true', help='❌ Reset the journal')
    parser.add_argument('-p', '--protocols', default=_protocolsRDF, help='📓 RDF for Protocols [%(default)s]')
    parser.add_argument('-e', '--email', default=_email, help='📧 Whom to notify [%(default)s]')
    parser.add_argument('-m', '--mailhost', default=_mailHost, help='🖥 Mail host [%(default)s]')
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    journal = pathlib.Path(args.journal)
    if args.reset: journal.unlink(missing_ok=True)
    firstTime, new, changed, dropped = scan(pathlib.Path(args.journal), args.protocols)
    if firstTime or (len(new) == 0 and len(changed) == 0 and len(dropped) == 0): return
    notify(args.email, args.mailhost, new, changed, dropped)


if __name__ == '__main__':
    main()
