#!/usr/bin/python3
# tested with python 3.4.2 and minimally with python 2.7.9

"""mcpi_fast_query

Function to speed up batch queries on the Minecraft Pi edition.
This performs a batch of queries much more quickly than
performing queries sequentially.

The main function is query_blocks.

If you are using picraft (github.com/waveform80/picraft):
This contains adapters for the vector_range forms of world.blocks
and world.height.
Note that these adapters are single-threaded, so you won't get
maximum performance benefit.

If you are using the original Minecraft (MCPI) APIs
(http://www.stuffaboutcode.com/2013/01/raspberry-pi-minecraft-api-basics.html):
This provides an alternate to world.getHeight and
a functional version of world.getBlocks (plural).

This may work as-is on the Raspberry Juice server, but has not been tested.
"""

from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

import picraft
from picraft import Vector, X, Y, Z

import collections
import io
import random
import select
import socket
import threading
import time
import timeit
try:
    import queue
except ImportError:
    import Queue as queue


def query_blocks(connection, requests, fmt, parse_fn, thread_count = 0):
    """Perform a batch of Minecraft server queries.

    The following Minecraft Pi edition socket query functions
    are supported:
     - world.getBlock(x,y,z) -> blockId
     - world.getBlockWithData(x,y,z) -> blockId,blockData
     - world.getHeight(x,z) -> y

    Parameters:
      connection
              A picraft "connection.Connection" object for an active
              Minecraft server.  Must have attributes:
              _socket, encoding.
      requests
              An iterable of coordinate tuples.  See the examples.
              Note that if thread_count > 0, this will be accessed
              from another thread, and if thread_count > 1, it
              will be accessed from multiple threads.
      fmt
              The request format string, one of:
                  world.getBlock(%d,%d,%d)
                  world.getBlockWithData(%d,%d,%d)
                  world.getHeight(%d,%d)
      parse_fn
              Function to parse the results from the server, one of:
                  int
                  lambda ans: tuple(map(int, ans.split(",")))
              Note that responses have the form "0" or "0,0".
      thread_count
              Number of threads to create.  If thread_count == 0, no
              threads are created and work is done in the current thread.
              If thread_count > 0 and the "requests" parameter is a
              generator function, consider thread safety issues.
              The maximum recommended thread_count == 30 for very large
              query sizes.

    Generated values:
      tuple(request, answer), where
        request - is a value from the "requests" parameter
        answer - is the matching response from the server, as parsed
                 by parse_fn
      Note: If thread_count <= 1, tuples are generated in the same
      order as the "requests" parameter.  Otherwise, there is no such
      guarantee.
    """
    def worker_fn(mc_socket, request_iter, request_lock, answer_queue):
        """Single threaded worker function to keep its socket
        as full of requests as possible.

        The worker does this: Dequeue requests, format them, and
        write them into the socket as fast as it will take them.
        At the same time, read responses from the socket as fast
        as they appear, parse them, match them with the request,
        and enqueue the answers.
        """
        more_requests = True
        request_buffer = bytes()
        response_buffer = bytes()
        pending_request_queue = collections.deque()
        while more_requests or len(pending_request_queue) > 0:
            # Grab more requests
            while more_requests and len(request_buffer) < 4096:
                with request_lock:
                    try:
                        pos = next(request_iter)
                    except StopIteration:
                        more_requests = False
                        continue
                    new_request = (fmt % pos).encode(socket_encoding)
                    request_buffer = request_buffer + new_request + b"\n"
                    pending_request_queue.append(pos)
            if not (more_requests or len(pending_request_queue) > 0):
                continue

            # Select I/0 we can perform without blocking
            w = [mc_socket] if len(request_buffer) > 0 else []
            r, w, x = select.select([mc_socket], w, [], 1)
            allow_read = bool(r)
            allow_write = bool(w)

            # Write requests to the server
            if allow_write:
                # Write exactly once
                bytes_written = mc_socket.send(request_buffer)
                request_buffer = request_buffer[bytes_written:]
                if bytes_written == 0:
                    raise RuntimeError("unexpected socket.send()=0")

            # Read responses from the server
            if allow_read:
                # Read exactly once
                bytes_read = mc_socket.recv(1024)
                response_buffer = response_buffer + bytes_read
                if bytes_read == 0:
                    raise RuntimeError("unexpected socket.recv()=0")

            # Parse the response strings
            responses = response_buffer.split(b"\n")
            response_buffer = responses[-1]
            responses = responses[:-1]
            for response_string in responses:
                request = pending_request_queue.popleft()
                answer_queue.put((request, parse_fn(response_string.decode(socket_encoding))))

    socket_encoding = connection.encoding
    request_lock = threading.Lock()
    answer_queue = queue.Queue()
    if thread_count == 0:
        worker_fn(connection._socket,
                  iter(requests),
                  request_lock,
                  answer_queue)
    else:
        sockets = []
        socket_host, socket_port = connection._socket.getpeername()
        try:
            for i in range(thread_count):
                sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                sockets[-1].connect((socket_host, socket_port))
            workers = []
            threading.stack_size(128 * 1024)  # bytes; reset when done?
            for w in range(thread_count):
                t = threading.Thread(target = worker_fn,
                                     args = (sockets[w],
                                             iter(requests),
                                             request_lock,
                                             answer_queue))
                t.start()
                workers.append(t)
            for w in workers:
                w.join()
        except socket.error as e:
            print("Socket error:", e)
            print("Is the Minecraft server running?")
            raise e
        finally:
            for s in sockets:
                try:
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                except socket.error as e:
                    pass
    while not answer_queue.empty():
        yield answer_queue.get()


