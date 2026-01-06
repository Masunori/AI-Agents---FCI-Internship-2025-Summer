from queue import Queue

def file_writer(path: str, q: Queue):
    """Thread worker function to write log messages to a file."""
    with open(path, 'a', encoding='utf-8') as f:
        while True:
            message = q.get()
            if message is None:
                break
            f.write(message + '\n')
            f.flush()
            q.task_done()