import datetime
import socket
from .validators import is_useragent, is_ipaddress, is_hostname

_IP_SEARCH_PARAMS = (
    'HTTP_CLIENT_IP',
    'HTTP_X_FORWARDED_FOR',
    'HTTP_X_FORWARDED',
    'HTTP_X_CLUSTER_CLIENT_IP',
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
            ipaddrs = filter(lambda x: is_ipaddress(x), map(lambda x: x.strip(), ipaddr_str.split(',')))
            if len(ipaddrs) > 0:
                return ipaddrs[0]
            continue
        else:
            if is_ipaddress(ipaddr_str):
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