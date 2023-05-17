	.file	"reduction.cpp"
	.text
	.section	.text._ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv,"axG",@progbits,_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv,comdat
	.align 2
	.p2align 4,,15
	.weak	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv
	.type	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv, @function
_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv:
.LFB3206:
	.cfi_startproc
	movq	%rdi, %rax
	subq	$16, %rsp
	.cfi_def_cfa_offset 24
	movl	24(%rdi), %ecx
	movq	32(%rdi), %rdx
	movq	40(%rdi), %rsi
	movq	48(%rdi), %rdi
	pushq	8(%rax)
	.cfi_def_cfa_offset 32
	movl	16(%rax), %r9d
	movl	20(%rax), %r8d
	call	*56(%rax)
	addq	$24, %rsp
	.cfi_def_cfa_offset 8
	ret
	.cfi_endproc
.LFE3206:
	.size	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv, .-_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv
	.text
	.p2align 4,,15
	.globl	_Z9array_addPiS_S_iiiS_
	.type	_Z9array_addPiS_S_iiiS_, @function
_Z9array_addPiS_S_iiiS_:
.LFB2624:
	.cfi_startproc
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	movq	%rsi, %r15
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	movq	%rdi, %r14
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	movl	%r8d, %r12d
	movq	%rdx, %rbx
	movl	%r9d, %r13d
	subq	$24, %rsp
	.cfi_def_cfa_offset 80
	movl	%ecx, 8(%rsp)
	movq	80(%rsp), %rbp
	call	m5_rpns
#APP
# 50 "reduction.cpp" 1
	
# Begin loop code
# 0 "" 2
#NO_APP
	movl	8(%rsp), %ecx
	cmpl	%r13d, %ecx
	jge	.L5
	movslq	%r12d, %rax
	movslq	%ecx, %r12
	movq	%rax, 8(%rsp)
	.p2align 4,,10
	.p2align 3
.L6:
	movl	(%r15,%r12,4), %eax
	addl	(%r14,%r12,4), %eax
	movl	$sum_mutex, %edi
	movl	%eax, (%rbx,%r12,4)
	call	pthread_mutex_lock
	movl	(%rbx,%r12,4), %eax
	addl	%eax, 0(%rbp)
	movl	$sum_mutex, %edi
	call	pthread_mutex_unlock
	addq	8(%rsp), %r12
	cmpl	%r12d, %r13d
	jg	.L6
.L5:
#APP
# 57 "reduction.cpp" 1
	
# End loop code
# 0 "" 2
#NO_APP
	addq	$24, %rsp
	.cfi_def_cfa_offset 56
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	jmp	m5_rpns
	.cfi_endproc
.LFE2624:
	.size	_Z9array_addPiS_S_iiiS_, .-_Z9array_addPiS_S_iiiS_
	.section	.text._ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev,"axG",@progbits,_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED5Ev,comdat
	.align 2
	.p2align 4,,15
	.weak	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev
	.type	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev, @function
_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev:
.LFB3186:
	.cfi_startproc
	movq	$_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE+16, (%rdi)
	jmp	_ZNSt6thread6_StateD2Ev
	.cfi_endproc
.LFE3186:
	.size	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev, .-_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev
	.weak	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED1Ev
	.set	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED1Ev,_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED2Ev
	.section	.text._ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev,"axG",@progbits,_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED5Ev,comdat
	.align 2
	.p2align 4,,15
	.weak	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev
	.type	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev, @function
_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev:
.LFB3188:
	.cfi_startproc
	pushq	%rbx
	.cfi_def_cfa_offset 16
	.cfi_offset 3, -16
	movq	%rdi, %rbx
	movq	$_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE+16, (%rdi)
	call	_ZNSt6thread6_StateD2Ev
	movq	%rbx, %rdi
	popq	%rbx
	.cfi_def_cfa_offset 8
	jmp	_ZdlPv
	.cfi_endproc
