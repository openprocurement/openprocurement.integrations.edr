# -*- coding: utf-8 -*-
from gevent import sleep


def custom_sleep(seconds):
    return sleep(seconds=0)
