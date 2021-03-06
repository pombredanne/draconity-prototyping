DEBUG = False


class RingBuffer(object):
    def __init__(self, size):
        self.buffer = bytearray(size)
        self.start = 0
        self.num_bytes_used = 0

    def __repr__(self):
        return "RingBuffer(start={}, num_bytes_used={}, buffer={})".format(
            self.start, self.num_bytes_used, self.buffer
        )

    def bytes_total(self):
        return len(self.buffer)

    def bytes_used(self):
        return self.num_bytes_used

    def bytes_free(self):
        return self.bytes_total() - self.bytes_used()

    def write(self, bs):
        if len(bs) > self.bytes_free():
            message = "Can't fit {} bytes into buffer ({} used, {} free of total {})".format(
                len(bs), self.bytes_used(), self.bytes_free(), self.bytes_total()
            )
            raise ValueError(message)

        bs_offset = 0
        # first, fit as much as we can into space between end and buffer end
        # (only possible if the buffer hasn't wrapped yet)
        if self.start + self.num_bytes_used < len(self.buffer):
            offset_start = self.start + self.num_bytes_used
            offset_end = min(offset_start + len(bs), len(self.buffer))
            bs_offset = offset_end - offset_start
            if DEBUG:
                print("1-writing", bs[:bs_offset], "end is:", offset_end)
            self.buffer[offset_start:offset_end] = bs[:bs_offset]
            self.num_bytes_used += offset_end - offset_start

        # secondly, fit the remainder at the start of the buffer
        if bs_offset < len(bs):  # (only if there's anything left to write)
            offset_start = (self.start + self.num_bytes_used) % len(self.buffer)
            offset_end = offset_start + len(bs) - bs_offset
            if DEBUG:
                print("2-writing", bs[bs_offset:])
            self.buffer[offset_start:offset_end] = bs[bs_offset:]
            self.num_bytes_used += offset_end - offset_start

    def read(self):
        if self.bytes_used() == 0:
            return None

        if self.start + self.num_bytes_used < len(self.buffer):
            offset_start = self.start
            offset_end = offset_start + self.num_bytes_used
            self.start = offset_end
            if DEBUG:
                print("1-read, offset start:", offset_start, "offset end", offset_end)
        else:
            # buffer has wrapped, so return as much as we can, then next
            # time we'll read from the start of the buffer to get the rest
            offset_start = self.start
            offset_end = len(self.buffer)
            self.start = 0
            if DEBUG:
                print("2-read, offset start:", offset_start, "offset end", offset_end)
        self.num_bytes_used -= offset_end - offset_start
        return self.buffer[offset_start:offset_end]

    def read_exactly(self, desired_bytes):
        if desired_bytes < 0:
            raise ValueError("desired bytes of {} is less than 0".format(desired_bytes))
        elif self.bytes_used() < desired_bytes:
            return None

        read_bytes = bytearray()

        # first read from start pos to potentially the end of the buffer
        offset_start = self.start
        offset_end = min(len(self.buffer), offset_start + desired_bytes)
        read_bytes.extend(self.buffer[offset_start:offset_end])
        self.start = offset_end
        if DEBUG:
            print("1-read-x, offset start:", offset_start, "offset end", offset_end)

        # if we have more bytes to read still, we need to read from start
        # of buffer to the last used portion of it
        if len(read_bytes) < desired_bytes:
            offset_start = 0
            offset_end = desired_bytes - len(read_bytes)
            read_bytes.extend(self.buffer[offset_start:offset_end])
            self.start = offset_end
            if DEBUG:
                print("2-read-x, offset start:", offset_start, "offset end", offset_end)

        self.num_bytes_used -= len(read_bytes)
        return read_bytes
