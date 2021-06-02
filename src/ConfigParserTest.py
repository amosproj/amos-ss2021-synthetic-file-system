import BackendManager
from BackendFactoryManager import BackendFactoryManager
from BackendManager import BackendManager
import MDHBackendFactory  # this is not actually unused. This import triggers the auto registration of the factory
import PassthroughBackendFactory

"""
TEST FILE UNTIL THE PROPER CONFIG PARSER IS DONE!!!!
THIS FILE WILL BE REMOVED
"""


def test_setup():
    backfacman: BackendFactoryManager = BackendFactoryManager()
    backendfac = backfacman.get_factory_for_config_tag("MDH")
    backend = backendfac.create_backend_from_section(section="")
    BackendManager().add_backend(backend)