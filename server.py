import http.server
import socketserver
import json
import socket
import os
import urllib.parse
from datetime import datetime

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Global In-Memory Game State
game_state = {
    'status': 'LOBBY',  # 'LOBBY', 'PLAYING', 'ENDED'
    'roundId': 1,
    'players': [],      # list of { studentId, emoji, name, joinedAt, tableNum, clientId }
    'scores': []        # list of { studentId, emoji, name, score, accuracy, qualityTag, qualityIcon, orderDish, orderPrice, orderStatus, timestamp }
}

class OCRQuestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/play':
            self.send_response(302)
            self.send_header('Location', '/?role=student')
            self.end_headers()
            return
        elif parsed.path in ('/api/info', '/api/game_state'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            return
        super().do_HEAD()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/play':
            self.send_response(302)
            self.send_header('Location', '/?role=student')
            self.end_headers()
            return
        elif parsed.path == '/api/info':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            data = {
                'ip': get_local_ip(),
                'port': PORT,
                'joinUrl': f"http://{get_local_ip()}:{PORT}/play"
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            return
        elif parsed.path == '/api/game_state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            # Sort orders by table number for easy kitchen serving
            orders = sorted(game_state['scores'], key=lambda x: x.get('tableNum', 99))
            res = {
                'status': game_state['status'],
                'roundId': game_state.get('roundId', 1),
                'players': game_state['players'],
                'scores': orders,
                'orders': orders
            }
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        payload = {}
        if post_data:
            try:
                payload = json.loads(post_data.decode('utf-8'))
            except Exception:
                pass

        if parsed.path == '/api/join':
            student_id = str(payload.get('studentId', '')).strip()
            name = str(payload.get('name', '')).strip()
            emoji = payload.get('emoji', '🐱')
            client_id = payload.get('clientId') or student_id or str(datetime.now().timestamp())

            if not name or not student_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'กรุณาป้อนชื่อเล่นและรหัสตัวเลขให้ครบถ้วนก่อนเข้าโต๊ะ'}, ensure_ascii=False).encode('utf-8'))
                return

            # Find existing table if rejoining
            existing_table = None
            for pl in game_state['players']:
                if pl.get('clientId') == client_id or pl.get('studentId') == student_id:
                    existing_table = pl.get('tableNum')
                    break

            # Remove any player with same clientId or studentId so re-joining updates cleanly
            game_state['players'] = [x for x in game_state['players'] if x.get('clientId') != client_id and x.get('studentId') != student_id]

            if len(game_state['players']) < 10:
                occupied_tables = {x.get('tableNum') for x in game_state['players'] if x.get('tableNum')}
                if existing_table and existing_table not in occupied_tables:
                    table_num = existing_table
                else:
                    table_num = 1
                    for t in range(1, 11):
                        if t not in occupied_tables:
                            table_num = t
                            break

                p = {
                    'clientId': client_id,
                    'studentId': student_id,
                    'emoji': emoji,
                    'name': name,
                    'tableNum': table_num,
                    'joinedAt': datetime.now().strftime('%H:%M:%S')
                }
                game_state['players'].append(p)
                status = 'joined'
            else:
                p = {'clientId': client_id, 'studentId': student_id, 'name': name, 'emoji': emoji, 'tableNum': None}
                status = 'room_full'

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': status, 'player': p, 'count': len(game_state['players'])}, ensure_ascii=False).encode('utf-8'))
            return

        elif parsed.path == '/api/start_game':
            game_state['status'] = 'PLAYING'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'started'}).encode('utf-8'))
            return

        elif parsed.path == '/api/reset_game':
            game_state['status'] = 'LOBBY'
            game_state['roundId'] = game_state.get('roundId', 1) + 1
            game_state['scores'].clear()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'reset_ok', 'roundId': game_state['roundId']}).encode('utf-8'))
            return

        elif parsed.path == '/api/clear_all_players':
            game_state['status'] = 'LOBBY'
            game_state['roundId'] = game_state.get('roundId', 1) + 1
            game_state['players'].clear()
            game_state['scores'].clear()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'cleared_all'}).encode('utf-8'))
            return

        elif parsed.path == '/api/leave':
            client_id = payload.get('clientId')
            student_id = payload.get('studentId')
            game_state['players'] = [x for x in game_state['players'] if x.get('clientId') != client_id and x.get('studentId') != student_id]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'left'}).encode('utf-8'))
            return

        elif parsed.path == '/api/scores':
            payload['timestamp'] = datetime.now().strftime('%H:%M:%S')
            payload['orderStatus'] = 'PENDING'  # PENDING -> SERVED
            if not payload.get('tableNum'):
                for pl in game_state['players']:
                    if pl.get('studentId') == payload.get('studentId') or pl.get('clientId') == payload.get('clientId'):
                        payload['tableNum'] = pl.get('tableNum')
                        break
            game_state['scores'] = [x for x in game_state['scores'] if x.get('studentId') != payload.get('studentId')]
            game_state['scores'].append(payload)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}, ensure_ascii=False).encode('utf-8'))
            return

        elif parsed.path == '/api/serve_order':
            # Teacher marks order as SERVED
            target_id = payload.get('studentId')
            for s in game_state['scores']:
                if s.get('studentId') == target_id:
                    s['orderStatus'] = 'SERVED'
                    break

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'served_ok'}).encode('utf-8'))
            return

        super().do_POST()

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"==================================================")
    print(f" 8-BIT OCR PIXEL BISTRO SERVER STARTED!")
    print(f" Teacher (Waiter) View : http://localhost:{PORT}")
    print(f" Student (Tourist) Join: http://{local_ip}:{PORT}/play")
    print(f"==================================================")
    
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(("", PORT), OCRQuestHandler) as httpd:
        httpd.serve_forever()
