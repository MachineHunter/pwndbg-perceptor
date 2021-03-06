import sys
import time
import memGUI
import threading
import copy

class MemInfo:
    """
    page = [<start>, <end>]
    """
    executable      = [0x555555554000, 0x555555559000]
    plt_section     = [0x555555555020, 0x555555555040]
    pltgot_section  = [0x555555555040, 0x555555555048]
    text_section    = [0x555555555050, 0x5555555551b1]
    got_section     = [0x555555557fd8, 0x555555558000]
    gotplt_section  = [0x555555558000, 0x555555558020]
    data_section    = [0x555555558020, 0x555555558030]
    bss_section     = [0x555555558030, 0x555555558038]
    heap            = [0x555555560020, 0x555555581020]
    libc            = [0x7ffff7ddb000, 0x7ffff7f9c000]
    ld              = [0x7ffff7fd2000, 0x7ffff7ffe000]
    stack_unused    = [0x7ffffffde000, 0x7ffffffdf000]
    stack_used      = [0x7ffffffdf000, 0x7ffffffff000]
    regs            = {"rip":0x555555555080, "rsp":0x7fffffffe000}
    frames          = {"main":[0x7ffffffed008, 0x7ffffffff000], "aaa": [0x7ffffffdf000, 0x7ffffffed000]}
    marks           = [0x555555558010, 0x555555570020]

if __name__ == '__main__':
    app = memGUI.MemoryApp()
    #app.set_meminfo(meminfo)
    th_app = threading.Thread(target=memGUI.app_run, args=(app,))
    th_app.start()

    time.sleep(1)
    meminfo = MemInfo()
    app.set_address(meminfo)
    