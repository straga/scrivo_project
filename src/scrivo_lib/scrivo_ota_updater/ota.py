
import hashlib
import esp

from esp32 import Partition
from scrivo.dev import _buffer

try:
    import ubinascii as binascii
    import upip_utarfile as utar
except Exception:
    import binascii
    import tarfile as utar


from scrivo import logging
log = logging.getLogger("OTA")
# log.setLevel(logging.DEBUG)


class OtaUpdater:

    def __init__(self,):

        self.CHUNK_SIZE = 1024
        self.SEC_SIZE = 4096

        self.upd_type = None
        self.upd_size = 0
        self.upd_hash = None

        self.next_part = ""
        self.cur_part = ""
        self.set_part()

        self.status = 0.0


        self.data = None
        self.step = ''
        self.update_part = None

    # Partition
    def set_part(self):
        runningpart = Partition(Partition.RUNNING)
        part_info = runningpart.info()
        part_name = part_info[4]

        if part_name == "ota_0":
            self.next_part = "ota_1"
        elif part_name == "ota_1":
            self.next_part = "ota_0"
        self.cur_part = part_name

    def partition_init(self, update_hash, update_size):

        result = {}
        parts = Partition.find(label=self.next_part)  # search Partition for update

        if parts:
            # Make update partition
            self.update_part = UpdatePart(next_part=self.next_part, cur_part=self.cur_part,
                                          chunk_size=self.CHUNK_SIZE, sec_size=self.SEC_SIZE)
            self.update_part.set_part(parts[0])
            self.upd_hash = update_hash
            self.upd_size = update_size

            log.info("= : upd_hash: {}".format(self.upd_hash))
            log.info("= : upd_size: {}".format(self.upd_size))

            result["CHUNK_SIZE"] = self.CHUNK_SIZE

            # calc pieces
            pieces = int(self.upd_size / self.CHUNK_SIZE) + (self.upd_size % self.CHUNK_SIZE > 0)
            # last_piece = (pieces - 1)
            log.info("= : DATA (pieces): {}".format(pieces))

            result["pieces"] = pieces
            # result["last_piece"] = last_piece

        return result

    def partition_flash(self, data, next_id):
        datab = binascii.a2b_base64(data)
        self.update_part.write_partition_chunk(datab, next_id-1)

        # log.info("-> peace: {}".format(next_id))

        result = {"done": next_id}
        return result

    def check_partition_init(self):
        pieces = self.update_part.check_partition_init(self.upd_hash, self.upd_size)

        log.info("HASH Start ".format(""))

        result = {"pieces": pieces}
        return result

    def check_partition_chunk(self, pieces, next_id):
        result = {"next_id": next_id}
        next_id = next_id - 1
        self.update_part.check_partition_chunk(pieces, next_id)

        # log.debug("HASH {}".format(next_id))

        return result

    def check_partition_result(self):
        valid = self.update_part.check_partition_result()
        result = {"Hash valid:": valid}
        return result


class UpdatePart:

    def __init__(self, next_part, cur_part, chunk_size=512, sec_size=4096):

        self.CHUNK_SIZE = chunk_size
        self.SEC_SIZE = sec_size
        self.CHUNK_PER_SECTOR = self.SEC_SIZE // self.CHUNK_SIZE

        self.next_boot_part = next_part
        self.cur_boot_part = cur_part

        self.part = None
        self.part_start = None
        self.part_size = None
        self.part_base_sec = None

        self.position = None
        self.updatehash = None
        self.hash = None
        self.step_hash = 0

        self.buf_sz = 0

        self.status = 0

    def set_part(self, part):
        self.part = part
        self.part_start = part.info()[2]
        self.part_size = part.info()[3]
        self.part_base_sec = self.part_start // self.SEC_SIZE

    # FLASH / before write - need clear sector
    def write_partition_chunk(self, buffer, next_id):
        # log.info('Write posit = {}'.format(self.part_start + self.CHUNK_SIZE * next_id))
        if next_id % self.CHUNK_PER_SECTOR == 0:
            esp.flash_erase(self.part_base_sec + next_id // self.CHUNK_PER_SECTOR)
        esp.flash_write(self.part_start + self.CHUNK_SIZE * next_id, buffer)
        return len(buffer)

    # Hash
    def check_partition_init(self, updatehash, updatesize):
        self.updatehash = updatehash
        self.hash = hashlib.sha256()
        buf_sz = int((updatesize / self.CHUNK_SIZE - updatesize // self.CHUNK_SIZE) * self.CHUNK_SIZE)
        # (44560 / 512 - 44560 // 512 ) * 512 = 16 : last peace check if == chunk size
        log.debug('last buf_sz {}'.format(buf_sz))
        if buf_sz == 0:
            buf_sz = self.CHUNK_SIZE

        self.buf_sz = buf_sz

        self.position = self.part_start
        pieces = int(updatesize / self.CHUNK_SIZE) + (updatesize % self.CHUNK_SIZE > 0)
        log.info('Pieces for hash check: {}, start from {}'.format(pieces, self.position))

        return pieces

    def check_partition_chunk(self, pieces, step):

        # log.debug('Hash position = {}'.format(self.position))

        # if last piece - use buffer size same as piece size
        if step == pieces-1:
            buf = _buffer(self.buf_sz)
        else:
            buf = _buffer(self.CHUNK_SIZE)

        esp.flash_read(self.position, buf)

        self.hash.update(buf)
        self.position += len(buf)

    def check_partition_result(self):
        parthash = (binascii.hexlify(self.hash.digest()).decode())

        log.info('partition hash is "{}", should be "{}"'.format(parthash, self.updatehash))
        return parthash == self.updatehash

