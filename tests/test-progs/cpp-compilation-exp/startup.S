.text
.global mystart
mystart:
    mov $__stack_top, %esp
    cld
    jmp main
trap:
    jmp trap
