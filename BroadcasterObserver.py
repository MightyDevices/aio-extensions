import asyncio as aio

# this is based on the concept of the closeable queue
from .ClosableQueue import *

# broadcaster channel is closed
class BroadcasterClosed(Exception):
    pass

# broadcaster class
class Broadcaster:
    # constructor
    def __init__(self):
        # list of observers
        self._observers = []

    # broadcast to all listeners
    async def broadcast(self, event, data):
        # go through the callback list 
        for observer in self._observers:
            await observer.put(event, data)
    
    # register the observer
    def register(self, observer):
        self._observers.append(observer)

    # unregister the observer
    def unregister(self, observer):
        self._observers.remove(observer)
    
    # close the broadcasting channel
    def close(self, exc=None):
        # notify all observers of closure
        for observer in self._observers
            observer.close(exc)

# observer class
class Observer(ClosableQueue):
    # constructor
    def __init__(self, broadcaster:Broadcaster, events=None):
        # store acceptable events
        self._events = events
        # store the broadcaster reference
        self._broadcaster = broadcaster
        # register ourselves for notifications
        self._broadcaster.register(self)
    
    # enter the context
    def __enter__(self):
        return self

    # exit the context where the object lived
    def __exit__(self, exc_type, exc_val, exc_tb):
        # unregister from the broadcasting channel
        self._broadcaster.unregister(self)
    
    # put data to the queue
    async def _put(self, event, data):
        # filter out unwanted events
        if self._events is None or event is self._events or \
            event in self._events:
            await super().put((event, data))

    # get data from the broadcaster
    async def get(self):
        try:
            return super().get()
        # re-raise the exception with appropriate class
        except ClosableQueueClosed as e:
            raise BroadcasterClosed() from e
    