def alt_picraft_getblock_vrange(world, vrange):
    """Drop-in replacement for picraft: b = world.blocks[vrange]

    This is intended as a drop-in replacement for
    picraft.world.World.blocks.__getitem__(vector_range).
    This invokes query_blocks and returns a list of block data
    in the same order as the input vrange.
    Note that vrange is iterated twice.
    """
    ans = { pos: data for (pos, data) in
            query_blocks(world.connection,
                         vrange,
                         "world.getBlockWithData(%d,%d,%d)",
                         lambda ans: tuple(map(int, ans.split(",")))) }
    return [picraft.Block(*ans[v]) for v in vrange]


def alt_picraft_getheight_vrange(world, vrange):
    """Drop-in replacement for picraft: b = world.height[vrange]

    This is intended as a drop-in replacement for
    picraft.world.World.height.__getitem__(vector_range).
    This invokes query_blocks and returns a list of vectors
    in the same order as the input vrange.
    Alternate design: If thread_count > 1 is desired, this could
    first get the query_blocks dict, then iterate vrange again.
    """
    return [Vector(pos[0], data, pos[1]) for (pos, data) in
            query_blocks(world.connection,
                         ((v[0], v[2]) for v in vrange),
                         "world.getHeight(%d,%d)",
                         int,
                         thread_count = 0)]


if __name__ == "__main__":
    world = picraft.World()
    world.say("Hello mcpi_fast_query!")

    cuboid = picraft.vector_range(Vector(-2, 0, -2), Vector(2, 0, 2) + 1)
    my_blocks = {}
    for pos, blk in query_blocks(
            world.connection,
            cuboid,
            "world.getBlockWithData(%d,%d,%d)",
            lambda ans: tuple(map(int, ans.split(","))),
            thread_count=0):
        my_blocks[pos] = blk
    #print(my_blocks)
    
    x = alt_picraft_getblock_vrange(world, cuboid)
    print(x)
    y = world.blocks[cuboid]
    #print(y)
    print(x==y)

    h = alt_picraft_getheight_vrange(world, cuboid)
    print(h)

