import ldap

from django.conf import settings
from django.utils.encoding import smart_str


def get_attrs_of_sciper(sciper):
    con = ldap.initialize(settings.LDAP)
    con.simple_bind()

    base_dn = 'c=ch'
    filter = '(uniqueIdentifier=' + str(sciper) + ')'
    attrs = ['sn', 'givenName', 'mail']

    for someone in con.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs):
        name = someone[1]['sn'][0].split(',')[0]
        firstname = someone[1]['givenName'][0].split(',')[0]
        email = someone[1]['mail'][0]

    return (name, firstname, email)


def search_sciper(s):

    con = ldap.initialize(settings.LDAP)
    con.simple_bind()

    base_dn = 'c=ch'
    filter = '(|(cn=*%s*)(uniqueIdentifier=%s))' % (smart_str(s), smart_str(s))
    attrs = ['uniqueIdentifier', 'sn', 'givenName', 'mail']

    results = {}

    for someone in con.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs):
        try:
            sciper = someone[1]['uniqueIdentifier'][0]
            name = someone[1]['sn'][0].split(',')[0]
            firstname = someone[1]['givenName'][0].split(',')[0]
            email = someone[1]['mail'][0]

            results[sciper] = (sciper, firstname, name, email)
        except:
            pass

        if len(results) >= 7:
            return results

    return results
