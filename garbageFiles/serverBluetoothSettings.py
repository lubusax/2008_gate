import sys
import array
import dbus, dbus.mainloop.glib
from gi.repository import GLib
from classesDefinitions import Advertisement
from classesDefinitions import register_ad_cb, register_ad_error_cb
from classesDefinitions import Service, Characteristic
from pprint import PrettyPrinter
import time


prettyPrint = PrettyPrinter(indent=1).pprint

BLUEZ_SERVICE_NAME =           'org.bluez'
DBUS_OM_IFACE =                'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE =           'org.bluez.GattManager1'
GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
ADAPTER_IFACE =                'org.Bluez.Adapter1'


mainloop = None

def register_app_cb(): print('GATT application registered')

def register_app_error_cb(error):
  print('Failed to register application: ' + str(error))
  mainloop.quit()

#############################################################
class TestCharacteristic(Characteristic):
    """
    Dummy test characteristic. Allows writing arbitrary bytes to its value, and
    contains "extended properties", as well as a test descriptor.
    """

    def __init__(self, bus, index, uuid, service):

        Characteristic.__init__(
                self, bus, index,
                uuid,
                #['read', 'write', 'writable-auxiliaries', 'notify'],
                ['read','write'],
                service)
        self.value = []
        self.notifying = False
        self.index = index
        #self.service= service

    def ReadValue(self, options):
        self.value= time.asctime()
        print('TestCharacteristic Read: ' + repr(self.value))
        returnValue = bytearray()
        returnValue.extend(map(ord, self.value))
        print(returnValue)
        print(type(returnValue))
        return returnValue

    def WriteValue(self, value, options):
        valueString = ""
        for i in range(0,len(value)):
            valueString+= str(value[i])
        print('TestCharacteristic on index ' +
        str(self.index) + ' was written : '+valueString)
       
        self.value = value
        self.valueString = valueString
        # if (self.index % 2) == 0:
        #     self.service.keysList.insert(self.index/2) = valueString
        # else:
        #     self.service.valuesList.insert((self.index-1)/2) = valueString

###############################################################

class TestService(Service):
	"""
	Dummy test service that provides characteristics and descriptors that
	exercise various API functionality.
	"""
	def __init__(self, bus, index):
		Service.__init__(self, bus, index,'12345678-1234-5678-1234-56789abcdfff', True)
		charUUID     = '12345678-1234-5678-1234-56789abcd800'
		#print('characteristic added: '+ charUUID )
		self.add_characteristic(TestCharacteristic(bus, 0, charUUID,self))
##################################################################
class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        #print ("*************calling_service object init for APPLICATION")
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)
        # print('appended service --- - ', service)
        # print('  service properties - ', service.get_properties())

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        #print("was here ---"*10)
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        print(response)
        return response

###################################################################
class IoTApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(TestService(bus, 0))

####################################################################
class IoTAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('5468696e-6773-496e-546f-756368000100') # ThingsInTouch - Device ID
        self.add_local_name('ThingsInTouch-Gate')
        self.include_tx_power = True

#########################################################################
def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for o, props in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in props and GATT_MANAGER_IFACE in props:
            return o
        print('Skip adapter:', o)
    return None


########################################################################
def printAppAttributes(app):
    print("#"*90)
    prettyPrint("Application Path: %s " % app.get_path())
    prettyPrint("app.__dict__.keys(): %s" % app.__dict__.keys())
    prettyPrint("app._object_path: %s " % app._object_path)    
    prettyPrint("app._name: %s " % app._name)    
    prettyPrint("app.services: %s " % app.services)
    prettyPrint("app._connection: %s " % app._connection)
    prettyPrint("app.path: %s " % app.path)
    prettyPrint("app._locations: %s " % app._locations)
    prettyPrint("app._locations_lock: %s " % app._locations_lock)
    prettyPrint("app._fallback: %s " % app._fallback)
    print("x"*80)
    print("app.GetManagedObjects(): " )
    prettyPrint( app.GetManagedObjects())
    print("#"*90) 

def printAdapterInfos(adapter):
    print("#"*90)
    print("printAdapterInfos: " )
    prettyPrint(adapter)
    print("#"*90)
     
def main():
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)

    #printAdapterInfos(adapter)

    # print('bus - ', bus)
    # print('adapter - ',adapter)

    if not adapter:
        print('BLE adapter not found')
        return

    service_manager = dbus.Interface( bus.get_object( BLUEZ_SERVICE_NAME, adapter),
                                GATT_MANAGER_IFACE)
    advertising_manager = dbus.Interface( bus.get_object( BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)
    adapter_interface = dbus.Interface( bus.get_object( BLUEZ_SERVICE_NAME, adapter),
                                ADAPTER_IFACE)                            

    #help(adapter_interface)

    # print('service_manager - ',service_manager)
    # print('ad_manager', ad_manager)

    #print("discoverable ", adapter_interface.Discoverable)

    adapter_interface.Discoverable = True
    #DiscoverableTimeout

    app = IoTApplication(bus)
    #printAppAttributes(app)


  

    #help(app)
    adv = IoTAdvertisement(bus, 0)

    mainloop = GLib.MainLoop()

    # print('mainloop - ', mainloop)
    service_manager.RegisterApplication('/', {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    # service_manager.RegisterApplication('/', {},
    #                                 ignore_reply=True)

		# the error handler quits the mainloop: mainloop.quit

    advertising_manager.RegisterAdvertisement(adv.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
    try:
        mainloop.run()
    except KeyboardInterrupt:

        adv.Release()

if __name__ == '__main__':
    main()