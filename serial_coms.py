#! /usr/bin/env python
# encoding: utf-8
"""
Example of a AT command protocol.

https://en.wikipedia.org/wiki/Hayes_command_set
http://www.itu.int/rec/T-REC-V.250-200307-I/en
"""
from __future__ import print_function

import sys
sys.path.insert(0, '..')

import logging
import serial
import serial.threaded
import threading

try:
    import queue
except ImportError:
    import Queue as queue


class ATException(Exception):
    pass


class ATProtocol(serial.threaded.LineReader):

    TERMINATOR = b'\r\n'

    def __init__(self):
        super(ATProtocol, self).__init__()
        self.alive = True
        self.responses = queue.Queue()
        self.events = queue.Queue()
        self._event_thread = threading.Thread(target=self._run_event)
        self._event_thread.daemon = True
        self._event_thread.name = 'at-event'
        self._event_thread.start()
        self.lock = threading.Lock()

    def stop(self):
        """
        Stop the event processing thread, abort pending commands, if any.
        """
        self.alive = False
        self.events.put(None)
        self.responses.put('<exit>')

    def _run_event(self):
        """
        Process events in a separate thread so that input thread is not
        blocked.
        """
        while self.alive:
            try:
                self.handle_event(self.events.get())
            except:
                logging.exception('_run_event')

    def handle_line(self, line):
        """
        Handle input from serial port, check for events.
        """
        if line.startswith('+'):
            self.events.put(line)
        else:
            self.responses.put(line)

    def handle_event(self, event):
        """
        Spontaneous message received.
        """
        print('event received:', event)

    def command(self, command, response='OK', timeout=5):
        """
        Set an AT command and wait for the response.
        """
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(command)
            lines = []
            while True:
                try:
                    line = self.responses.get(timeout=timeout)
                    #~ print("%s -> %r" % (command, line))
                    if line == response:
                        return lines
                    else:
                        lines.append(line)
                except queue.Empty:
                    raise ATException('AT command timeout ({!r})'.format(command))


