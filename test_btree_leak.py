# test_btree_leak.py
# Demonstrates two native C-heap memory leaks in unmodified extmod/modbtree.c:
#   1. Unclosed btree collected by GC (missing mp_obj_malloc_with_finaliser / __del__)
#   2. btree.close() when flushing (__bt_sync) fails (e.g. disk full or closed stream)

import io
import gc
import btree

try:
    import esp32
    def free_c_heap():
        return sum(r[1] for r in esp32.idf_heap_info(esp32.HEAP_DATA))
except ImportError:
    esp32 = None
    def free_c_heap():
        return None


def test_gc_finalizer_leak():
    gc.collect()
    before = free_c_heap()
    print("=== Test 1: GC Finalizer Leak (del bt without bt.close()) ===")
    print("C heap before :", before)

    bt = btree.open(io.BytesIO(), cachesize=4096)
    during = free_c_heap()
    print("C heap opened :", during)

    del bt
    gc.collect()
    after = free_c_heap()
    print("C heap after  :", after)

    if before is not None:
        leaked = before - after
        print("Result        :", "PASS (0 bytes leaked)" if leaked <= 0 else "FAIL (leaked %d bytes)" % leaked)


def test_failed_sync_on_close_leak():
    class FullStream(io.IOBase):
        def readinto(self, buf):
            return 0
        def write(self, buf):
            return 0       # simulate full disk (short write -> RET_ERROR in __bt_sync)
        def ioctl(self, req, arg):
            return 0

    gc.collect()
    before = free_c_heap()
    print("\n=== Test 2: Failed Sync in bt.close() Leak ===")
    print("C heap before :", before)

    s = FullStream()
    bt = btree.open(s, cachesize=4096)
    bt[b"k"] = b"v"        # mark tree B_MODIFIED

    try:
        bt.close()
    except OSError:
        pass

    del bt, s
    gc.collect()
    after = free_c_heap()
    print("C heap after  :", after)

    if before is not None:
        leaked = before - after
        print("Result        :", "PASS (0 bytes leaked)" if leaked <= 0 else "FAIL (leaked %d bytes)" % leaked)


if __name__ == "__main__":
    test_gc_finalizer_leak()
    test_failed_sync_on_close_leak()
