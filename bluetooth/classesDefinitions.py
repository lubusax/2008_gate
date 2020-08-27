#!/usr/bin/python3.5

from gi.repository import GObject
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

mainloop = None

BLUEZ_SERVICE_NAME            = 'org.bluez'
LE_ADVERTISING_MANAGER_IFACE  = 'org.bluez.LEAdvertisingManager1'
DBUS_OM_IFACE                 = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE               = 'org.freedesktop.DBus.Properties'

LE_ADVERTISEMENT_IFACE        = 'org.bluez.LEAdvertisement1'
GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'

PATH_ADVERTISEMENT            = '/org/bluez/example/advertisement'
PATH_SERVICE                  = '/org/bluez/example/service'

class Advertisement(dbus.service.Object):
  #PATH_ADVERTISEMENT = '/org/bluez/example/advertisement'

  def __init__(self, bus, index, advertising_type):
    self.path = PATH_ADVERTISEMENT + str(index)
    self.bus = bus
    self.ad_type = advertising_type
    self.service_uuids = None
    self.manufacturer_data = None
    self.solicit_uuids = None
    self.service_data = None
    self.local_name = None
    self.include_tx_power = None
    self.data = None
    dbus.service.Object.__init__(self, bus, self.path)

  def get_properties(self):
    properties = dict()
    properties['Type'] = self.ad_type
    if self.service_uuids is not None:
      properties['ServiceUUIDs'] = dbus.Array(self.service_uuids, signature='s')
    if self.solicit_uuids is not None:
      properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids, signature='s')
    if self.manufacturer_data is not None:
      properties['ManufacturerData'] = dbus.Dictionary(self.manufacturer_data, signature='qv')
    if self.service_data is not None:
      properties['ServiceData'] = dbus.Dictionary(self.service_data, signature='sv')
    if self.local_name is not None:
      properties['LocalName'] = dbus.String(self.local_name)
    if self.include_tx_power is not None:
      properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)
    if self.data is not None:
      properties['Data'] = dbus.Dictionary(self.data, signature='yv')
    return {LE_ADVERTISEMENT_IFACE: properties}

  def get_path(self):
    return dbus.ObjectPath(self.path)

  def add_service_uuid(self, uuid):
    if not self.service_uuids: self.service_uuids = []
    self.service_uuids.append(uuid)

  def add_solicit_uuid(self, uuid):
    if not self.solicit_uuids: self.solicit_uuids = []
    self.solicit_uuids.append(uuid)

  def add_manufacturer_data(self, manuf_code, data):
    if not self.manufacturer_data:
      self.manufacturer_data = dbus.Dictionary({}, signature='qv')
    self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')

  def add_service_data(self, uuid, data):
    if not self.service_data:
      self.service_data = dbus.Dictionary({}, signature='sv')
    self.service_data[uuid] = dbus.Array(data, signature='y')

  def add_local_name(self, name):
    if not self.local_name: self.local_name = ""
    self.local_name = dbus.String(name)

  def add_data(self, ad_type, data):
    if not self.data: self.data = dbus.Dictionary({}, signature='yv')
    self.data[ad_type] = dbus.Array(data, signature='y')

  @dbus.service.method(DBUS_PROP_IFACE,
                        in_signature='s',
                        out_signature='a{sv}')
  def GetAll(self, interface):
    #print('GetAll')
    if interface != LE_ADVERTISEMENT_IFACE:
      raise InvalidArgsException()
    #print('returning props')
    return self.get_properties()[LE_ADVERTISEMENT_IFACE]

  @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                        in_signature='',
                        out_signature='')
  def Release(self):
    print('%s: Released!' % self.path)

def register_ad_cb(): print('Advertisement registered')

def register_ad_error_cb(error):
  print('Failed to register advertisement: ' + str(error))
  mainloop.quit()

class Service(dbus.service.Object):
  """
  org.bluez.GattService1 interface implementation
  """
  # PATH_SERVICE = '/org/bluez/example/service'

  def __init__(self, bus, index, uuid, primary):
    self.path = PATH_SERVICE + str(index)
    self.bus = bus
    self.uuid = uuid
    self.primary = primary
    self.characteristics = []
    dbus.service.Object.__init__(self, bus, self.path)

  def get_properties(self):
    return {
            GATT_SERVICE_IFACE: {
                    'UUID': self.uuid,
                    'Primary': self.primary,
                    'Characteristics': [dbus.Array(
                            self.get_characteristic_paths(),
                            signature='o')]
            }
    }

  def get_path(self): return dbus.ObjectPath(self.path)

  def add_characteristic(self, characteristic): self.characteristics.append(characteristic)

  def get_characteristic_paths(self):
    result = []
    for chrc in self.characteristics:
      result.append(chrc.get_path())
    return result

  def get_characteristics(self): return self.characteristics

  @dbus.service.method(DBUS_PROP_IFACE,
                        in_signature='s',
                        out_signature='a{sv}')
  def GetAll(self, interface):
    if interface != GATT_SERVICE_IFACE: raise InvalidArgsException()

    return self.get_properties()[GATT_SERVICE_IFACE]

class Characteristic(dbus.service.Object):
  """
  org.bluez.GattCharacteristic1 interface implementation
  """
  def __init__(self, bus, index, uuid, flags, service):
    self.path = service.path + '/char' + str(index)
    self.bus = bus
    self.uuid = uuid
    self.service = service
    self.flags = flags
    self.descriptors = []
    dbus.service.Object.__init__(self, bus, self.path)

  def get_properties(self):
    return {
            GATT_CHRC_IFACE: {
                    'Service': self.service.get_path(),
                    'UUID': self.uuid,
                    'Flags': self.flags,
                    'Descriptors': dbus.Array(
                            self.get_descriptor_paths(),
                            signature='o')
            }
    }

  def get_path(self): return dbus.ObjectPath(self.path)

  def add_descriptor(self, descriptor): self.descriptors.append(descriptor)

  def get_descriptor_paths(self):
    result = []
    for desc in self.descriptors:
      result.append(desc.get_path())
    return result

  def get_descriptors(self): return self.descriptors

  @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
  def GetAll(self, interface):
    if interface != GATT_CHRC_IFACE: raise InvalidArgsException()

    return self.get_properties()[GATT_CHRC_IFACE]

  @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
  def ReadValue(self, options):
    print('Default ReadValue called, returning error')
    raise NotSupportedException()

  @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
  def WriteValue(self, value, options):
    print('Default WriteValue called, returning error')
    raise NotSupportedException()

  @dbus.service.method(GATT_CHRC_IFACE)
  def StartNotify(self):
    print('Default StartNotify called, returning error')
    raise NotSupportedException()

  @dbus.service.method(GATT_CHRC_IFACE)
  def StopNotify(self):
    print('Default StopNotify called, returning error')
    raise NotSupportedException()

  @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
  def PropertiesChanged(self, interface, changed, invalidated): pass

