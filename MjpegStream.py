from http.server import BaseHTTPRequestHandler, HTTPServer
import cv2
import socket
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from datetime import datetime

def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("google.com",80))
	PCip = s.getsockname()[0]
	s.close()
	return PCip

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		parsed_path = urlparse(self.path)
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

		#/best to auto optimize 
		if parsed_path.path == '/best':
			self.send_response(301)
			self.send_header('Location', '/?q=20&gray=true&resize=-2')
			self.end_headers()
			return
		
		self.send_response(200)
		self.send_header('Cache-Control', 'no-store, no-cache, private, max-age=0')
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--frame')
		self.send_header('Pragma', 'no-cache')
		self.end_headers()
		
		while True:
			try:
				return_value, image = camera.read()

				if not return_value:
					continue 

				if make_it_blue:
					image[:,:,1] = 0
					image[:,:,2] = 0

				if make_it_gray:
					image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

				if flip_it:
					image = cv2.flip(image, 1)

				#after set image color 
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

				self.wfile.write('--frame'.encode('utf-8'))
				self.send_header('Content-type', 'image/jpeg')
				self.send_header('Content-length', len(buf))
				self.end_headers()
				self.wfile.write(buf)
	
			except KeyboardInterrupt:
				pass
		return

camera = cv2.VideoCapture(0)
if not camera.isOpened():
	exit ('Please connect camera')

try:
	server_port = 80
	server = ThreadedHTTPServer(('0.0.0.0', server_port), CamHandler)
	print ('Server start on http://%s:%s/' % (get_local_ip(), server_port))
	server.serve_forever()
except KeyboardInterrupt:
	camera.release()
	server.socket.close()