.LFE3188:
	.size	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev, .-_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev
	.section	.rodata.str1.1,"aMS",@progbits,1
.LC0:
	.string	"Usage: "
.LC1:
	.string	" [num_values]"
.LC2:
	.string	"Running on "
.LC3:
	.string	" cores. "
.LC4:
	.string	"with "
.LC5:
	.string	" values"
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align 8
.LC8:
	.string	"Waiting for other threads to complete"
	.section	.rodata.str1.1
.LC9:
	.string	"Success! "
.LC10:
	.string	"c["
.LC11:
	.string	"] is wrong."
.LC12:
	.string	" Expected "
.LC13:
	.string	" Got "
.LC14:
	.string	"."
.LC15:
	.string	"Validating..."
	.section	.text.startup,"ax",@progbits
	.p2align 4,,15
	.globl	main
	.type	main, @function
main:
.LFB2625:
	.cfi_startproc
	.cfi_personality 0x3,__gxx_personality_v0
	.cfi_lsda 0x3,.LLSDA2625
	pushq	%r15
	.cfi_def_cfa_offset 16
	.cfi_offset 15, -16
	pushq	%r14
	.cfi_def_cfa_offset 24
	.cfi_offset 14, -24
	pushq	%r13
	.cfi_def_cfa_offset 32
	.cfi_offset 13, -32
	pushq	%r12
	.cfi_def_cfa_offset 40
	.cfi_offset 12, -40
	pushq	%rbp
	.cfi_def_cfa_offset 48
	.cfi_offset 6, -48
	pushq	%rbx
	.cfi_def_cfa_offset 56
	.cfi_offset 3, -56
	subq	$72, %rsp
	.cfi_def_cfa_offset 128
	cmpl	$1, %edi
	je	.L35
	cmpl	$2, %edi
	movq	%rsi, %rbx
	je	.L49
.L14:
	movl	$7, %edx
	movl	$.LC0, %esi
	movl	$_ZSt4cerr, %edi
.LEHB0:
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movq	(%rbx), %rsi
	movl	$_ZSt4cerr, %edi
	call	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	movl	$13, %edx
	movq	%rax, %rbx
	movl	$.LC1, %esi
	movq	%rax, %rdi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movq	%rbx, %rdi
	call	_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	movl	$1, %eax
.L12:
	addq	$72, %rsp
	.cfi_remember_state
	.cfi_def_cfa_offset 56
	popq	%rbx
	.cfi_def_cfa_offset 48
	popq	%rbp
	.cfi_def_cfa_offset 40
	popq	%r12
	.cfi_def_cfa_offset 32
	popq	%r13
	.cfi_def_cfa_offset 24
	popq	%r14
	.cfi_def_cfa_offset 16
	popq	%r15
	.cfi_def_cfa_offset 8
	ret
.L49:
	.cfi_restore_state
	movq	8(%rsi), %rdi
	movl	$10, %edx
	xorl	%esi, %esi
	call	strtol
	testl	%eax, %eax
	movl	%eax, %ebp
	je	.L14
