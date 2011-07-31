#!/usr/bin/python
import os
import sys
import time

sys.path.append("/home/user/test/bot")
sys.path.append("/home/alevtina/Data/!Business/Bot/rzd_bot/bot")
import bot

def application(environ, start_response):
    status = '200 OK'

    data = environ['wsgi.input'].readlines()
    bot.ip_addr = environ['REMOTE_ADDR']
    bot.output_dir = '/var/log/bot/test'
    response = bot.call(data[0])
    response_headers = [('Content-type', 'application/json; charset=utf-8'),
                        ('Cache-Control', 'no-cache, must-revalidate'),
                        ('Expires', 'Mon, 26 Jul 1997 05:00:00 GMT'),
                        ('Content-Length', str(len(response)))]

    start_response(status, response_headers)
    return response
