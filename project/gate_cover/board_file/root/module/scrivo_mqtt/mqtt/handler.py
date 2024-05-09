# Copyright (c) 2020 Viktor Vorobjov
import struct
from scrivo.dev import DataClassArg

from .utils import unpack_variable_byte_integer
from .property import Property

from scrivo import logging
log = logging.getLogger("MQTT")


class MQTTHandler:
    def __init__(self, client):
        self.client = client

    def _parse_properties(self, packet):
        if self.client.protocol.ver < 5:
            # If protocol is version is less than 5.0, there is no properties in packet
            return {}, packet
        properties_len, left_packet = unpack_variable_byte_integer(packet)
        packet = left_packet[:properties_len]
        left_packet = left_packet[properties_len:]

        properties_dict = {}
        log.debug("[Property] {}, {}".format(properties_len, packet))
        while packet:
            property_identifier, = struct.unpack("!B", packet[:1])
            property_obj = Property.factory(id_=property_identifier)
            if property_obj is None:
                log.critical('[PROPERTIES] received invalid property id {}, disconnecting'.format(property_identifier))
                return None, None
            result, packet = Property.loads(property_obj, packet[1:])
            if result:
                properties_dict[property_obj.name] = result

        properties_data = DataClassArg(**properties_dict)
        return properties_data, left_packet

    async def handler(self, m_type, m_raw):
        log.debug('[m_type] : {}'.format(m_type))

        # CONNACK 0x20:  # dec 32
        if m_type == 0x20:
            code = 1
            self.client.broker_status = 0

            try:
                (flags, code) = struct.unpack("!BB", m_raw[:2])
                log.debug('[CONNACK] flags: %s, code: %s', hex(flags), hex(code))
            except Exception as e:
                log.debug('[CONNACK] : {}'.format(e))
                pass

            # if return code not 0, something wrong, else #subscipe to topic
            if not code:
                log.info('Connected')
                self.client.open_status = 1
                self.client.broker_status = 1
                self.client.fail = 0
            else:
                log.info('Disconnected')
                await self.client.close("CONNACK - wrong")

            # May to-do with left_string
            if len(m_raw) > 2:
                properties, left_string = self._parse_properties(m_raw[2:])
                if properties is None:
                    log.info('Disconnected')
                    await self.client.close("CONNACK - props")
                self.client.properties = properties

            self.client.on_connect(self.client)


        # SUBACK 0x90 # dec 144
        elif m_type == 0x90:

            pack_format = "!H" + str(len(m_raw) - 2) + 's'
            (mid, packet) = struct.unpack(pack_format, m_raw)
            properties, packet = self._parse_properties(packet)

            pack_format = "!" + "B" * len(packet)
            get_qos = struct.unpack(pack_format, packet)

            log.debug('[SUBACK] mid: {} q: {}'.format(mid, get_qos))

            if get_qos[0] == 0:  # 0x00 - Success - Maximum QoS 0 , 0x80 - Failure
                log.debug('[SUBACK] mid: {}'.format(mid))
                self.client.fail = 0

            self.client.on_subscribe(self.client)

        #PUBLISH 0x30, 0x31 # _handle_publish_packet , retain and not retain 48 49
        elif m_type in [0x30, 0x31]:

            dup = (m_type & 0x08) >> 3
            qos = (m_type & 0x06) >> 1
            retain = m_type & 0x01

            #format / message
            try:
                pack_format = "!H" + str(len(m_raw) - 2) + 's'
                (slen, packet) = struct.unpack(pack_format, m_raw)
                pack_format = '!' + str(slen) + 's' + str(len(packet) - slen) + 's'
                (topic, packet) = struct.unpack(pack_format, packet)
            except Exception as e:
                log.warning('[ERR format/message] {}'.format(e))
                return

            #topic
            if not topic:
                log.warning('[ERR PROTO] topic name is empty')
                return

            try:
                print_topic = topic.decode('utf-8')
            except UnicodeDecodeError as exc:
                log.warning('[INVALID CHARACTER IN TOPIC] {} - {}'.format(topic, exc))
                print_topic = topic


            if qos > 0:
                pack_format = "!H" + str(len(packet) - 2) + 's'
                (mid, packet) = struct.unpack(pack_format, packet)
            else:
                mid = None

            properties, packet = self._parse_properties(packet)
            properties.dup = dup
            properties.retain = retain

            if qos == 0:
                self.client.on_message_task(client=self.client, topic=print_topic, payload=packet, qos=qos,  properties=properties)
            # elif qos == 1:
            #     # _handle_qos_1_publish_packet(mid, packet, print_topic, properties)
            #     pass
            # elif qos == 2:
            #     # _handle_qos_2_publish_packet(mid, packet, print_topic, properties)
            #     pass

        #PUBACK 0x40 # dec 64
        elif m_type == 0x40:
            pack_format = "!H" + str(len(m_raw) - 2) + 's'
            (mid, packet) = struct.unpack(pack_format, m_raw)
            self.client.on_puback(self.client, mid)

        #   PINGRESP 0xD0 # dec 208
        elif m_type == 0xD0:
            log.debug('[PING PINGRESP]')
            self.client.fail = 0