.L13:
	call	_ZNSt6thread20hardware_concurrencyEv
	movl	%eax, %ebx
	movl	$11, %edx
	movl	$.LC2, %esi
	movl	$_ZSt4cout, %edi
	movl	%ebx, %ebx
	movl	%eax, 4(%rsp)
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movq	%rbx, %rsi
	movl	$_ZSt4cout, %edi
	call	_ZNSo9_M_insertImEERSoT_
	movl	$.LC3, %esi
	movq	%rax, %rdi
	call	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	movl	$5, %edx
	movl	$.LC4, %esi
	movl	$_ZSt4cout, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	%ebp, %eax
	movl	$_ZSt4cout, %edi
	movq	%rax, %rsi
	movq	%rax, %r15
	movq	%rax, 24(%rsp)
	call	_ZNSo9_M_insertImEERSoT_
	movl	$7, %edx
	movl	$.LC5, %esi
	movq	%rax, %r12
	movq	%rax, %rdi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movq	%r12, %rdi
	leaq	0(,%r15,4), %r12
	call	_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	movq	%r12, %rdi
	call	_Znam
	movq	%r12, %rdi
	movq	%rax, %r14
	call	_Znam
	movq	%r12, %rdi
	movq	%rax, %r15
	call	_Znam
	movq	%r14, %rdx
	leal	-1(%rbp), %ecx
	movq	%rax, %r13
	shrq	$2, %rdx
	negq	%rdx
	movl	%ecx, %esi
	movl	%ecx, 32(%rsp)
	andl	$3, %edx
	movl	$4, %ecx
	leal	3(%rdx), %eax
	cmpl	$4, %eax
	cmovb	%ecx, %eax
	cmpl	%eax, %esi
	jb	.L36
	testl	%edx, %edx
	je	.L37
	cmpl	$1, %edx
	movl	$0, (%r14)
	movl	%ebp, (%r15)
	je	.L38
	cmpl	$2, %edx
	movl	$1, 4(%r14)
	movl	%esi, 4(%r15)
	je	.L39
	leal	-2(%rbp), %eax
	movl	$2, 8(%r14)
	movl	$3, 16(%rsp)
	movl	$3, 8(%rsp)
	movl	%eax, 8(%r15)
.L17:
	movd	8(%rsp), %xmm5
	movl	%ebp, 36(%rsp)
	movl	%ebp, %edi
	movd	16(%rsp), %xmm6
	subl	%edx, %edi
	salq	$2, %rdx
	pshufd	$0, %xmm5, %xmm0
	movd	36(%rsp), %xmm7
	pshufd	$0, %xmm6, %xmm1
	movl	%edi, %r8d
	movdqa	.LC6(%rip), %xmm2
	leaq	(%r14,%rdx), %rsi
	pshufd	$0, %xmm7, %xmm4
	shrl	$2, %r8d
	paddd	%xmm2, %xmm0
	paddd	%xmm2, %xmm1
	movdqa	.LC7(%rip), %xmm2
	addq	%r15, %rdx
	xorl	%eax, %eax
	xorl	%ecx, %ecx
	.p2align 4,,10
	.p2align 3
.L19:
	movdqa	%xmm4, %xmm3
	addl	$1, %ecx
	movaps	%xmm1, (%rsi,%rax)
	paddd	%xmm2, %xmm1
	psubd	%xmm0, %xmm3
	paddd	%xmm2, %xmm0
	movups	%xmm3, (%rdx,%rax)
	addq	$16, %rax
	cmpl	%ecx, %r8d
	ja	.L19
	movl	%edi, %ecx
	movl	8(%rsp), %edx
	movl	16(%rsp), %eax
	andl	$-4, %ecx
	addl	%ecx, %edx
	addl	%ecx, %eax
	cmpl	%ecx, %edi
	je	.L20
.L16:
	movl	%ebp, %esi
	movslq	%eax, %rcx
	subl	%edx, %esi
	leal	1(%rax), %edx
	movl	%eax, (%r14,%rcx,4)
	movl	%esi, (%r15,%rcx,4)
	cmpl	%ebp, %edx
	jnb	.L20
	movslq	%edx, %rcx
	movl	%ebp, %esi
	subl	%edx, %esi
	movl	%edx, (%r14,%rcx,4)
	leal	2(%rax), %edx
	movl	%esi, (%r15,%rcx,4)
	cmpl	%edx, %ebp
	jbe	.L20
	movslq	%edx, %rcx
	movl	%ebp, %esi
	subl	%edx, %esi
	movl	%edx, (%r14,%rcx,4)
	leal	3(%rax), %edx
	movl	%esi, (%r15,%rcx,4)
	cmpl	%edx, %ebp
	jbe	.L20
	movslq	%edx, %rcx
	movl	%ebp, %esi
	subl	%edx, %esi
	movl	%edx, (%r14,%rcx,4)
	leal	4(%rax), %edx
	movl	%esi, (%r15,%rcx,4)
	cmpl	%edx, %ebp
	jbe	.L20
	movl	%ebp, %esi
	addl	$5, %eax
	movslq	%edx, %rcx
	subl	%edx, %esi
	cmpl	%eax, %ebp
	movl	%edx, (%r14,%rcx,4)
	movl	%esi, (%r15,%rcx,4)
	jbe	.L20
	movl	%ebp, %ecx
	movslq	%eax, %rdx
	subl	%eax, %ecx
	movl	%eax, (%r14,%rdx,4)
	movl	%ecx, (%r15,%rdx,4)