class PAN1322(ATProtocol):
        """
        Example communication with PAN1322 BT module.

        Some commands do not respond with OK but with a '+...' line. This is
        implemented via command_with_event_response and handle_event, because
        '+...' lines are also used for real events.
        """

        def __init__(self):
            super(PAN1322, self).__init__()
            self.event_responses = queue.Queue()
            self._awaiting_response_for = None

        def connection_made(self, transport):
            super(PAN1322, self).connection_made(transport)
            # our adapter enables the module with RTS=low
            self.transport.serial.rts = False
            time.sleep(0.3)
            self.transport.serial.reset_input_buffer()

        def handle_event(self, event):
            """Handle events and command responses starting with '+...'"""
            if event.startswith('+RRBDRES') and self._awaiting_response_for.startswith('AT+JRBD'):
                rev = event[9:9 + 12]
                mac = ':'.join('{:02X}'.format(ord(x)) for x in rev.decode('hex')[::-1])
                self.event_responses.put(mac)
            else:
                logging.warning('unhandled event: {!r}'.format(event))

        def command_with_event_response(self, command):
            """Send a command that responds with '+...' line"""
            with self.lock:  # ensure that just one thread is sending commands at once
                self._awaiting_response_for = command
                self.transport.write(b'{}\r\n'.format(command.encode(self.ENCODING, self.UNICODE_HANDLING)))
                response = self.event_responses.get()
                self._awaiting_response_for = None
                return response

        # - - - example commands

        def reset(self):
            self.command("AT+JRES", response='ROK')      # SW-Reset BT module
        def okat(self):
            self.command("AT", response='OK')  # SW-Reset BT module
        def test(self):
            cmd = "AT+CFUN=4"
            self.command(cmd, response='OK')  # SW-Reset BT module
            cmd1 =  "AT%CMNG=0,12345,0,\""\
                    "-----BEGIN CERTIFICATE-----\r\n"\
                    "MIIDVDCCAjygAwIBAgIUKj+tQ2ZVKN7zp0hAyvoDb25i8i8wDQYJKoZIhvcNAQEL\r\n"\
                    "BQAwGTEXMBUGA1UEAwwONTQuMTcwLjE4MS4xODgwHhcNMjIxMDA3MTQwMDE4WhcN\r\n"\
                    "MzIxMDA0MTQwMDE4WjAZMRcwFQYDVQQDDA41NC4xNzAuMTgxLjE4ODCCASIwDQYJ\r\n"\
                    "KoZIhvcNAQEBBQADggEPADCCAQoCggEBAMSUHbYhBY2CTEh+afpvzF83poLpim3j\r\n"\
                    "zCHffxVboQVRXmTAcrTlHgr3ewq0tMW6Lry+9WFX6Ki5+R1dWYwcTKLe1evMLdSn\r\n"\
                    "LZA3v//H3Dj2BBmR3i/LLC2XQiqesfEpQLfyn8DOMrl87nllkOfx4mOscLWOCz8h\r\n"\
                    "yFE3x/HKoqcZV0qYmse1aUZWp+25onTvNckiUoTwFASw1Lh0CZfEKhgUxshRKp2F\r\n"\
                    "BNlnTX3mZLDSUibpY8uje5KvTWQfysqG1wOWRr26SfHPJRqQxGzUBgYoi820ylcq\r\n"\
                    "Wz1h9D4MoTbxgcFA9aSS/L7hj9MfP2o503WSXrXsQtUNUYd9dagyIEMCAwEAAaOB\r\n"\
                    "kzCBkDAdBgNVHQ4EFgQUEivavF3vjzki7qFc10OHCq8b9fwwVAYDVR0jBE0wS4AU\r\n"\
                    "EivavF3vjzki7qFc10OHCq8b9fyhHaQbMBkxFzAVBgNVBAMMDjU0LjE3MC4xODEu\r\n"\
                    "MTg4ghQqP61DZlUo3vOnSEDK+gNvbmLyLzAMBgNVHRMEBTADAQH/MAsGA1UdDwQE\r\n"\
                    "AwIBBjANBgkqhkiG9w0BAQsFAAOCAQEARUYzwXm/UIRN1d/aF/z1a6k0f4OobkFI\r\n"\
                    "Q1qA8gehI0e9QObuI/tZqCrwlvq2xPJosrpyfvWFOy0q2xUcieLqocM+qHKjVgHU\r\n"\
                    "k0sDwzuimhblA7hsT+tC+UsmJaU21XtyaDDbemAzulHK4ZLvtx9LMV5yKSVAM2iD\r\n"\
                    "cN736V1zaOZSZlPC3MQRt/S6LosAd+7wZ5H0jqzjDeVcJ9BMYpwgvfLpPh5gNbk5\r\n"\
                    "4SAnnT2O3VlCY8L6k/HzIOwS/m7byL0kFqVwZPmXw7lP//6YaGnv0m1BvrjBxZbG\r\n"\
                    "/pPuNwt1e66R53O5hzwcl3cY+bLCFkAXWJORLDnnB16C7I/ufS+3IQ==\r\n"\
                    "-----END CERTIFICATE-----\"\r\n"
            self.command(cmd1, response='OK')  # SW-Reset BT module
            cmd2 = "AT%CMNG=0,12345,1,\"" \
                    "-----BEGIN CERTIFICATE-----\r\n" \
                    "MIIDYzCCAkugAwIBAgIQDspTd3jl5QpGqGLrs/6r+jANBgkqhkiG9w0BAQsFADAZ\r\n" \
                    "MRcwFQYDVQQDDA41NC4xNzAuMTgxLjE4ODAeFw0yMjEwMDcyMDA5NDVaFw0yNTA5\r\n" \
                    "MjEyMDA5NDVaMBoxGDAWBgNVBAMMD2VkZ2VsaW90X2NsaWVudDCCASIwDQYJKoZI\r\n" \
                    "hvcNAQEBBQADggEPADCCAQoCggEBANXCuYmj1gA6ozMqhBedIz4urFp8/Qts8oBR\r\n" \
                    "kjDE7crRqD52CfNQZ1VhRY5CWRtwrSaB0uUpwVDTP0Qto4vNwHbxqjfoV2zSI5TZ\r\n" \
                    "i2KdF7SgyjodyWpMHUcWRPNYJ+oyVXKC78Do+7PkDkPWDUByHKN61lWSRGnSZMBR\r\n" \
                    "Oes9pbdQ48TydXMgOOihKKnEC9b9RjeT4yWPbktLFOKp4QSX3jNAVqV8TdPOsTcM\r\n" \
                    "UFDxa7ehxHaS6OZxWpjQvdvr3OLm7QP7nBmgN2EJj2VJ3Uj8y2mp2RRMq/CnI7yy\r\n" \
                    "IIFyK5sRf6x8zkBEa0HmYCboxa6N3Q+/ClwDYu4LyC+RXXgO590CAwEAAaOBpTCB\r\n" \
                    "ojAJBgNVHRMEAjAAMB0GA1UdDgQWBBSPcquE7aSspQVTobIlOUtsvcgpDTBUBgNV\r\n" \
                    "HSMETTBLgBQSK9q8Xe+POSLuoVzXQ4cKrxv1/KEdpBswGTEXMBUGA1UEAwwONTQu\r\n" \
                    "MTcwLjE4MS4xODiCFCo/rUNmVSje86dIQMr6A29uYvIvMBMGA1UdJQQMMAoGCCsG\r\n" \
                    "AQUFBwMCMAsGA1UdDwQEAwIHgDANBgkqhkiG9w0BAQsFAAOCAQEAV4cZHN2Ll9Ez\r\n" \
                    "SgNa5hCmJjP21jLAqCrTQnPHC32BbWuuLxYDh3HXwOa1l5hfldnbUZuoDQkc6Aky\r\n" \
                    "LeRSzQ4kOOkOJ6Rhk6FyTp/O1dfveSIXscVpPh/+Z9bm5NwlrX8c05vzVQdre5fh\r\n" \
                    "+cAf3YrPbhF9+w68VFSWwz0bu0qtTubVHlhSDJNd+c4W3aWcfYdmpGRsOIZESHlE\r\n" \
                    "EVheE+yIsIBj32pBGKUOREmaGJ/hgCgwWPl/uQ6FGabWycyDxYWhWhXmbv884ETO\r\n" \
                    "NLr3IgJlwCBN8M2xgUchmNRzmro9dt6W4Dz3nVwK0jqilIrCWODPY0lajLRSkmRX\r\n" \
                    "iosQRuQoYQ==\r\n" \
                    "-----END CERTIFICATE-----\"\r\n"
            self.command(cmd2, response='OK')  # SW-Reset BT module
            cmd3 =  "AT%CMNG=0,12345,2,\""\
                    "-----BEGIN PRIVATE KEY-----\r\n"\
                    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDVwrmJo9YAOqMz\r\n"\
                    "KoQXnSM+LqxafP0LbPKAUZIwxO3K0ag+dgnzUGdVYUWOQlkbcK0mgdLlKcFQ0z9E\r\n"\
                    "LaOLzcB28ao36Fds0iOU2YtinRe0oMo6HclqTB1HFkTzWCfqMlVygu/A6Puz5A5D\r\n"\
                    "1g1AchyjetZVkkRp0mTAUTnrPaW3UOPE8nVzIDjooSipxAvW/UY3k+Mlj25LSxTi\r\n"\
                    "qeEEl94zQFalfE3TzrE3DFBQ8Wu3ocR2kujmcVqY0L3b69zi5u0D+5wZoDdhCY9l\r\n"\
                    "Sd1I/MtpqdkUTKvwpyO8siCBciubEX+sfM5ARGtB5mAm6MWujd0PvwpcA2LuC8gv\r\n"\
                    "kV14DufdAgMBAAECggEBAJVVK/kUE/SlAk5EbXNxu6U9RfsRRlYtDlzGn7KiYN1I\r\n"\
                    "CplYLStmCEqFYeo4P7gDx3MXTxX5TawBaDlhCNgqLULrIVddYXYMd/8M22tRA7aU\r\n"\
                    "fbKMDKHN+sYmsJSwCXJ7J2aQQp4qJW1O7QhHCYr0LT2oGwQ84r5q1SfllujYcGTX\r\n"\
                    "PtZR/Azb3cMvxM0a1yAJiE4R6M/Uu9Xw+rcxyXXYB8AGgkt21KhftYhBPjt3gBoR\r\n"\
                    "qWAw8o90fd8naDeLPP7TptAU5gyr4wB0WFv75rnRqWJ/VkDg+qQcT9CTxbGd2VYN\r\n"\
                    "5PNU4YlE5qX6+khyX4b1j5i6C0CZxJQuLVGUAi2BiwECgYEA75zuwbla7TkgZ0FB\r\n"\
                    "boVTqD0Ajbj84zV/VFf/gSkB7RqUwPkdkgxavGpZwpt9b52wT35II4YtNAjrCcOl\r\n"\
                    "HLU+77umWQ/6xzTdozHWPhDZT0dxURNeFrOS2YkkOxEKRR4pTsMt4fbdqseOT4Si\r\n"\
                    "o8nI90duqT4D5OxKN2XlAJvYv1UCgYEA5GEtVYbpPs7frSmHpUPhqgON4fYuXkst\r\n"\
                    "wXrlDxMAA6jlL6x/efus3eWqJwXku9AgOiMh03bcbr0i5myIH4jzPc9EodDIBIYK\r\n"\
                    "l8pO4cr9qysS3OdCnUMI0QpWFKVNwq5AHfAvzqPQI/H+ECrb2Y4M7IB3Ly6FTP4H\r\n"\
                    "KOwFFu+atmkCgYAsIxQ3yxTcrbEyU+rhmN2YF+SKNpEeqTQTLUJ7YDpimorcIQc5\r\n"\
                    "Z90u58gw+MNaVAmuGuze3lBlTV8+JTO83gYB0ucJcNAY8bwB26RDOodM+zP8Yzzp\r\n"\
                    "oZpjR8fMuY7SvIOPZpSFExwx4SBttVjgIsNKCXZw5mOBP6VMHxDX091RIQKBgDcT\r\n"\
                    "jHhM0eFYyK6dDl530WtL8iKlWSdaYA2CEs2g2mcHi0YFBrUnUdgts+w3SqNUnQEI\r\n"\
                    "SfcSejSmnk0NrYJVZ7vnSXjwvdwBa3qRypY/ew+VkrX9e54rdWvcX0gZWXhyx3mw\r\n"\
                    "3AaskNyqVogVnfGIhWtfy95wDKu1s4pV6SBP5nLJAoGBAJD3OXCVbCqHJQaoRRVm\r\n"\
                    "9+mVHqHYXLjpE9toGsYGa4TK1fd2nCWhkzF96/psjNQX/UbO1QvrPJBqFvKjsf2o\r\n"\
                    "+l1KKKLBcT/LSTy3yW3ozQcqe2lrAw4lAomD34rjcVXo9Ba6u4iuOHJKmuJuBqt6\r\n"\
                    "VPECIU8Qeik/tN3K5hSnJii6\r\n"\
                    "-----END PRIVATE KEY-----\"\r\n"
            self.command(cmd3, response='OK')  # SW-Reset BT module
            cmd4 = "AT+CFUN=1"
            self.command(cmd4, response='OK')  # SW-Reset BT module
        def get_mac_address(self):
            # requests hardware / calibration info as event
            return self.command_with_event_response("AT+JRBD")

        def open_serial_port(self):
            self.serial.serial_for_url('COM8', baudrate=115200, timeout=1)
        #~ ser = serial.Serial('COM1', baudrate=115200, timeout=1)
    #with serial.threaded.ReaderThread(ser, PAN1322) as bt_module:
       # bt_module.reset()
     #   bt_module.test()
       # print("reset OK")
       # print("MAC address is", bt_module.get_mac_address())