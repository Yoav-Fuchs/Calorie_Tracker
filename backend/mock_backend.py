from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time

class MockCalorieTrackerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-type")
        self.end_headers()

    def do_POST(self):
        if self.path == '/analyze-food':
            # Simulate processing delay
            time.sleep(1)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "items": [
                    {
                        "name": "Grilled Salmon (Mock Backend Fallback)",
                        "confidence": 0.95,
                        "estimated_volume_cm3": 150.0,
                        "estimated_weight_g": 150.0,
                        "nutrition": {
                            "calories": 312.0,
                            "protein_g": 34.0,
                            "carbs_g": 0.0,
                            "fat_g": 19.0
                        }
                    }
                ],
                "processing_time_ms": 1050.5
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=MockCalorieTrackerHandler, port=8000):
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting fallback mock server on http://127.0.0.1:{port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