.L20:
	movl	32(%rsp), %eax
	xorl	%esi, %esi
	movq	%r13, %rdi
	leaq	4(,%rax,4), %rdx
	call	memset
	leaq	0(,%rbx,8), %rdi
	call	_Znam
	movq	%rax, 8(%rsp)
	movl	4(%rsp), %eax
	movl	%eax, %ecx
	subl	$1, %ecx
	movl	%ecx, 36(%rsp)
	je	.L21
	subl	$2, %eax
	xorl	%ebx, %ebx
	movq	%rax, 40(%rsp)
	addq	$1, %rax
	movq	%rax, 16(%rsp)
	.p2align 4,,10
	.p2align 3
.L22:
	movl	$8, %edi
	call	_Znwm
.LEHE0:
	movl	$64, %edi
	movq	$0, (%rax)
	movq	%rax, %r12
.LEHB1:
	call	_Znwm
.LEHE1:
	movl	4(%rsp), %ecx
	leaq	56(%rsp), %rsi
	movq	$_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE+16, (%rax)
	movq	$sum, 8(%rax)
	movl	%ebp, 16(%rax)
	movl	$pthread_create, %edx
	movl	%ebx, 24(%rax)
	movq	%r13, 32(%rax)
	movq	%r12, %rdi
	movl	%ecx, 20(%rax)
	movq	%r15, 40(%rax)
	movq	%r14, 48(%rax)
	movq	$_Z9array_addPiS_S_iiiS_, 56(%rax)
	movq	%rax, 56(%rsp)
.LEHB2:
	call	_ZNSt6thread15_M_start_threadESt10unique_ptrINS_6_StateESt14default_deleteIS1_EEPFvvE
.LEHE2:
	movq	56(%rsp), %rdi
	testq	%rdi, %rdi
	je	.L23
	movq	(%rdi), %rax
	call	*8(%rax)
.L23:
	movq	8(%rsp), %rax
	movq	%r12, (%rax,%rbx,8)
	addq	$1, %rbx
	cmpq	16(%rsp), %rbx
	jne	.L22
	subq	$8, %rsp
	.cfi_def_cfa_offset 136
	movl	%ebp, %r9d
	movq	%r13, %rdx
	pushq	$sum
	.cfi_def_cfa_offset 144
	movl	20(%rsp), %r8d
	movq	%r15, %rsi
	movl	52(%rsp), %ecx
	movq	%r14, %rdi
.LEHB3:
	call	_Z9array_addPiS_S_iiiS_
	popq	%rcx
	.cfi_def_cfa_offset 136
	popq	%rsi
	.cfi_def_cfa_offset 128
	movl	$37, %edx
	movl	$.LC8, %esi
	movl	$_ZSt4cout, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	$_ZSt4cout, %edi
	call	_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	movq	8(%rsp), %rax
	movq	40(%rsp), %rcx
	leaq	8(%rax,%rcx,8), %rbx
	movq	%rax, %r12
	.p2align 4,,10
	.p2align 3
.L30:
	movq	(%r12), %rdi
	addq	$8, %r12
	call	_ZNSt6thread4joinEv
	cmpq	%rbx, %r12
	jne	.L30
