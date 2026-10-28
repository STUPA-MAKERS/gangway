"""HTTP receiver for Xovis events that forwards them to subscribers."""

import collections
import json
import time
from collections.abc import Callable, Collection, Iterable
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Lock, Thread
from typing import override

from ..types import TrackedPoint
from .homographic_projection import apply_transform
from .model import DeleteTrack, Event, EventJson, EventObject, iter_events

type EventCallback = Callable[[Event], None]
"""Receive one event."""

type PositionCallback = Callable[[list[TrackedPoint]], None]
"""Receive the floor positions of all tracked persons."""


def create_xovis_request_handler(
    server: "XOVISServer",
) -> type[BaseHTTPRequestHandler]:
    """Make a request handler class that sends the events to a server.

    Args:
        server: The server that gets the events.

    Returns:
        The request handler class for `http.server.HTTPServer`.
    """

    class RequestHandler(BaseHTTPRequestHandler):
        def _read_body(self) -> bytes:
            # The sensor can send a chunked body with no Content-Length.
            if "chunked" in self.headers.get("Transfer-Encoding", "").lower():
                chunks: list[bytes] = []
                while True:
                    size = int(self.rfile.readline().split(b";")[0].strip(), 16)
                    if size == 0:
                        # Skip the trailer section up to the empty line.
                        while self.rfile.readline() not in {b"\r\n", b"\n", b""}:
                            pass
                        return b"".join(chunks)
                    chunks.append(self.rfile.read(size))
                    self.rfile.readline()
            return self.rfile.read(int(self.headers.get("Content-Length", 0)))

        def do_POST(self) -> None:
            post_data = self._read_body()

            try:
                # The sensor sends a JSON list of event items. The parser
                # trusts this structure and does not validate it.
                data: list[EventJson] = json.loads(post_data)
                server.notify(data)
                self.send_response(200)
                self.end_headers()
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()

        @override
        def log_message(self, format: str, *args: object) -> None:
            # The sensor posts continuously. An access log line for each
            # request would flood the log.
            return

    return RequestHandler


class XOVISServer:
    """Receive Xovis events and send them to the subscribers."""

    _subscribers: list[tuple[EventCallback, Collection[type[Event]] | None]]
    _subscribers_position: list[PositionCallback]
    _host: str
    _port: int

    _objects: dict[int, EventObject]
    _timestamps: dict[int, int]
    _update_times: collections.deque[float]

    def __init__(self, host: str = "0.0.0.0", port: int = 8081) -> None:
        """Make a server. Call `start_server` to receive events.

        Args:
            host: The address to listen on.
            port: The port to listen on.
        """
        self._host = host
        self._port = port
        self._subscribers = []
        self._subscribers_position = []
        self._objects = {}
        self._timestamps = {}
        self._update_times = collections.deque(maxlen=100)
        self._lock = Lock()

    def subscribe(
        self,
        callback: EventCallback,
        event_filter: Collection[type[Event]] | None,
    ) -> None:
        """Receive each event.

        Args:
            callback: The function that gets each event.
            event_filter: The event types to receive. None means all types.
        """
        self._subscribers.append((callback, event_filter))

    def subscribe_position(self, callback: PositionCallback) -> None:
        """Receive the floor positions of all tracked persons after each request.

        Args:
            callback: The function that gets the positions.
        """
        self._subscribers_position.append(callback)

    @property
    def ups(self) -> int:
        """The number of sensor requests in the last second."""
        now = time.time()
        with self._lock:
            while len(self._update_times) > 0 and self._update_times[0] < now - 1.0:
                self._update_times.popleft()
            return len(self._update_times)

    def notify(self, data: Iterable[EventJson]) -> None:
        """Process the event items of one sensor request.

        Args:
            data: The raw event items.
        """
        now = time.time()
        with self._lock:
            self._update_times.append(now)
            while len(self._update_times) > 0 and self._update_times[0] < now - 1.0:
                self._update_times.popleft()

        # Both notify steps iterate over the events, so materialize them once.
        events = list(iter_events(data))

        self._notify_event(events)
        self._notify_position(events)

    def _notify_event(self, events: Iterable[Event]) -> None:
        for event in events:
            for callback, event_filter in self._subscribers:
                if event_filter is None or type(event) in event_filter:
                    callback(event)

    def _notify_position(self, events: Iterable[Event]) -> None:
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
            for r, obj in zip(apply_transform(points), objects_values, strict=True)
        ]

        for callback in self._subscribers_position:
            callback(mapped_points)

    def start_server(self) -> HTTPServer:
        """Start the HTTP server in a daemon thread.

        Returns:
            The running HTTP server. Call ``shutdown`` on it to stop it.
        """
        handler = create_xovis_request_handler(self)
        http_server = HTTPServer((self._host, self._port), handler)
        thread = Thread(target=http_server.serve_forever)
        thread.daemon = True
        thread.start()
        print(f"XOVIS callback server receiver running on {self._host}:{self._port}")
        return http_server
