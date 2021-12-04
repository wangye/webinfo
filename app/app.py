import logging
import datetime, json
from urllib.parse import urlparse
from flask import Flask, Response
from flask import request, redirect, abort, render_template_string
from xml.dom.minidom import parseString
from dicttoxml import dicttoxml
from flask.wrappers import Request
from .clientinfo import *
from .uaparser import *

Request.user_agent_class = ParsedUserAgent

app = Flask(__name__)
app.config['DEBUG'] = True
app.url_map.strict_slashes = False

# https://stackoverflow.com/questions/40365390/trailing-slash-in-flask-route
@app.before_request
def clear_trailing():
    rp = request.path 
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])

logger = logging.getLogger("app.py")

@app.errorhandler(404)
def page_not_found(e):
    # Even though Flask logs it by default, 
    # I prefer to have a logger dedicated to 404
    logger.warning('404: {0}'.format(request.url))
    return 'Not found', 404

_INFO_CALLAPI_MAP = {
    "ip": get_ipaddress,
    "cn": lambda request, default : get_geoinfo(request, "country", "name", default),
    "cc": lambda request, default : get_geoinfo(request, "country", "code", default),
    "c3": lambda request, default : get_geoinfo(request, "country", "code3", default),
    "ct": lambda request, default : get_geoinfo(request, "city", "name", default),
    "ua": get_useragent,
    "hn": get_hostname,
    "ts": lambda request, default : get_timestamp(),
    "dt": lambda requset, default : datetime.datetime.utcnow().strftime("%c"),
    "pt": get_remote_port,
    "os": lambda request, default : get_useragent_attr(request, 'platform', default),
    "bw": lambda request, default : get_useragent_attr(request, 'browser', default),
    "bv": lambda request, default : get_useragent_attr(request, 'version', default),
}

_INFO_ALIAS = {
    "ip": "IP Address",
    "cn": "Country Name",
    "cc": "Country Code",
    "c3": "Country Code 3",
    "ct": "City Name",
    "ua": "User Agent",
    "hn": "Host Name",
    "ts": "Current Timestamp (UTC)",
    "dt": "Current Date Time (UTC)",
    "pt": "Remote Port",
    "os": "Platform Name",
    "bw": "Browser Name",
    "bv": "Browser Version",
}

_FULL_TEMPLATE = r"""# (C) {{year}} Wangye.Org. All rights reserved.
#
# This file contains the request client IP address, Location,
# User-Agent, and detect which is a mobile device or not. 
# I kept it simple for the programmer or any other system
# administrators' use.
# For system administrators who use curl :
#
#   curl {{hostname}}/info       # Full information
#   curl {{hostname}}/info.txt   # Full information (Plain text format)
#   curl {{hostname}}/info.json  # Full information (JSON format)
#   curl {{hostname}}/info.xml   # Full information (XML format)
#   curl {{hostname}}/info/ip    # IP address only
#   curl {{hostname}}/info/cn    # Country name only
#   curl {{hostname}}/info/cc    # Country code only
#   curl {{hostname}}/info/c3    # Country code 3 only
#   curl {{hostname}}/info/ct    # City name only
#   curl {{hostname}}/info/pt    # Remote port number only
#   curl {{hostname}}/info/hn    # Host name only
#   curl {{hostname}}/info/ua    # User-Agent only
#   curl {{hostname}}/info/os    # Platform name only
#   curl {{hostname}}/info/bw    # Browser name only
#   curl {{hostname}}/info/bv    # Browser version only
#   curl {{hostname}}/info/ts    # Current UTC Timestamp
#   curl {{hostname}}/info/dt    # Current UTC Date & Time

{{info}}

# NOTICE: This information will not be shown if you request
# this page through curl or wget client.
# If you request this page with X_REQUESTED_WITH header set to
# XMLHttpRequest, This page "/info" will display in JSON format.
#
# For more information please visit https://wangye.org
# Last Update: {{date}}
# EOF"""

def get_info_txt_short():
    buffer=[]
    max_alias_len = max(map(len, _INFO_ALIAS.values()))
    for k,func in _INFO_CALLAPI_MAP.items():
        value = str(func(request, 'N/A'))
        buffer.append(f"{_INFO_ALIAS[k].ljust(max_alias_len, '.')}.: {value}")
    return '\n'.join(buffer) + '\n'

def get_info_txt():
    o = urlparse(request.base_url)

    return render_template_string(
        _FULL_TEMPLATE,
        year=datetime.datetime.utcnow().year,
        info=get_info_txt_short(),
        date=datetime.datetime.utcnow().strftime("%c"),
        hostname=o.hostname,
        )

def internal_get_info_dict():
    results = {}
    for k,func in _INFO_CALLAPI_MAP.items():
        value = str(func(request, 'N/A'))
        results[k] = {
            'value' : value,
            'description': _INFO_ALIAS[k]
        }
    return results

def get_info_json():
    return json.dumps(internal_get_info_dict())

def get_info_xml():
    xml = dicttoxml(internal_get_info_dict(), attr_type = False)
    dom = parseString(xml)
    return dom.toprettyxml()

_FULLINFO_TYPES = {
    "txt": "text/plain",
    "txt_short": "text/plain",
    "json": "application/json",
    "xml": "application/xml",
}

def is_xml_http_request(request):
    requested_with = request.environ.get('HTTP_X_REQUESTED_WITH')
    if not requested_with:
        return False
    return requested_with.lower() == 'xmlhttprequest'

@app.route("/info", defaults={"extension" : None}, methods=['GET', 'POST'])
@app.route("/info.<extension>", methods=['GET', 'POST'])
def path_info(extension):
    if not extension:
        extension = 'json' if is_xml_http_request(request) else 'txt'

    if not extension.isalpha() or extension not in _FULLINFO_TYPES.keys():
        abort(404)

    if extension == 'txt' and is_cli_request(request):
        extension += '_short'

    possibles = globals().copy()
    possibles.update(locals())
    method = possibles.get(f"get_info_{extension}")
    if not method:
        raise NotImplementedError(f"Method get_info_{extension} not implemented")

    return Response(method(), mimetype=_FULLINFO_TYPES[extension], status=200)

@app.route("/info/<name>", methods=['GET', 'POST'])
def path_info_name(name):
    if name not in _INFO_CALLAPI_MAP.keys():
        abort(404)

    return str(_INFO_CALLAPI_MAP[name](request, 'N/A'))

if __name__ == "__main__":
    # use 0.0.0.0 to use it in container
    app.run(host='0.0.0.0')