#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
memory information for memory visualization tool
"""
import gdb
from elftools.elf.elffile import ELFFile
import pwndbg.vmmap
import pwndbg.regs


class MemInfo:
    """
    region = [<start>, <end>]
    regs   = {"rax":<int value>, ...}
    frames = {"func name":<start addr>, ...}
    marks  = [<addr1>, <addr2>, ...]
    """
    executable      = [-1, -1]
    text_section    = [-1, -1]
    plt_section     = [-1, -1]
    got_section     = [-1, -1]
    pltgot_section  = [-1, -1]
    gotplt_section  = [-1, -1]
    data_section    = [-1, -1]
    bss_section     = [-1, -1]
    libc            = [-1, -1]
    ld              = [-1, -1]
    stack           = [-1, -1]
    heap            = [-1, -1]
    regs            = {}
    frames          = {}
    marks           = []



"""
update all information of meminfo to newest
and return the meminfo
"""
def get():
    meminfo = MemInfo()
    get_vmmap(meminfo)
    get_elfheader(meminfo)
    get_regs(meminfo)
    get_frames(meminfo)
    return meminfo



"""
update all information of meminfo to newest
and set <value> to the meminfo member specified by <target>
and return the meminfo
"""
def set(target, value):
    meminfo = get()
    if target=="marks":
        if(is_valid_addr(meminfo, value)):
            meminfo.marks.append(value)
    return meminfo



"""
unset <value> from the meminfo member specified by <target>
and return updated meminfo
"""
def unset(target, value):
    meminfo = get()
    if len(meminfo.marks)<1:
        return meminfo
    if target=="marks":
        if value in meminfo.marks:
            meminfo.marks.remove(value)
    return meminfo




"""
check if <addr> is valid memory address
(check if <addr> is in between max/min address of meminfo)
- Ex) if <addr> is -0x1, this is not valid memory address so return False
"""
def is_valid_addr(meminfo, addr):
    max_addr = meminfo.stack[1]
    if exists(meminfo, "plt_section"):
        min_addr = meminfo.plt_section[0]
    elif exists(meminfo, "pltgot_section"):
        min_addr = meminfo.pltgot_section[0]
    else:
        min_addr = meminfo.text_section[0]

    if min_addr<=addr and addr<=max_addr:
        return True
    else:
        return False


"""
check if given <region> exists
(check if meminfo's <region> member doesn't have -1 as value)
- Ex1) if <region> is "stack" it exists in meminfo so return "True" 
- Ex2) if <region> is "hoge" it doesn't exists in meminfo so return "False"
[!!] only eligible for region that is initialized with -1
"""
def exists(meminfo, region):
    try:
        member = getattr(meminfo, region)
    except AttributeError:
        return False
    if type(member)==list:
        if -1 in member:
            return False
        else:
            return True
    return False



"""
can retrive
- executable mapped location
- stack location
- heap location
- libc location
- loader location
"""
def get_vmmap(meminfo):
    vmmap = pwndbg.vmmap.get()

    for page in vmmap:
        if page.is_memory_mapped_file:
            filename = page.objfile.split("/")[-1]
            if filename[-3:]==".so":
                if filename[0:4]=="libc":
                    if meminfo.libc[0] == -1:
                        meminfo.libc[0] = page.start
                    if meminfo.libc[1] < page.end:
                        meminfo.libc[1] = page.end
                if filename[0:2]=="ld":
                    if meminfo.ld[0] == -1:
                        meminfo.ld[0] = page.start
                    if meminfo.ld[1] < page.end:
                        meminfo.ld[1] = page.end
            else:
                if meminfo.executable[0] == -1:
                    meminfo.executable[0] = page.start
                if meminfo.executable[1] < page.end:
                    meminfo.executable[1] = page.end
        if page.is_stack:
            meminfo.stack[0] = page.start
            meminfo.stack[1] = page.end
            
        if page.objfile=="[heap]":
            meminfo.heap[0] = page.start
            meminfo.heap[1] = page.end

    return meminfo


"""
can retrive
- section of loaded executable
"""
def get_elfheader(meminfo):
    local_path = pwndbg.file.get_file(pwndbg.proc.exe)

    with open(local_path, 'rb') as f:
        elffile = ELFFile(f)
        sections = []
        for section in elffile.iter_sections():
            start = section['sh_addr']

            # Don't print sections that aren't mapped into memory
            if start == 0:
                continue

            size = section['sh_size']
            sections.append((start, start + size, section.name))

        sections.sort()

        for start, end, name in sections:
            start += meminfo.executable[0]
            end   += meminfo.executable[0]
            if name == ".text":
                meminfo.text_section[0] = start
                meminfo.text_section[1] = end
            if name == ".data":
                meminfo.data_section[0] = start
                meminfo.data_section[1] = end
            if name == ".plt":
                meminfo.plt_section[0] = start
                meminfo.plt_section[1] = end
            if name == ".got":
                meminfo.got_section[0] = start
                meminfo.got_section[1] = end
            if name == ".plt.got":
                meminfo.pltgot_section[0] = start
                meminfo.pltgot_section[1] = end
            if name == ".got.plt":
                meminfo.gotplt_section[0] = start
                meminfo.gotplt_section[1] = end
            if name == ".bss":
                meminfo.bss_section[0] = start
                meminfo.bss_section[1] = end


"""
can retrive
- all register value
"""
def get_regs(meminfo):
    regs = pwndbg.regs
    for gpr in regs.current.gpr:
        meminfo.regs[gpr] = regs[gpr]
    meminfo.regs[regs.current.stack] = regs[regs.current.stack]
    meminfo.regs[regs.current.frame] = regs[regs.current.frame]
    meminfo.regs[regs.current.pc]    = regs.pc


"""
can retrive
- all stack frame start addr
"""
def get_frames(meminfo):
    all_frames = []
    current_frame = gdb.newest_frame()

    # get all stack frames
    while True:
        all_frames.append(current_frame)
        try:
            candidate = current_frame.older()
        except gdb.MemoryError:
            break

        if not candidate:
            break
        current_frame = candidate

    # get start address of each frames
    for f in all_frames:
        if f.is_valid():
            if f.older()!=None and f.older().read_register(pwndbg.regs.frame)!=f.read_register(pwndbg.regs.frame):
                if f.name()=="__libc_start_main":
                    # somehow rbp points wrong address on __libc_start_main
                    continue
                else:
                    meminfo.frames[f.name()] = int(f.read_register(pwndbg.regs.frame))