.L29:
	movq	8(%rsp), %rdi
	xorl	%ebx, %ebx
	xorl	%r15d, %r15d
	call	_ZdaPv
	movl	$13, %edx
	movl	$.LC15, %esi
	movl	$_ZSt4cout, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	$_ZSt4cout, %edi
	call	_ZSt5flushIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	movl	32(%rsp), %r12d
	addq	$1, %r12
	jmp	.L33
	.p2align 4,,10
	.p2align 3
.L51:
	addq	$1, %rbx
	addl	$1, %r15d
	cmpq	%r12, %rbx
	je	.L50
.L33:
	cmpl	%ebp, 0(%r13,%rbx,4)
	je	.L51
	movl	$2, %edx
	movl	$.LC10, %esi
	movl	$_ZSt4cerr, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	%ebx, %esi
	movl	$_ZSt4cerr, %edi
	call	_ZNSolsEi
	movl	$.LC11, %esi
	movq	%rax, %rdi
	call	_ZStlsISt11char_traitsIcEERSt13basic_ostreamIcT_ES5_PKc
	movl	$10, %edx
	movl	$.LC12, %esi
	movl	$_ZSt4cerr, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movq	24(%rsp), %rsi
	movl	$_ZSt4cerr, %edi
	call	_ZNSo9_M_insertImEERSoT_
	movl	$5, %edx
	movl	$.LC13, %esi
	movl	$_ZSt4cerr, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	0(%r13,%rbx,4), %esi
	movl	$_ZSt4cerr, %edi
	addq	$1, %rbx
	call	_ZNSolsEi
	movl	$1, %edx
	movq	%rax, %r14
	movl	$.LC14, %esi
	movq	%rax, %rdi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movq	%r14, %rdi
	call	_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	cmpq	%r12, %rbx
	jne	.L33
.L50:
	cmpl	%ebp, %r15d
	je	.L34
	movl	$2, %eax
	jmp	.L12
.L35:
	movl	$100, %ebp
	jmp	.L13
.L38:
	movl	$1, 8(%rsp)
	movl	$1, 16(%rsp)
	jmp	.L17
.L34:
	movl	$9, %edx
	movl	$.LC9, %esi
	movl	$_ZSt4cout, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	sum(%rip), %esi
	movl	$_ZSt4cout, %edi
	call	_ZNSolsEi
	movq	%rax, %rdi
	call	_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	xorl	%eax, %eax
	jmp	.L12
.L37:
	movl	$0, 8(%rsp)
	movl	$0, 16(%rsp)
	jmp	.L17
.L39:
	movl	$2, 8(%rsp)
	movl	$2, 16(%rsp)
	jmp	.L17
.L21:
	subq	$8, %rsp
	.cfi_def_cfa_offset 136
	movl	%ebp, %r9d
	movl	$1, %r8d
	pushq	$sum
	.cfi_def_cfa_offset 144
	xorl	%ecx, %ecx
	movq	%r13, %rdx
	movq	%r15, %rsi
	movq	%r14, %rdi
	call	_Z9array_addPiS_S_iiiS_
	popq	%rax
	.cfi_def_cfa_offset 136
	popq	%rdx
	.cfi_def_cfa_offset 128
	movl	$.LC8, %esi
	movl	$37, %edx
	movl	$_ZSt4cout, %edi
	call	_ZSt16__ostream_insertIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_PKS3_l
	movl	$_ZSt4cout, %edi
	call	_ZSt4endlIcSt11char_traitsIcEERSt13basic_ostreamIT_T0_ES6_
	jmp	.L29
.L36:
	xorl	%eax, %eax
	xorl	%edx, %edx
	jmp	.L16
.L40:
	movq	%rax, %rbx
.L28:
	movq	%r12, %rdi
	call	_ZdlPv
	movq	%rbx, %rdi
	call	_Unwind_Resume
.LEHE3:
.L41:
	movq	56(%rsp), %rdi
	movq	%rax, %rbx
	testq	%rdi, %rdi
	je	.L28
	movq	(%rdi), %rax
	call	*8(%rax)
	jmp	.L28
	.cfi_endproc
