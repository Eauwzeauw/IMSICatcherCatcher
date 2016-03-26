from __future__ import print_function
from pcapng import *
from pcapng.blocks import *
###

import sys
import io
from datetime import datetime

import pcapng
from pcapng.blocks import SectionHeader, InterfaceDescription, EnhancedPacket
from scapy.layers.l2 import Ether
import scapy.packet
# To make sure all packet types are available
import scapy.all  # noqa



class PostProcessing:

    def __init__(self):
        location = '/home/eauwzeauw/IMSI/captures/22-03-2016_21:20:48/capture0_932000000.pcapng'
        fileScanner = FileScanner(location)

        with open(location) as fp:
                scanner = FileScanner(fp)
                for block in scanner:
                    if isinstance(block, SectionHeader):
                        self.pprint_sectionheader(block)
                    elif isinstance(block, InterfaceDescription):
                        self.pprint_interfacedesc(block)
                    elif isinstance(block, EnhancedPacket):
                        self.pprint_enhanced_packet(block)
                    else:
                        print('    ' + str(block))

    def pprint_options(self, options):
        if len(options):
            yield '--'
            for key, values in options.iter_all_items():
                for value in values:
                    yield self.col256(key + ':', bold=True, fg='453')
                    yield self.col256(unicode(value), fg='340')


    def pprint_sectionheader(self, block):
        endianness_desc = {
            '<': 'Little endian',
            '>': 'Big endian',
            '!': 'Network (Big endian)',
            '=': 'Native',
        }

        text = [
            self.col256(' Section ', bg='400', fg='550'),
            self.col256('version:', bold=True),
            self.col256('.'.join(str(x) for x in block.version), fg='145'),

            # col256('endianness:', bold=True),
            '-',
            self.col256(endianness_desc.get(block.endianness, 'Unknown endianness'),
                   bold=True),
            '-',
        ]

        if block.length < 0:
            text.append(self.col256('unspecified size', bold=True))
        else:
            text.append(self.col256('length:', bold=True))
            text.append(self.col256(str(block.length), fg='145'))

        text.extend(self.pprint_options(block.options))
        print(' '.join(text))


    def pprint_interfacedesc(self, block):
        text = [
            self.col256(' Interface #{0} '.format(block.interface_id),
                   bg='010', fg='453'),
            self.col256('Link type:', bold=True),
            self.col256(unicode(block.link_type), fg='140'),
            self.col256(block.link_type_description, fg='145'),
            self.col256('Snap length:', bold=True),
            self.col256(unicode(block.snaplen), fg='145'),
        ]
        text.extend(self.pprint_options(block.options))
        print(' '.join(text))


    def pprint_enhanced_packet(self, block):
        text = [
            self.col256(' Packet+ ', bg='001', fg='345'),

            # col256('NIC:', bold=True),
            # col256(unicode(block.interface_id), fg='145'),
            self.col256(unicode(block.interface.options['if_name']), fg='140'),

            self.col256(unicode(datetime.utcfromtimestamp(block.timestamp)
                           .strftime('%Y-%m-%d %H:%M:%S')), fg='455'),
        ]

        text.extend([
            # col256('Size:', bold=True),
            self.col256(unicode(block.packet_len) + u' bytes', fg='025')])

        if block.captured_len != block.packet_len:
            text.extend([
                self.col256('Truncated to:', bold=True),
                self.col256(unicode(block.captured_len) + u'bytes', fg='145')])

        text.extend(self.pprint_options(block.options))
        print(' '.join(text))

        if block.interface.link_type == 1:
            # print(repr(block.packet_data))
            # print(col256(repr(Ether(block.packet_data)), fg='255'))

            _info = self.format_packet_information(block.packet_data)
            print('\n'.join('    ' + line for line in _info))

        else:
            print('        Printing information for non-ethernet packets')
            print('        is not supported yet.')

        # print('\n'.join('        ' + line
        #                 for line in format_binary_data(block.packet_data)))


    def format_packet_information(self, packet_data):
        decoded = Ether(packet_data)
        return self.format_scapy_packet(decoded)


    def format_scapy_packet(self, packet):
        fields = []
        for f in packet.fields_desc:
            # if isinstance(f, ConditionalField) and not f._evalcond(self):
            #     continue
            if f.name in packet.fields:
                val = f.i2repr(packet, packet.fields[f.name])

            elif f.name in packet.overloaded_fields:
                val = f.i2repr(packet, packet.overloaded_fields[f.name])

            else:
                continue

            fields.append('{0}={1}'.format(self.col256(f.name, '542'),
                                           self.col256(val, '352')))

        yield '{0} {1}'.format(
            self.col256(packet.__class__.__name__, '501'),
            ' '.join(fields))

        if packet.payload:
            if isinstance(packet.payload, scapy.packet.Raw):
                raw_data = str(packet.payload)
                for line in self.make_printable(raw_data).splitlines():
                    yield '    ' + line

                #     for line in format_binary_data(raw_data):
                #         yield '    ' + line

            elif isinstance(packet.payload, scapy.packet.Packet):
                for line in self.format_scapy_packet(packet.payload):
                    yield '    ' + line

            else:
                for line in repr(packet.payload).splitlines():
                    yield '    ' + line


    def make_printable(self, data):  # todo: preserve unicode
        stream = io.BytesIO(data)
        for ch in data:
            if ch == '\\':
                stream.write('\\\\')
            elif ch in '\n\r' or (32 <= ord(ch) <= 126):
                stream.write(ch)
            else:
                stream.write('\\x{0:02x}'.format(ord(ch)))
        return stream.getvalue()


    def format_binary_data(self, data):
        stream = io.BytesIO(data)
        row_offset = 0
        row_size = 16  # bytes

        while True:
            data = stream.read(row_size)
            if not data:
                return

            hexrow = io.BytesIO()
            asciirow = io.BytesIO()
            for i, byte in enumerate(data):
                if 32 <= ord(byte) <= 126:
                    asciirow.write(byte)
                else:
                    asciirow.write('.')
                hexrow.write(format(ord(byte), '02x'))
                if i < 15:
                    if i % 2 == 1:
                        hexrow.write(' ')
                    if i % 8 == 7:
                        hexrow.write(' ')

                row_offset += 1

            yield '{0:08x}:   {1:40s}   {2:16s}'.format(
                row_offset,
                hexrow.getvalue(),
                asciirow.getvalue())
    def col256(self, text, fg=None, bg=None, bold=False):
        def _get_color(col):
            return u'8;5;{0:d}'.format(_to_color(col))

        def _to_color(num):
            if isinstance(num, (int, long)):
                return num  # Assume it is already a color

            if isinstance(num, basestring) and len(num) <= 3:
                return 16 + int(num, 6)

            raise ValueError("Invalid color: {0!r}".format(num))

        if not isinstance(text, basestring):
            text = repr(text)

        if not isinstance(text, unicode):
            text = unicode(text, encoding='utf-8')

        buf = io.StringIO()

        if bold:
            buf.write(u'\x1b[1m')

        if fg is not None:
            buf.write(u'\x1b[3{0}m'.format(_get_color(fg)))

        if bg is not None:
            buf.write(u'\x1b[4{0}m'.format(_get_color(bg)))

        buf.write(text)
        buf.write(u'\x1b[0m')
        return buf.getvalue()



PostProcessing()
