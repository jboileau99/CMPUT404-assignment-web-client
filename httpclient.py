#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, https://github.com/treedust, and jboileau
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

"""
Things to remember/do/check
- Check what the virtualhosting part means, I think the point is just to include the host header?
- Figure out if I'm allowed to use urllib the way I did, or if I have to get host header myself?
"""


import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

ALLOWED_CONTENT_TYPES = ['application/x-www-form-encoded']

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __str__(self):
        return f"Response (Code = {self.code}):\n{self.body}"

class HTTPClient(object):

    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    # Get all HTTP headers for a given method, host, and optional request_body
    def get_request_headers(self, method, host, request_body=''):

        # Default headers
        headers = self.get_header_str('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0') + \
            self.get_header_str('Accept', '*/*') + \
            self.get_header_str('Connection', 'close') + \
            self.get_header_str('Host', host)

        # Add content headers for post request
        if method.lower() == 'post':
            headers += self.get_header_str("Content-Length", len(request_body))
            if request_body is not None:
                headers += self.get_header_str('Content-type', 'application/x-www-form-urlencoded')
        
        return headers

    # Get a single HTTP header string for a key-value pair
    def get_header_str(self, key, value):
        return f"{key}: {value}\r\n"
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    # Parse status code, headers, and body from HTTP response
    def parse_response(self, response):

        parts = response.split('\r\n\r\n')

        # Extract status line and headers
        status_headers = parts[0].split('\r\n')
        status = status_headers[0].strip()
        code = int(status.split()[1])
        headers = status_headers[1:]

        # Extract body if it's there
        if len(parts) == 2:
            body = parts[1].strip()

        return code, headers, body or None

    def GET(self, url, args=None):

        # Use urllib to parse a standard URL
        parsed_url = urllib.parse.urlparse(url)

        # Set headers
        headers = self.get_request_headers('GET', parsed_url.hostname)

        # Make a connection
        self.connect(parsed_url.hostname, parsed_url.port or 80)  # TODO: Using 80 by default here, is this correct?

        # Make a GET request to the indicated path
        req_string = f"GET {parsed_url.path or '/'} HTTP/1.1\r\n{headers}\r\n"
        self.sendall(req_string)

        # Get and parse response
        response = self.recvall(self.socket)
        code, headers, body = self.parse_response(response)

        # Close socket
        self.close()

        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        
        # Use urllib to parse a standard URL
        parsed_url = urllib.parse.urlparse(url)

        # Set headers and post body
        request_body = urllib.parse.urlencode(args) if args else ''
        request_headers = self.get_request_headers('POST', parsed_url.hostname, request_body=request_body)

        # Make a connection
        self.connect(parsed_url.hostname, parsed_url.port or 80)  # TODO: Using 80 by default here, is this correct?

        # Make a POST request to the indicated path
        req_string = f"POST {parsed_url.path or '/'} HTTP/1.1\r\n{request_headers}\r\n{request_body}"
        self.sendall(req_string)

        # Get and parse response
        response = self.recvall(self.socket)
        response_code, response_headers, response_body = self.parse_response(response)

        # Close socket
        self.close()

        return HTTPResponse(response_code, response_body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
