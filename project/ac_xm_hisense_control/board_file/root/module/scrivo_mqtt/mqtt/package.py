
import struct
from .utils import pack_variable_byte_integer, pack_str16
from .property import Property

from scrivo import logging
log = logging.getLogger("MQTT")


class PackageFactory:

    @classmethod
    def build_properties_data(cls, properties_dict, protocol_version):
        if protocol_version < 5:
            return bytearray()
        data = bytearray()
        for property_name, property_value in properties_dict.items():
            packet_property = Property.factory(name=property_name)
            if packet_property is None:
                log.warning('PackageFactory: property {} is not supported, it was ignored'.format(property_name))
                continue
            property_bytes = packet_property.dumps(property_value)
            data.extend(property_bytes)
        result = pack_variable_byte_integer(len(data))
        result.extend(data)
        return result


class MQTTPacket(PackageFactory):

    @staticmethod
    def ping():
        # command = 0xC0 #11000000 PINGREQ
        return struct.pack('!BB', 0xC0, 0)

    @classmethod
    def subscribe(cls, sbt, protocol, mid, **kwargs):

        command = 0x80 ##SUBSCRIBE fixed header 0x80 + 0010 reserved
        remaining_length = 2
        topics = []
        for s in sbt:
            remaining_length += 2 + len(s.topic) + 1
            topics.append(s.topic)

        properties = cls.build_properties_data(kwargs, protocol.ver)
        remaining_length += len(properties)
        command = command | 0 << 3 | 0 << 2 | 1 << 1 | 0 << 0

        packet = bytearray()
        packet.append(command)
        packet.extend(pack_variable_byte_integer(remaining_length))
        packet.extend(struct.pack("!H", mid))
        packet.extend(properties)

        for s in sbt:
            pack_str16(packet, s.topic)
            subscribe_options = s.retain_handling_options << 4 | s.retain_as_published << 3 | s.no_local << 2 | s.qos
            packet.append(subscribe_options)

        log.debug("[SUBSCRIBE] mid: {},  topic: {} ,packet: {}".format(mid, topics, packet))

        return packet


    @classmethod
    def publish(cls, msg, mid, protocol):

        command = 0x30  # 00110000
        command = command | ((msg.dup & 0x1) << 3) | (msg.qos << 1) | (msg.retain & 0x1)

        packet = bytearray()
        packet.append(command)

        remaining_length = 2 + len(msg.topic) + msg.payload_size
        prop_bytes = cls.build_properties_data(msg.properties.a_dict(), protocol.ver)
        remaining_length += len(prop_bytes)
        #bytearray(b'1"\x00\x19dev/pc_iot_control/status\x00online')
        #bytearray(b'1"\x00\x19dev/pc_iot_control/status\x00online')
        if msg.qos > 0:
            # For message id
            remaining_length += 2

        packet.extend(pack_variable_byte_integer(remaining_length))
        pack_str16(packet, msg.topic)

        if msg.qos > 0:
            # For message id
            packet.extend(struct.pack("!H", mid))

        packet.extend(prop_bytes)
        try:
            packet.extend(msg.payload)
        except Exception as e:
            log.error(e)
            log.error(msg.payload)
#        packet.extend(msg.payload)

        # log.debug("[PUBLISH] topic: {} , msg: {} ,packet: {}".format(msg.topic, msg.payload, packet))

        return packet



    @classmethod
    def login(cls, client_id, username, password, clean_session, keepalive, protocol, will_message=None, **kwargs):
        # MQTT Commands CONNECT
        command = 0x10  # CONNECT

        remaining_length = 2 + len(protocol.name) + 1 + 1 + 2 + 2 + len(client_id)

        connect_flags = 0
        if clean_session:
            connect_flags |= 0x02 #clean session

        #will_message
        if will_message:
            will_prop_bytes = cls.build_properties_data(will_message.properties.a_dict(), protocol.ver)
            remaining_length += 2 + len(will_message.topic) + 2 + len(will_message.payload) + len(will_prop_bytes)
            connect_flags |= 0x04 | ((will_message.qos & 0x03) << 3) | ((will_message.retain & 0x01) << 5)


        #user
        if username is not None:
            remaining_length += 2 + len(username)
            connect_flags |= 0x80
            if password is not None:
                connect_flags |= 0x40
                remaining_length += 2 + len(password)

        packet = bytearray()
        packet.append(command)

        prop_bytes = cls.build_properties_data(kwargs, protocol.ver)
        remaining_length += len(prop_bytes)

        packet.extend(pack_variable_byte_integer(remaining_length))
        packet.extend(struct.pack("!H" + str(len(protocol.name)) + "sBBH",
                                  len(protocol.name),
                                  protocol.name,
                                  protocol.ver,
                                  connect_flags,
                                  keepalive))
        packet.extend(prop_bytes)

        pack_str16(packet, client_id)

        if will_message:
            packet += will_prop_bytes
            pack_str16(packet, will_message.topic)
            pack_str16(packet, will_message.payload)

        if username is not None:
            pack_str16(packet, username)

            if password is not None:
                pack_str16(packet, password)

        return packet

