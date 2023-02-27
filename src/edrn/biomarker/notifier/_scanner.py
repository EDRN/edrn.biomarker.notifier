# encoding: utf-8

'''Scanner'''

from .utils import readRDF
from .classes import Protocol
from urllib.parse import urlparse
import rdflib, logging, pickle, smtplib, email

_logger = logging.getLogger(__name__)
_protocolTypeURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/types.rdf#Protocol')
_bmNamePrdicateURI = rdflib.URIRef('http://edrn.nci.nih.gov/rdf/schema.rdf#bmName')
_from = 'sean.kelly@jpl.nasa.gov'


def loadProtocols(journalFile):
    _logger.debug('🤓 Reading protocols from journal %s', journalFile)
    if journalFile.is_file():
        with journalFile.open('rb') as f:
            return pickle.load(f)
    else:
        return {}


def saveProtocols(protocols, journalFile):
    _logger.debug('💾 Saving %d protocols to journal %s', len(protocols), journalFile)
    with journalFile.open('wb') as f:
        pickle.dump(protocols, f)


def scan(journalFile, protocolsRDF):
    _logger.debug('👋 This is the scan, using %s and %s', journalFile, protocolsRDF)

    new, changed, seen = [], [], set()
    protocols = loadProtocols(journalFile)
    firstTime = len(protocols) == 0

    statements = readRDF(protocolsRDF)
    for subject, predicates in statements.items():
        typeURI = predicates.get(rdflib.RDF.type, [None])[0]
        if typeURI != _protocolTypeURI: continue
        # I thought I was being clever:
        # biomarkers = [i.strip() for i in str(predicates.get(_bmNamePrdicateURI, [''])[0]).split(',') if i.strip()]
        # But the DMCC's data *sucks*; so just treat it as plain text
        biomarkers = str(predicates.get(_bmNamePrdicateURI, [''])[0]).strip()
        title = str(predicates.get(rdflib.DCTERMS.title, ['«UNKNOWN»'])[0]).strip()

        subject = str(subject)
        seen.add(subject)
        p = protocols.get(subject)
        if p is None:
            _logger.debug('👶 New protocol %s', subject)
            p = Protocol(subject, title, biomarkers)
            new.append(p)
            protocols[subject] = p
        else:
            _logger.debug('👵 Existing protocol %s', subject)
            if biomarkers != p.biomarkers:
                _logger.debug('👛 Change to biomarkers in %s; was «%s», now «%s»', subject, p.biomarkers, biomarkers)
                updatedProtocol = Protocol(subject, title, biomarkers)
                changed.append((p, updatedProtocol))
                protocols[subject] = updatedProtocol

    existing = set(protocols.keys())
    dropped = existing - seen
    for subject in dropped:
        _logger.debug('✏️ Erasing no longer releveant protocol %s', subject)
        del protocols[subject]

    saveProtocols(protocols, journalFile)
    return firstTime, new, changed, dropped


def _friendly(uri):
    return urlparse(uri).path.split('/')[-1]


def notify(to, mailHost, new, changed, dropped):
    _logger.debug('📧 Sending notifications to %s', to)
    with smtplib.SMTP(mailHost) as mailer:
        msg = email.message.EmailMessage()
        msg['Subject'] = 'Changes detected in biomarkers listed in protocols from the DMCC'
        msg['From'] = f'DMCC Protocol Notifier <{_from}>'
        msg['To'] = to
        body = [f"👋 Greetings, {to}!\n\nI've detected some changes made at the DMCC to the biomarker annotations on protocols. The following details the changes:\n"]
        if len(new) > 0:
            body.append('\n👶 NEW PROTOCOLS\n\nThese are brand new protocols that appeared since my last scan:\n\n')
            body.append('\n'.join([f'• {_friendly(p.identifier)}: "{p.title}" (biomarkers: "{p.biomarkers}")' for p in new]))
        if len(changed) > 0:
            body.append('\n👛 CHANGED BIOMARKERS\n\nThese protocols have different biomarker annotations since the last scan:\n\n')
            for old, new in changed:
                body.append(f'• {_friendly(old.identifier)} "{old.title}":\n')
                body.append(f'    biomarkers was "{old.biomarkers}", now is "{new.biomarkers}"\n')
        if len(dropped) > 0:
            body.append("\n💀 DELETED PROTOCOLS\n\nThese protocols no longer appear in the DMCC's data:\n\n")
            body.append('\n'.join([f'• {_friendly(i)}' for i in dropped]))
        body.append('\n\n🙏 Thank you for your attention.')
        body.append('\n\nBy the way, you can search for protocols by number on the portal now. Just type the number in the search box!')
        msg.set_content(''.join(body))
        mailer.send_message(msg)
