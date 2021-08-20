#!/usr/bin/env python
# coding=utf-8
'''
Author: HeathKang
Date: 2017-12-22 16:38:59
LastEditors: Zhang Hengye
LastEditTime: 2021-08-20 14:19:22
'''
import socket
import logging
import time
from simplecannet.event import Event
from simplecannet.message import Message
from simplecannet.exception import NeedMoreDataError


logger = logging.getLogger(__name__)


class Connection:

    HEART_BEAT = bytes([0xaa, 0x00, 0xff, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x55])

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.init()

    def init(self):
        """init tcp socket
            :return:
        """
        self.socket = socket.create_connection((self.ip, self.port))
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.settimeout(10)

    def _recv(self, length=13):
        """recv tcp data from server
            :param length: data length
            :return:
        """
        try:
            data = self.socket.recv(length)
            return data
        except (InterruptedError, socket.timeout) as e:
            # raise e("Tcp connection interrupted, please check connection and reconnect")
            self.reconnect()

    def _convert(self, data):
        """convert tcp data to can bus event
            :param data:
            :return: can bus event
        """
        if data == self.HEART_BEAT:
            return None
        else:
            event = Event.from_buffer(data)  # init a Event
        return event.msg

    def recv(self, timeout=None):
        """recv can bus data
            :param timeout:
            :return:
        """
        try:
            data = self._recv()
            data_handle = self._convert(data)
        except NeedMoreDataError:
            # 2021-08-20 zhy:
            # try to recv data and splice it at once when NeedMoreDataError.
            data += self._recv()
            data_handle = self._convert(data)

        return data_handle

    def destroy(self):
        """destroy tcp socket
            :return:
        """
        self.socket.close()
        logger.debug("Destroyed tcp socket")

    def reconnect(self):
        """reconnect to tcp server
            :return:
        """
        self.destroy()
        self.init()
