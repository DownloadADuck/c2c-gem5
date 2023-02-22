MEMORY
{
  ram (rwx) : ORIGIN = 0x20000000, LENGTH = 0x4000
}

SECTIONS
{
  .text :
  {
    *(.text)
  } > ram

  .data :
  {
    *(.data)
  } > ram

  .bss :
  {
    *(.bss)
  } > ram
}