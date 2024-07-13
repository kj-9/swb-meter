from dataclasses import dataclass
from enum import Enum

from swb_meter.logger import logger


@dataclass
class ParsedManufacturerData:
    company_code: str
    mac_address: str


@dataclass
class DeviceType:
    name: str
    mode: str
    code: str


@dataclass
class Group:
    A: bool
    B: bool
    C: bool
    D: bool


@dataclass
class TempAlert(Enum):
    NO_ALERT = 0
    LOW_TEMP_ALERT = 1
    HIGH_TEMP_ALERT = 2
    TEMP_ALERT = 3


@dataclass
class HumidAlert(Enum):
    NO_ALERT = 0
    LOW_HUMIDITY_ALERT = 1
    HIGH_HUMIDITY_ALERT = 2
    HUMIDITY_ALERT = 3


@dataclass
class TemperatureScale(Enum):
    CELSIUS = 0
    FAHRENHEIT = 1


@dataclass
class Temperature:
    value: float
    scale: str


@dataclass
class ParsedServiceData:
    uuid: str
    device_type: DeviceType
    group: Group
    battery: int
    temperature_alert: str
    humidity_alert: str
    temperature: Temperature
    humidity: int


@dataclass
class ParsedAdvertisementData:
    local_name: str
    rssi: int
    tx_power: int
    service_uuids: list
    manufacturer_data: ParsedManufacturerData
    service_data: ParsedServiceData


# SwitchBot Meter Service Data UUID
SERVICE_DATA_UUID = "0000fd3d-0000-1000-8000-00805f9b34fb"

# SwitchBot Company Code
COMPANY_CODE = "0x969"


def get_device_type(type_code):
    device_types = {
        0x48: ("SwitchBot Bot (WoHand)", None),
        0x42: ("WoButton", None),
        0x4C: ("SwitchBot Hub (WoLink)", "Add Mode"),
        0x6C: ("SwitchBot Hub (WoLink)", "Normal Mode"),
        0x50: ("SwitchBot Hub Plus (WoLink Plus)", "Add Mode"),
        0x70: ("SwitchBot Hub Plus (WoLink Plus)", "Normal Mode"),
        0x46: ("SwitchBot Fan (WoFan)", "Add Mode"),
        0x66: ("SwitchBot Fan (WoFan)", "Normal Mode"),
        0x74: ("SwitchBot MeterTH (WoSensorTH)", "Add Mode"),
        0x54: ("SwitchBot MeterTH (WoSensorTH)", "Normal Mode"),
        0x4D: ("SwitchBot Mini (HubMini)", "Add Mode"),
        0x6D: ("SwitchBot Mini (HubMini)", "Normal Mode"),
    }
    return device_types.get(type_code, ("Unknown Device", None))


def parse_advertisement_data(
    advertisement_data,
    service_data_uuid=SERVICE_DATA_UUID,
):
    manufacturer_data = None

    # manufacturer_dataは, {会社コード: データ}の辞書
    # eg: {76: b'\x16\x08\x00\x98\x91\xb4j\xd8\x11\xfc'}
    for company_code_bin, data in advertisement_data.manufacturer_data.items():
        # int as byte to hex string
        company_code = hex(company_code_bin)

        if company_code != COMPANY_CODE:
            logger.debug(f"Company code does not match: {company_code}")
            return

        # switchbot meterのmacアドレスを取得
        mac_address = ":".join([f"{b:02X}" for b in data[:6]])

        manufacturer_data = ParsedManufacturerData(
            company_code=company_code, mac_address=mac_address
        )

    service_data = None

    for uuid, data in advertisement_data.service_data.items():
        # Service Data UUIDが一致しない場合はスキップ
        if not uuid or uuid != service_data_uuid:
            return

        # Byte 0: Device Type
        device_type_code = data[0] & 0x7F
        device_name, mode = get_device_type(device_type_code)
        device_type = DeviceType(
            name=device_name, mode=mode, code=hex(device_type_code)
        )

        # Byte 1: Status
        status = data[1]
        group = Group(
            A=bool(status & 0x01),
            B=bool(status & 0x02),
            C=bool(status & 0x04),
            D=bool(status & 0x08),
        )

        # Byte 2: Battery
        battery = data[2] & 0x7F

        # Byte 3: Temperature Alert, Humidity Alert, Temperature Decimal
        temp_alert = (data[3] >> 6) & 0x03
        humid_alert = (data[3] >> 4) & 0x03
        temp_decimal = data[3] & 0x0F

        temperature_alert = TempAlert(temp_alert).name
        humidity_alert = HumidAlert(humid_alert).name

        # Byte 4: Temperature
        temp_positive = bool(data[4] & 0x80)
        temp_integer = data[4] & 0x7F

        # Byte 5: Temperature Scale and Humidity
        humidity = data[5] & 0x7F

        # Calculate full temperature
        temperature = temp_integer + (temp_decimal / 10)
        if not temp_positive:
            temperature = -temperature

        temperature = Temperature(
            value=temperature, scale=TemperatureScale(data[5] & 0x80).name
        )

        service_data = ParsedServiceData(
            uuid=uuid,
            device_type=device_type,
            group=group,
            battery=battery,
            temperature_alert=temperature_alert,
            humidity_alert=humidity_alert,
            temperature=temperature,
            humidity=humidity,
        )

    # 何も取得できなかった場合はNoneを返す
    if not manufacturer_data or not service_data:
        logger.debug("No data in advertisement data")
        return

    parsed_data = ParsedAdvertisementData(
        local_name=advertisement_data.local_name,
        rssi=advertisement_data.rssi,
        tx_power=advertisement_data.tx_power,
        service_uuids=advertisement_data.service_uuids,
        manufacturer_data=manufacturer_data,
        service_data=service_data,
    )

    return parsed_data
