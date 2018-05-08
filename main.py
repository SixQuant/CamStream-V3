import signal
import sys
import time
import getopt
from http.server import BaseHTTPRequestHandler, HTTPServer
import cv2
import socket
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from datetime import datetime

existing = False
file = None
cap = None
server_host = '0.0.0.0'
server_port = 5000

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		parsed_path = urlparse(self.path)
		path = parsed_path.path
		
		if path == '/':
			return self.doOutputHome()

		# visit /best to auto optimize 
		if path == '/streaming/best':
			self.send_response(301)
			self.send_header('Location', '/streaming?q=20&gray=true&resize=-2')
			self.end_headers()
			return

		query_components = parse_qs(parsed_path.query) 

		image_quality = None
		if 'q' in query_components:
			image_quality = int(query_components['q'][0]) 

		resize_percent = None
		if 'resize' in query_components:
			resize_percent = int(query_components['resize'][0])

		make_it_blue = 'blue' in query_components
		make_it_gray = 'gray' in query_components
		flip_it = 'flip' in query_components

		self.doOutputStreaming(image_quality, resize_percent, make_it_blue, make_it_gray, flip_it)
		
	def doOutputHome(self):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		self.wfile.write(b'''
			<html>
			  <head>
			    <title>Video Streaming Demonstration</title>
			  </head>
			  <body>
			    <h1>Video Streaming Demonstration</h1>
			    <img src="streaming">
			  </body>
			</html>
			''')

	def doOutputStreaming(self, image_quality, resize_percent, make_it_blue, make_it_gray, flip_it):
		self.send_response(200)
		self.send_header('Cache-Control', 'no-store, no-cache, private, max-age=0')
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--frame')
		self.send_header('Pragma', 'no-cache')
		self.end_headers()

		global cap
		
		if file:		
			cap = cv2.VideoCapture(file)

		time_start = 0
		while True:
			try:
				return_value, image = cap.read()

				if not return_value:
					if file and cap:
						cap.release()
						return
					continue 

				if make_it_blue:
					image[:,:,1] = 0
					image[:,:,2] = 0

				if make_it_gray:
					image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

				if flip_it:
					image = cv2.flip(image, 1)

				# after set image color 
				ts =  datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
				cv2.putText(image, ts, (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

				if resize_percent:
					height, width = image.shape[:2]
					if resize_percent > 0: 
						#make image bigger
						image = cv2.resize(image, (width*resize_percent, height*resize_percent)) 
					elif resize_percent < 0:
						#make image smaller
						resize_percent = abs(resize_percent)
						image = cv2.resize(image, (width/resize_percent, height/resize_percent)) 
					  
				if image_quality:
					_, buf = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, image_quality]) 
				else:
					_, buf = cv2.imencode('.jpg', image) 

				if file:
					end = time.time()
					if time_start != 0:
						secs = 0.1-(end - time_start)
						if secs > 0:
							time.sleep(secs)
					time_start = end

				self.wfile.write(b'--frame\r\n'
               					 b'Content-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n\r\n')

			except BrokenPipeError:
				return
		return

def usage():
	print('python3 main.py -f=[movice.mp4] [-ip=192.168.1.100] [-p=8888]')

try:
    options,args = getopt.getopt(sys.argv[1:],"hf:p:i:", ["help","file=","ip=","port="])
except getopt.GetoptError:
    sys.exit()
for name,value in options:
    if name in ("-h","--help"):
        usage()
    if name in ("-f","--file"):
        file = value[1:]
    if name in ("-i","--ip"):
        server_host = value[1:]
    if name in ("-p","--port"):
        server_port = value[1:]

def signal_handler(signal, frame):
	print('You pressed Ctrl+C!')
	existing = True
	if cap: cap.release()
	server.socket.close()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if file:
	print('Read video frames from file: ' + file)
else:
	print('Capture video frames from camera')
	cap = cv2.VideoCapture(0)
	if not cap.isOpened():
		print('Please connect camera')

server = ThreadedHTTPServer((server_host, server_port), CamHandler)
print('Motion JPEG Streaming Server start on port %s' % (server_port))
print('Press Ctrl+C to exit')

server.serve_forever()

	