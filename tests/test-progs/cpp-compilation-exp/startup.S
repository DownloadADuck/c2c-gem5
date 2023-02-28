.text
.global mystart
mystart:
    mov $__stack_top, %esp
    cld
    call main
trap:
    jmp trap