.LFE2625:
	.globl	__gxx_personality_v0
	.section	.gcc_except_table,"a",@progbits
.LLSDA2625:
	.byte	0xff
	.byte	0xff
	.byte	0x1
	.uleb128 .LLSDACSE2625-.LLSDACSB2625
.LLSDACSB2625:
	.uleb128 .LEHB0-.LFB2625
	.uleb128 .LEHE0-.LEHB0
	.uleb128 0
	.uleb128 0
	.uleb128 .LEHB1-.LFB2625
	.uleb128 .LEHE1-.LEHB1
	.uleb128 .L40-.LFB2625
	.uleb128 0
	.uleb128 .LEHB2-.LFB2625
	.uleb128 .LEHE2-.LEHB2
	.uleb128 .L41-.LFB2625
	.uleb128 0
	.uleb128 .LEHB3-.LFB2625
	.uleb128 .LEHE3-.LEHB3
	.uleb128 0
	.uleb128 0
.LLSDACSE2625:
	.section	.text.startup
	.size	main, .-main
	.p2align 4,,15
	.type	_GLOBAL__sub_I_sum_mutex, @function
_GLOBAL__sub_I_sum_mutex:
.LFB3238:
	.cfi_startproc
	subq	$8, %rsp
	.cfi_def_cfa_offset 16
	movl	$_ZStL8__ioinit, %edi
	call	_ZNSt8ios_base4InitC1Ev
	movl	$__dso_handle, %edx
	movl	$_ZStL8__ioinit, %esi
	movl	$_ZNSt8ios_base4InitD1Ev, %edi
	addq	$8, %rsp
	.cfi_def_cfa_offset 8
	jmp	__cxa_atexit
	.cfi_endproc
.LFE3238:
	.size	_GLOBAL__sub_I_sum_mutex, .-_GLOBAL__sub_I_sum_mutex
	.section	.init_array,"aw"
	.align 8
	.quad	_GLOBAL__sub_I_sum_mutex
	.weak	_ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE
	.section	.rodata._ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE,"aG",@progbits,_ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE,comdat
	.align 32
	.type	_ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE, @object
	.size	_ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE, 87
_ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE:
	.string	"NSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE"
	.weak	_ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE
	.section	.rodata._ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE,"aG",@progbits,_ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE,comdat
	.align 8
	.type	_ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE, @object
	.size	_ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE, 24
_ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE:
	.quad	_ZTVN10__cxxabiv120__si_class_type_infoE+16
	.quad	_ZTSNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE
	.quad	_ZTINSt6thread6_StateE
	.weak	_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE
	.section	.rodata._ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE,"aG",@progbits,_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE,comdat
	.align 8
	.type	_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE, @object
	.size	_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE, 40
_ZTVNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE:
	.quad	0
	.quad	_ZTINSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEEE
	.quad	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED1Ev
	.quad	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEED0Ev
	.quad	_ZNSt6thread11_State_implINS_8_InvokerISt5tupleIJPFvPiS3_S3_iiiS3_ES3_S3_S3_ijjS3_EEEEE6_M_runEv
	.globl	sum
	.bss
	.align 4
	.type	sum, @object
	.size	sum, 4
sum:
	.zero	4
	.globl	sum_mutex
	.align 32
	.type	sum_mutex, @object
	.size	sum_mutex, 40
sum_mutex:
	.zero	40
	.local	_ZStL8__ioinit
	.comm	_ZStL8__ioinit,1,1
	.section	.rodata.cst16,"aM",@progbits,16
	.align 16
.LC6:
	.long	0
	.long	1
	.long	2
	.long	3
	.align 16
.LC7:
	.long	4
	.long	4
	.long	4
	.long	4
	.hidden	__dso_handle
	.ident	"GCC: (GNU) 7.3.1 20180303 (Red Hat 7.3.1-5)"
	.section	.note.GNU-stack,"",@progbits
