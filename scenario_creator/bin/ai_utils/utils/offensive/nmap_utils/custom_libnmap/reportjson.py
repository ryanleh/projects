#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from ai_utils.utils.offensive.nmap_utils.custom_libnmap.objects import NmapHost, NmapService, NmapReport
from ai_utils.utils.offensive.nmap_utils.custom_libnmap.objects.os import NmapOSFingerprint, NmapOSMatch, NmapOSClass
from ai_utils.utils.offensive.nmap_utils.custom_libnmap.objects.os import CPE, OSFPPortUsed
from ai_utils.utils.offensive.nmap_utils.custom_libnmap.parser import NmapParser


class ReportEncoder(json.JSONEncoder):
    def default(self, obj):
        otype = {'NmapHost': NmapHost,
                 'NmapOSFingerprint': NmapOSFingerprint,
                 'NmapOSMatch': NmapOSMatch,
                 'NmapOSClass': NmapOSClass,
                 'CPE': CPE,
                 'OSFPPortUsed': OSFPPortUsed,
                 'NmapService': NmapService,
                 'NmapReport': NmapReport}
        if isinstance(obj, tuple(otype.values())):
            key = ('__{0}__').format(obj.__class__.__name__)
            return {key: obj.__dict__}
        return json.JSONEncoder.default(self, obj)


class ReportDecoder(json.JSONDecoder):
    def decode(self, json_str):
        r = NmapParser.parse_fromdict(json.loads(json_str))
        return r
