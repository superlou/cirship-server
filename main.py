#!/usr/bin/python3
import time
import asyncio
import websockets
import random
import json
import queue
from multiprocessing import Process, Queue
from sim import Simulation


refs = {}


async def connection_handler(websocket, path, sim_queue, client_queue):
    await websocket.send(build_welcome_msg())
    await asyncio.wait([push_data(websocket, sim_queue),
                        receive_data(websocket, client_queue)])


async def push_data(websocket, sim_queue):
    global refs
    while websocket.open:
        while not sim_queue.empty():
            refs = sim_queue.get_nowait()

        await websocket.send(build_update_msg())
        await asyncio.sleep(0.05)


async def receive_data(websocket, client_queue):
    async for msg in websocket:
        data = json.loads(msg)
        client_queue.put(data)


def build_welcome_msg():
    return json.dumps({
        'type': 'welcome'
    })


def build_update_msg():
    global refs

    return json.dumps({
        'type': 'update',
        'data': refs
    })


def sim_process(sim_queue, client_queue):
    sim = Simulation('../model/Cirship.fmu')
    print('Simulation ready')
    id = 0

    watches = {
        'real': set(),
        'bool': set(),
    }

    while True:
        while not client_queue.empty():
            msg = client_queue.get_nowait()
            if msg['type'] == 'set':
                ref = msg['ref']
                value = msg['value']

                if isinstance(value, bool):
                    sim.set_bool(ref, value)
                else:
                    sim.set_real(ref, value)
            elif msg['type'] == 'watch':
                for ref in msg.get('real', []):
                    watches['real'].add(ref)
                for ref in msg.get('bool', []):
                    watches['bool'].add(ref)

        t = sim.update()
        id += 1

        reals = {ref: sim.get_real(ref) for ref in watches['real']}
        bools = {ref: sim.get_bool(ref) for ref in watches['bool']}

        refs = {
            'id': id,
            'time': t,
            **reals,
            **bools
        }

        sim_queue.put(refs)
        time.sleep(0.05)


def main():
    print('Starting server...')
    sim_queue = Queue()
    client_queue = Queue()
    p = Process(target=sim_process, args=(sim_queue, client_queue))
    p.start()
    start_server = websockets.serve(lambda a, b: connection_handler(a, b, sim_queue, client_queue), 'localhost', 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
