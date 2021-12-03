#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re

INTERNET_PROTOCOL_V4 = 0x00001
INTERNET_PROTOCOL_V6 = 0x00002

_PATTERN_IPV4 = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')
def is_ipaddress(value, options = dict(version=INTERNET_PROTOCOL_V4|INTERNET_PROTOCOL_V6)):

    if not bool(value):
        return False
        
    results = {}
    if options['version'] & INTERNET_PROTOCOL_V4:
        results[INTERNET_PROTOCOL_V4] = False
        if '.' in value and _PATTERN_IPV4.search(value):
            results[INTERNET_PROTOCOL_V4] = True
            
    if options['version'] & INTERNET_PROTOCOL_V6:
        results[INTERNET_PROTOCOL_V6] = False
        if len(value)<=40 and ':' in value and value.count('::') < 2 and ':::' not in value:
            ipv6_patterns = map(re.compile, [
                r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$',
                r'^((?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4})*)?)::((?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4})*)?)$',
                r'^((?:[0-9A-Fa-f]{1,4}:){6,6})(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$',
                r'^((?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4})*)?) ::((?:[0-9A-Fa-f]{1,4}:)*)(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$',
            ])
            
            for ipv6_pattern in ipv6_patterns:
                if ipv6_pattern.search(value):
                    results[INTERNET_PROTOCOL_V6] = True
                    break
                    
    return any(results.values())

_PATTERN_USERAGENT = re.compile(r'^[a-zA-Z0-9\/\\\.\(\); \-_\*\?\+@\=\:,]*')
def is_useragent(value):

    if not bool(value):
        return False
    
    return _PATTERN_USERAGENT.search(value)

_PATTERN_HOSTNAME = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
def is_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present

    return all(_PATTERN_HOSTNAME.match(x) for x in hostname.split("."))