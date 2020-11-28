import sys


class Progress:
    def __init__(self, total, message='progress'):
        self.message = message
        self.total = total
        self.current = 0

    def next(self, step=1, extra_message=''):
        bar_length, status = 20, ""
        self.current += step
        progress = float(self.current) / float(self.total)
        if progress >= 1.:
            progress = 1
        block = int(round(bar_length * progress))
        text = "\r{} [{}] {:.0f}% {} {}".format(self.message,
                                                "#" * block + "-" * (bar_length - block), round(progress * 100, 0),
                                                status, extra_message)
        sys.stdout.write(text)
        sys.stdout.flush()

    @staticmethod
    def finish():
        sys.stdout.write("\n")
        sys.stdout.flush()

    @staticmethod
    def print_counter(counter, message):
        text = "\r{}: {}".format(message, counter)
        sys.stdout.write(text)
        sys.stdout.flush()
