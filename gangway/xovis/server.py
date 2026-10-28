#!/usr/bin/env python3
"""
Web Server to receive XOVIS-Events and forward them to listening threads
"""

import collections
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock, Thread
from typing import Callable, Dict, List, Optional, Tuple

from ..types import TrackedPoint
from .homographic_projection import apply_transform
from .model import DeleteTrack, Event, EventObject, create_events_from_json


def create_xovis_request_handler(server: "XOVISServer"):
    class RequestHandler(BaseHTTPRequestHandler):
        def _read_body(self) -> bytes:
            # The sensor can send a chunked body with no Content-Length.
            if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
                chunks = []
                while True:
                    size = int(self.rfile.readline().split(b";")[0].strip(), 16)
                    if size == 0:
                        # Skip the trailer section up to the empty line.
                        while self.rfile.readline() not in (b"\r\n", b"\n", b""):
                            pass
                        return b"".join(chunks)
                    chunks.append(self.rfile.read(size))
                    self.rfile.readline()
            return self.rfile.read(int(self.headers.get("Content-Length", 0)))

        def do_POST(self):
            post_data = self._read_body()

            try:
                data = json.loads(post_data)
                server._notify(data)
                self.send_response(200)
                self.end_headers()
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()

        def log_message(self, format, *args):
            # Suppress logging
            return

    return RequestHandler


class XOVISServer:
    _subscribers: List[Tuple[Callable[[Event], None], Optional[List[Event]]]]
    _subscribers_position: List[Callable[[List[TrackedPoint]], None]]
    _host: str
    _port: int

    _objects: Dict[int, EventObject]
    _timestamps: Dict[int, int]
    _update_times: collections.deque

    def __init__(self, host: str = "0.0.0.0", port: int = 8081) -> None:
        self._host = host
        self._port = port
        self._subscribers = list()
        self._subscribers_position = list()
        self._objects = dict()
        self._timestamps = dict()
        self._update_times = collections.deque(maxlen=100)
        self._lock = Lock()

    def subscribe(
        self, callback: Callable[[Event], None], filter: Optional[List[Event]]
    ) -> None:
        self._subscribers.append((callback, filter))

    def subscribe_position(
        self, callback: Callable[[List[TrackedPoint]], None]
    ) -> None:
        self._subscribers_position.append(callback)

    @property
    def ups(self) -> int:
        now = time.time()
        with self._lock:
            while len(self._update_times) > 0 and self._update_times[0] < now - 1.0:
                self._update_times.popleft()
            return len(self._update_times)

    def _notify(self, data) -> None:
        now = time.time()
        with self._lock:
            self._update_times.append(now)
            while len(self._update_times) > 0 and self._update_times[0] < now - 1.0:
                self._update_times.popleft()

        events = create_events_from_json(data)

        self._notify_event(events)
        self._notify_position(events)

    def _notify_event(self, events) -> None:
        for event in events:
            for callback, event_filter in self._subscribers:
                if event_filter is None or type(event) in event_filter:
                    callback(event)

    def _notify_position(self, events) -> None:
        for event in events:
            if isinstance(event, DeleteTrack) and event.object.id in self._objects:
                self._objects.pop(event.object.id)
            elif (
                event.object.id not in self._objects
                or event.timestamp > self._timestamps[event.object.id]
            ):
                self._objects[event.object.id] = event.object
                self._timestamps[event.object.id] = event.timestamp

        if len(self._objects) == 0:
            for callback in self._subscribers_position:
                callback([])
            return

        objects_values = list(self._objects.values())
        points = [(obj.x, obj.y) for obj in objects_values]
        mapped_points = [
            TrackedPoint(
                r[0], r[1], id=obj.id, timestamp=self._timestamps[obj.id] / 1000.0
            )
            for r, obj in zip(apply_transform(points), objects_values)
        ]

        for callback in self._subscribers_position:
            callback(mapped_points)

    def start_server(self) -> HTTPServer:
        handler = create_xovis_request_handler(self)
        http_server = HTTPServer((self._host, self._port), handler)
        thread = Thread(target=http_server.serve_forever)
        thread.daemon = True
        thread.start()
        print(f"XOVIS callback server receiver running on {self._host}:{self._port}")
        return http_server
