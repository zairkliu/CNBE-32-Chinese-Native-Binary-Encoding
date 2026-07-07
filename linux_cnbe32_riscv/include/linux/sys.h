/* Linux 0.01 CNBE-32 RISC-V 系统调用头文件
 * 基于原始 Linux 0.01 sys.h，更新为 ANSI C 函数原型
 */

#include <sys/types.h>

/* 前向声明结构体 (避免 include 循环) */
struct stat;
struct tms;
struct utimbuf;
struct utsname;
struct sigaction;

extern int sys_setup(void);
extern int sys_exit(int error_code);
extern int sys_fork(void);
extern int sys_read(unsigned int fd, char * buf, int count);
extern int sys_write(unsigned int fd, char * buf, int count);
extern int sys_open(const char * filename, int flag, int mode);
extern int sys_close(unsigned int fd);
extern int sys_waitpid(pid_t pid, int * stat_addr, int options);
extern int sys_creat(const char * pathname, int mode);
extern int sys_link(const char * oldname, const char * newname);
extern int sys_unlink(const char * name);
extern int sys_execve(const char * filename, char ** argv, char ** envp);
extern int sys_chdir(const char * filename);
extern int sys_time(long * tloc);
extern int sys_mknod(void);
extern int sys_chmod(const char * filename, int mode);
extern int sys_chown(const char * filename, int uid, int gid);
extern int sys_break(void);
extern int sys_stat(char * filename, struct stat * statbuf);
extern int sys_lseek(unsigned int fd, off_t offset, int origin);
extern int sys_getpid(void);
extern int sys_mount(void);
extern int sys_umount(void);
extern int sys_setuid(int uid);
extern int sys_getuid(void);
extern int sys_stime(long * tptr);
extern int sys_ptrace(void);
extern int sys_alarm(long seconds);
extern int sys_fstat(unsigned int fd, struct stat * statbuf);
extern int sys_pause(void);
extern int sys_utime(char * filename, struct utimbuf * times);
extern int sys_stty(void);
extern int sys_gtty(void);
extern int sys_access(const char * filename, int mode);
extern int sys_nice(long increment);
extern int sys_ftime(void);
extern int sys_sync(void);
extern int sys_kill(int pid, int sig);
extern int sys_rename(void);
extern int sys_mkdir(const char * pathname, int mode);
extern int sys_rmdir(const char * name);
extern int sys_dup(unsigned int fildes);
extern int sys_pipe(unsigned long * fildes);
extern int sys_times(struct tms * tbuf);
extern int sys_prof(void);
extern int sys_brk(unsigned long end_data_seg);
extern int sys_setgid(int gid);
extern int sys_getgid(void);
extern int sys_signal(long signal, long addr, long restorer);
extern int sys_geteuid(void);
extern int sys_getegid(void);
extern int sys_acct(void);
extern int sys_phys(void);
extern int sys_lock(void);
extern int sys_ioctl(unsigned int fd, unsigned int cmd, unsigned long arg);
extern int sys_fcntl(unsigned int fd, unsigned int cmd, unsigned long arg);
extern int sys_mpx(void);
extern int sys_setpgid(int pid, int pgid);
extern int sys_ulimit(void);
extern int sys_uname(struct utsname * name);
extern int sys_umask(int mask);
extern int sys_chroot(const char * filename);
extern int sys_ustat(int dev, struct ustat * ubuf);
extern int sys_dup2(unsigned int oldfd, unsigned int newfd);
extern int sys_getppid(void);
extern int sys_getpgrp(void);
extern int sys_setsid(void);
extern int sys_sigaction(int sig, const struct sigaction *act, struct sigaction *oact);
extern int sys_sgetmask(void);
extern int sys_ssetmask(int newmask);
extern int sys_setreuid(int ruid, int euid);
extern int sys_setregid(int rgid, int egid);

/* 系统调用表 — 使用 void* 避免类型不匹配 */
typedef void *syscall_fn_t;

syscall_fn_t sys_call_table[] = { (syscall_fn_t)sys_setup, (syscall_fn_t)sys_exit, (syscall_fn_t)sys_fork, (syscall_fn_t)sys_read,
    (syscall_fn_t)sys_write, (syscall_fn_t)sys_open, (syscall_fn_t)sys_close, (syscall_fn_t)sys_waitpid, (syscall_fn_t)sys_creat, (syscall_fn_t)sys_link,
    (syscall_fn_t)sys_unlink, (syscall_fn_t)sys_execve, (syscall_fn_t)sys_chdir, (syscall_fn_t)sys_time, (syscall_fn_t)sys_mknod, (syscall_fn_t)sys_chmod,
    (syscall_fn_t)sys_chown, (syscall_fn_t)sys_break, (syscall_fn_t)sys_stat, (syscall_fn_t)sys_lseek, (syscall_fn_t)sys_getpid, (syscall_fn_t)sys_mount,
    (syscall_fn_t)sys_umount, (syscall_fn_t)sys_setuid, (syscall_fn_t)sys_getuid, (syscall_fn_t)sys_stime, (syscall_fn_t)sys_ptrace, (syscall_fn_t)sys_alarm,
    (syscall_fn_t)sys_fstat, (syscall_fn_t)sys_pause, (syscall_fn_t)sys_utime, (syscall_fn_t)sys_stty, (syscall_fn_t)sys_gtty, (syscall_fn_t)sys_access,
    (syscall_fn_t)sys_nice, (syscall_fn_t)sys_ftime, (syscall_fn_t)sys_sync, (syscall_fn_t)sys_kill, (syscall_fn_t)sys_rename, (syscall_fn_t)sys_mkdir,
    (syscall_fn_t)sys_rmdir, (syscall_fn_t)sys_dup, (syscall_fn_t)sys_pipe, (syscall_fn_t)sys_times, (syscall_fn_t)sys_prof, (syscall_fn_t)sys_brk, (syscall_fn_t)sys_setgid,
    (syscall_fn_t)sys_getgid, (syscall_fn_t)sys_signal, (syscall_fn_t)sys_geteuid, (syscall_fn_t)sys_getegid, (syscall_fn_t)sys_acct, (syscall_fn_t)sys_phys,
    (syscall_fn_t)sys_lock, (syscall_fn_t)sys_ioctl, (syscall_fn_t)sys_fcntl, (syscall_fn_t)sys_mpx, (syscall_fn_t)sys_setpgid, (syscall_fn_t)sys_ulimit,
    (syscall_fn_t)sys_uname, (syscall_fn_t)sys_umask, (syscall_fn_t)sys_chroot, (syscall_fn_t)sys_ustat, (syscall_fn_t)sys_dup2, (syscall_fn_t)sys_getppid,
    (syscall_fn_t)sys_getpgrp, (syscall_fn_t)sys_setsid, (syscall_fn_t)sys_sigaction, (syscall_fn_t)sys_sgetmask, (syscall_fn_t)sys_ssetmask,
    (syscall_fn_t)sys_setreuid, (syscall_fn_t)sys_setregid
};

#define NR_syscalls 72
