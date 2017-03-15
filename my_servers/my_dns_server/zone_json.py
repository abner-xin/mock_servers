import zone_file
import json
from logger import logger


zone_template="""{
    "empty.zone":{
                    "$origin": "empty.zone",
                    "$ttl": 0,
                    "soa": {
                        "mname": "IMSX.ROBOT.AUTOMATION.TEST.",
                        "rname": "ROOT.IMSX.COM.",
                        "serial": "20160718",
                        "refresh": 5,
                        "retry": 5,
                        "expire": 5,
                        "minimum": 86400
                    },
                    "a": [],
                    "aaaa": [],
                    "mx": [],
                    "txt": [],
                    "ptr": []
    }
}"""


class ZoneJson:
    """this case will process json zone file, refer to configs/zone_template.json"""
    def __init__(self, zonefile=None):
        self.zonefile = zonefile
        self.data = self._load()

    def _load(self):
        if self.zonefile:
            with open(self.zonefile, 'r') as f:
                return json.loads(f.read())
        else:
            return json.loads(zone_template)

    @property
    def zoneData(self):
        zone_data = []
        for json_value in self.data.values():
            zone_data.append(zone_file.make_zone_file(json_value))
        return '\r\n'.join(zone_data)

    def is_zone_exist(self, zone):
        return isinstance(self.data.get(zone, None), dict)

    def add_zone(self, zone):
        import copy
        self.data[zone] = copy.deepcopy(self.data['empty.zone'])
        self.data[zone]['$origin'] = "%s." % zone
        logger.info('added zone: %s' % zone)

    def delete_zone(self, zone):
        if zone in self.data.keys():
            del self.data[zone]
            logger.info('deleted zone: %s' % zone)

    @staticmethod
    def _get_new_record(node, record, type, priority):
        if type.lower() == 'a':
            return {'name': node, 'ip': "%s." % record}
        elif type.lower() == 'mx':
            return {'name': node, 'preference': priority, 'host': "%s." % record}
        elif type.lower() == 'txt':
            return {'name': node, 'txt': record}
        elif type.lower() == 'aaaa':
            return {'name': node, 'ip': "%s" % record}
        elif type.lower() == 'ptr':
            return {'name': node, 'host': "%s" % record}
        elif type.lower() == 'spf':
            return {'name': node, 'data': "%s" % record}
        else:
            raise ValueError("only support type: A/AAAA/MX/TXT/PTR/SPF")

    def _log_record(self, msg, node, zone, type, record, priority):
        if type.lower() == 'mx':
            logger.info('%s record: %s.%s %s %s [%s]' % (msg, node, zone, type, record, priority))
        else:
            logger.info('%s record: %s.%s %s %s' % (msg, node, zone, type, record))

    def add_record(self, zone, node, record, type='A', priority=10):
        if not self.is_zone_exist(zone):
            self.add_zone(zone)

        record_line = self._get_new_record(node, record, type, priority)

        zone_record = self.data[zone][type.lower()]
        if record_line not in zone_record:
            zone_record.append(record_line)
            self._log_record('added', node, zone, type, record, priority)

    def delete_record(self, zone, node, record, type='A', priority=10):
        if not self.is_zone_exist(zone):
            return

        record_line = self._get_new_record(node, record, type, priority)
        zone_record = self.data[zone][type.lower()]
        if record_line in zone_record:
            zone_record.remove(record_line)
            self._log_record('deleted', node, zone, type, record, priority)