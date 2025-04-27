import logging
logger = logging.getLogger(__name__)
from playwright.sync_api import Locator

from pillepas.automation.proxy_classes import Proxy
from pillepas.automation.make_proxies import proxy_factory


class FormGateway(dict[str, Proxy]):
    """Helper class that contains proxies for each form element, and methods
    for iterating over the ones that are present on the current page, etc."""

    def __init__(self, element: Locator):
        super().__init__()
        self.element = element
        
        for key, proxy in proxy_factory(elem=self.element):
            self[key] = proxy
        #
    #
    
    def present_fields(self):
        for key, proxy in self.items():
            if proxy.is_present():
                yield key
            #
        #
    
    def __repr__(self):
        return self.__class__.__name__
    
    def signature(self) -> int:
        """Returns a distinct integer which depends on the combination of fields that are currently visible.
        This can be used as a kind of signature, to differentiate between the various pages of a form"""
        
        bits = []
        for key, proxy in sorted(self.items()):
            present = proxy.is_present()
            bits.append(present)
        
        bin_str = "".join((str(int(p)) for p in bits))
        res = int(bin_str, 2)
        return res
    #


if __name__ == '__main__':
    pass
