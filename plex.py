#!/usr/bin/python

from urllib2 import urlopen
from xml.etree import ElementTree as ET
from ssl import create_default_context, CERT_NONE

class RequestManager:
    def __init__(self):
        self.context = self._create_context()

    def _create_context(self):
        context = create_default_context()
        context.check_hostname = False
        context.verify_mode = CERT_NONE
        return context

    def perform_request(self, host, path, is_secure):
        protocol = "https" if is_secure else "http"
        url = "{}://{}/{}".format(protocol, host, path)
        return urlopen(url, context=self.context)

class DomoticzManager:
    def __init__(self, host, device_id, is_secure = False):
        self.host = host
        self.device_id = device_id
        self.is_secure = is_secure
        self.request_manager = RequestManager()

    def notify(self, message):
        self._add_log_entry(message)
        self._update_device_status(message)

    def _add_log_entry(self, message):
        path = "json.htm?type=command&param=addlogmessage&message={}".format(message)
        self.request_manager.perform_request(self.host, path, self.is_secure)

    def _update_device_status(self, message):
        path = "json.htm?type=command&param=udevice&idx={}&nvalue=0&svalue={}".format(self.device_id, message)
        self.request_manager.perform_request(self.host, path, self.is_secure)

class PlexManager:
    def __init__(self, host, is_secure = False):
        self.host = host
        self.is_secure = is_secure
        self.request_manager = RequestManager()

    def get_plex_data(self):
        response = self.request_manager.perform_request(self.host, "status/sessions", self.is_secure)
        tree = ET.parse(response)
        root = tree.getroot()

        title = self._get_plex_title(root)
        return "IDLE" if title is None else "Playing: {}".format(title)

    def _get_plex_title(self, data):
        tag = data.find("Video")
        if tag is None:
            return None

        title = tag.attrib.get("title")
        parent_title = tag.attrib.get("grandparentTitle")
        return title if parent_title is None else "{} - {}".format(title, parent_title)

class PlexToDomoticzNotifier:
    def __init__(self, plex_manager, domoticz_manager):
        self.plex_manager = plex_manager
        self.domoticz_manager = domoticz_manager

    def notify(self):
        plex_data = self.plex_manager.get_plex_data()
        self.domoticz_manager.notify(plex_data)

if __name__ == "__main__":
    plex = new PlexManager("plex-server:32400")
    domoticz = new DomoticzManager("localhost:8080", "domoticz_device_id")
    notifier = new PlexToDomoticzNotifier(plex, domoticz)
    notifier.notify()