from lib.pubsub import clean_routine
from lib.pubsub.redis import Redis_Subscriber

subscriber = Redis_Subscriber()
subscriber.callback_function = clean_routine

if __name__ == '__main__':
    while True:
        try:
            subscriber.run()
        except KeyboardInterrupt:
            subscriber.stop()
