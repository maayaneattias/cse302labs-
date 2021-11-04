	.section .rodata
.lprintfmt:
	.string "%ld\n"
	.text
	.globl main
main:
	pushq %rbp
	movq %rsp, %rbp
	subq $112, %rsp
	movq $837799, -8(%rbp)
	.L0:
	jmp .L1
	.L1:
	movq -8(%rbp), %r11
	movq %r11, -16(%rbp)
	pushq %rdi
	pushq %rax
	movq -16(%rbp), %rdi
	callq bx_print_int
	popq %rax
	popq %rdi
	movq -8(%rbp), %r11
	movq %r11, -24(%rbp)
	movq $1, -32(%rbp)
	movq -24(%rbp), %r11
	subq -32(%rbp), %r11
	movq %r11, -24(%rbp)
	movq -24(%rbp), %r11
	cmpq $0, %r11
	jz .L3
	jmp .L4
	.L3:
	jmp .L2
	jmp .L5
	.L4:
	.L5:
	movq -8(%rbp), %r11
	movq %r11, -40(%rbp)
	movq $2, -48(%rbp)
	movq -40(%rbp), %rax
	cqto
	idivq -48(%rbp)
	movq %rdx, -56(%rbp)
	movq $0, -64(%rbp)
	movq -56(%rbp), %r11
	subq -64(%rbp), %r11
	movq %r11, -56(%rbp)
	movq -56(%rbp), %r11
	cmpq $0, %r11
	jz .L6
	jmp .L7
	.L6:
	movq -8(%rbp), %r11
	movq %r11, -72(%rbp)
	movq $2, -80(%rbp)
	movq -72(%rbp), %rax
	cqto
	idivq -80(%rbp)
	movq %rax, -8(%rbp)
	jmp .L8
	.L7:
	movq $3, -88(%rbp)
	movq -8(%rbp), %r11
	movq %r11, -96(%rbp)
	movq -88(%rbp), %rax
	imulq -96(%rbp)
	movq %rax, -104(%rbp)
	movq $1, -112(%rbp)
	movq -104(%rbp), %r11
	addq -112(%rbp), %r11
	movq %r11, -8(%rbp)
	.L8:
	jmp .L0
	.L2:
	movq %rbp, %rsp
	popq %rbp
	xorq %rax, %rax
	retq
