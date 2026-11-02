[README.md](https://github.com/user-attachments/files/34283594/README.md)

## Possible memory leak bug

There might be a memory leak bug in the `extmod/modbtree.c` file. Here you can find a test script called `test_btree_leak.py` and a possible fix in the `extmod` directory.

### Test runs

Run log on unpatch `extmod/modbtree.c`

```
$ mpr u1 run test_btree_leak.py
=== Test 1: GC Finalizer Leak (del bt without bt.close()) ===
C heap before : 120472
C heap opened : 110048
C heap after  : 110048
Result        : FAIL (leaked 10424 bytes)

=== Test 2: Failed Sync in bt.close() Leak ===
C heap before : 110048
C heap after  : 99624
Result        : FAIL (leaked 10424 bytes)

$ mpr u1 run test_btree_leak.py
=== Test 1: GC Finalizer Leak (del bt without bt.close()) ===
C heap before : 99624
C heap opened : 89200
C heap after  : 89200
Result        : FAIL (leaked 10424 bytes)

=== Test 2: Failed Sync in bt.close() Leak ===
C heap before : 89200
C heap after  : 78776
Result        : FAIL (leaked 10424 bytes)
```

You can see that the amount of C heap decreased after each test run.


Run log on patched `extmod/modbtree.c`

```
$ mpr u0 run test_btree_leak.py
=== Test 1: GC Finalizer Leak (del bt without bt.close()) ===
C heap before : 136904
C heap opened : 126224
C heap after  : 136904
Result        : PASS (0 bytes leaked)

=== Test 2: Failed Sync in bt.close() Leak ===
C heap before : 136904
C heap after  : 136904
Result        : PASS (0 bytes leaked)

$ mpr u0 run test_btree_leak.py
=== Test 1: GC Finalizer Leak (del bt without bt.close()) ===
C heap before : 136904
C heap opened : 126224
C heap after  : 136904
Result        : PASS (0 bytes leaked)

=== Test 2: Failed Sync in bt.close() Leak ===
C heap before : 136904
C heap after  : 136904
Result        : PASS (0 bytes leaked)
```

### The patch btree

The patched file is `extmod/modbtree.c` 

Patch diff
```
 diff modbtree.c modbtree.c-ORIG
98d97
< // 1. In btree_new(): use mp_obj_malloc_with_finaliser instead of mp_obj_malloc
100,101c99
<     mp_obj_btree_t *o = mp_obj_malloc_with_finaliser(mp_obj_btree_t, (mp_obj_type_t
<     *)&btree_type);
---
>     mp_obj_btree_t *o = mp_obj_malloc(mp_obj_btree_t, (mp_obj_type_t *)&btree_type);
130d127
< // 2. In btree_close(): ensure C heap (mpool, BTREE, DB) is still freed even if __bt_sync fails
132a130
>     int res;
134,141c132
<         int res = __bt_close(self->db);
<         if (res == RET_ERROR) {
<             // __bt_sync failed (e.g. disk full, or stream already closed during GC sweep).
<             // Clear B_MODIFIED so __bt_close skips __bt_sync and frees MPOOL/BTREE/DB.
<             BTREE *t = self->db->internal;
<             F_CLR(t, B_MODIFIED);
<             __bt_close(self->db);
<         }
---
>         res = __bt_close(self->db);
143,145c134,135
< 	if (res == RET_ERROR) {
<                 mp_raise_OSError(errno);
<         }
---
>     } else {
>         res = RET_SUCCESS; // Closing an already-closed DB always succeeds.
147c137
<     return mp_const_none;
---
>     return MP_OBJ_NEW_SMALL_INT(res);
364d353
<     { MP_ROM_QSTR(MP_QSTR___del__), MP_ROM_PTR(&btree_close_obj) },
```

### AI assistance
AI-assisted help with the **agy** cli running Gemini-4-Argon.
