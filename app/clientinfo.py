import datetime
import socket, json
from ipaddress import ip_address
from .validators import is_useragent, is_ipaddress, is_hostname

_IP_SEARCH_PARAMS = (
    'HTTP_CLIENT_IP',
    'HTTP_CF_CONNECTING_IP',
    'HTTP_X_FORWARDED_FOR',
    'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTER_CLIENT_IP',
    'HTTP_X_REAL_IP',
    'HTTP_FORWARDED_FOR',
    'HTTP_FORWARDED',
    'REMOTE_ADDR'
)

def get_ipaddress(request, default=None):
    for key in _IP_SEARCH_PARAMS:
        ipaddr_str = request.environ.get(key)
        if not ipaddr_str:
            continue
        ipaddr_str = ipaddr_str.strip('\r\t\n ,')
        if ',' in ipaddr_str:
            ipaddrs = list(filter(lambda x: is_ipaddress(x), map(lambda x: x.strip(), ipaddr_str.split(','))))
            for addr_str in ipaddrs:
                if is_ipaddress(addr_str) and not ip_address(addr_str).is_private:
                    return addr_str
            continue
        else:
            if is_ipaddress(ipaddr_str) and not ip_address(ipaddr_str).is_private:
                return ipaddr_str

    return default if not request.remote_addr else request.remote_addr

def get_useragent(request, default=None):
    useragent = request.headers.get('User-Agent')
    if is_useragent(useragent):
        return useragent
    return default

def get_useragent_attr(request, attr, default=None):
    if not is_useragent(request.headers.get('User-Agent')):
        return default
    if not request.user_agent:
        return default
    return getattr(request.user_agent, attr)

def resolve_hostname(ipaddr, default=None):
    if not ipaddr:
        return default
    try:
       hname, _, _ = socket.gethostbyaddr(ipaddr)
       return hname if is_hostname(hname) else default
    except (socket.error, ValueError):
        return default
    except KeyboardInterrupt:
        raise

def get_hostname(request, default=None):
    return resolve_hostname(get_ipaddress(request), default)

def get_remote_port(request, default=None):
    remote_port = request.environ.get('REMOTE_PORT')
    if isinstance(remote_port, str):
        if not remote_port or not remote_port.isdigit():
            return default
        try:
            port = int(remote_port)
        except:
            return default
    elif isinstance(remote_port, int):
        port = remote_port

    if port < 0 or port > 65535:
        return default
    return port

def get_timestamp():
    return datetime.datetime.utcnow().timestamp()

def is_cli_request(request):
    useragent = get_useragent(request)
    if not useragent:
        return False

    return any(map(lambda x: x in useragent, ('curl/', 'libcurl/', 'wget/',)))

def get_geoinfo_summary(request, default=None):
    geoinfo = request.headers.get('X-Geo-IP')
    if not geoinfo or not isinstance(geoinfo, str) \
        or not geoinfo.startswith("{") \
            or not geoinfo.endswith("}"):
        return default

    try:
        geo = json.loads(geoinfo)
        buffer = []
        if 'country' in geo.keys():
            country = geo['country']
            s = []
            if 'name' in country.keys() and country['name']:
                s.append(f"name: {country['name']}, ")
            if 'code' in country.keys() and country['code']:
                s.append(f"code: {country['code']}, ")
            if 'code3' in country.keys() and country['code3']:
                s.append(f"code3: {country['code3']}")
            if len(s) > 0:
                buffer.append("[Country] " + ''.join(s).strip(', '))

        if 'city' in geo.keys():
            city = geo['city']
            s = []
            if 'name' in city.keys() and city['name']:
                s.append(f"name: {city['name']}")
            if len(s) > 0:
                buffer.append("[City] " + ''.join(s).strip(', '))

        return '; '.join(buffer) if len(buffer) > 0 else default

    except:
        return default

def get_geoinfo(request, section, key, default=None):
    geoinfo = request.headers.get('X-Geo-IP')
    if not geoinfo or not isinstance(geoinfo, str) \
        or not geoinfo.startswith("{") \
            or not geoinfo.endswith("}"):
        return default

    try:
        geo = json.loads(geoinfo)
        sect = geo[section]
        if key in sect.keys() and sect[key]:
            return sect[key]
    except:
        pass

    return default
    