import inspect
import asyncio as aio

# this is based on the concept of the closeable queue
from .ClosableQueue import ClosableQueue, ClosableQueueClosed

# broadcaster channel is closed exception
class BroadcasterClosed(Exception):
    pass

# broadcaster class. incorporate this to classes that produce events to which 
# others can subscribe. Use Broadcaseter.close() to notify the observers that 
# event broadcasting will no longer take place.
class Broadcaster:
    # constructor
    def __init__(self):
        # list of observers
        self._observers = []

    # broadcast to all listeners
    async def broadcast(self, event, data):
        # go through the callback list 
        for observer in self._observers:
            await observer.notify(event, data)
    
    # register the observer
    def register(self, observer):
        self._observers.append(observer)

    # unregister the observer
    def unregister(self, observer):
        self._observers.remove(observer)
    
    # close the broadcasting channel
    def close(self, exc=None):
        # notify all observers of closure
        for observer in self._observers:
            observer.close(exc)


# observer does not hold any notifications
class ObserverEmpty(Exception):
    pass

# observer class based on the concept of closable-queue
class Observer:
    # constructor that subscribes to the given 'broadcaster' and accepts the 
    # events that have a name present in 'events'. 'events' can be None, meaing 
    # that any event shall be accepted OR a string meaning that only events with 
    # name equal to that string will be observed OR a list of strings.
    def __init__(self, broadcaster:Broadcaster, events=None, callback=None, 
            *args, **kwargs):
        # initialize super-class
        self._q = ClosableQueue()

        # store acceptable events
        self._events = events
        
        # store the callback 
        self._callback = callback
        # ... and it's arguments
        self._callback_args, self._callback_kwargs = args, kwargs

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
    
    # close the channel
    def close(self):
        self._q.close()

    # send notification to observer
    async def notify(self, event, data):
        # filter out unwanted events
        if self._events is None or event is self._events or \
            event in self._events:
            # store in queue
            await self._q.put((event, data))
            # shorthand
            args, kwargs = self._callback_args, self._callback_kwargs
            # got callback function that is a coroutine?
            if inspect.iscoroutinefunction(self._callback):
                await self._callback(self, *args, **kwargs)
            # synchronous callback?
            elif callable(self._callback):
                self._callback(self, *args, **kwargs)

    # get data from the broadcaster
    async def get(self):
        try:
            return await self._q.get()
        # re-raise the exception with appropriate class
        except ClosableQueueClosed as e:
            raise BroadcasterClosed() from e
    
    # get data from the broadcaster without waiting
    def get_nowait(self):
        try:
            return self._q.get_nowait()
        # re-raise the exception with appropriate class
        except ClosableQueueClosed as e:
            raise BroadcasterClosed() from e
        # nowait calls may result in 'empty' exception generation
        except aio.QueueEmpty as e:
            raise ObserverEmpty() from e

    